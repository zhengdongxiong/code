#include <libgen.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <pci/pci.h>
#include <sys/io.h>
#include <sys/mman.h>
#include <sys/errno.h>

/*
 * Generic PCI configuration space registers.
 */
#define REG_VENDOR          0x00
#define REG_DEVICE          0x04

/*
 * D31:F0 configuration space registers.
 */
#define REG_ICH0_GPIOBASE   0x58
#define REG_ICH0_GC         0x5c

#define REG_ICH6_GPIOBASE   0x48
#define REG_ICH6_GC         0x4c

#define REG_ICHx_GC_EN      0x10
#define REG_ICHx_GC_GLE     0x01

/*
 * D31:F1 configuration space registers.
 */
#define REG_P2SB_BAR        0x10
#define REG_P2SB_BARH       0x14
#define REG_P2SB_CTRL       0xe0

#define REG_P2SB_CTRL_HIDE  0x0100

/*
 * P2SB private registers.
 */
#define P2SB_PORTID_SHIFT   16
#define P2SB_PORT_GPIO4     0xAB
#define P2SB_PORT_GPIO3     0xAC
#define P2SB_PORT_GPIO2     0xAD
#define P2SB_PORT_GPIO1     0xAE
#define P2SB_PORT_GPIO0     0xAF

/*
 * GPIO sideband registers.
 */
#define REG_PCH_GPIO_FAMBAR 0x8
#define REG_PCH_GPIO_PADBAR 0xC

#define REG_PCH_GPIO_DW0_PMODE    0x0C00
#define REG_PCH_GPIO_DW0_RXDIS    0x0200
#define REG_PCH_GPIO_DW0_TXDIS    0x0100
#define REG_PCH_GPIO_DW0_RXSTATE  0x0002
#define REG_PCH_GPIO_DW0_TXSTATE  0x0001

static struct pad_t {
    uint16_t port_id;
    unsigned int number;
    const char* name;
} g_smbus_pads[] = {
    {P2SB_PORT_GPIO1, 37, "D_13"},  //24 - 0   37 - 13
    {P2SB_PORT_GPIO1, 38, "D_14"},
    {P2SB_PORT_GPIO1, 28, "D_4" },  // LED 3     GPIO1 --> Community 1 C(24)   
    {P2SB_PORT_GPIO1, 46, "D_22"},  // LED 4
    {P2SB_PORT_GPIO1, 45, "D_21"},  // LED 5
    {P2SB_PORT_GPIO1, 39, "D_15"},  // LED 6
    {P2SB_PORT_GPIO0, 62, "F_14"},  // LED 7
};

struct pci_dev *pci_find_dev(struct pci_access *pci, uint8_t bus, uint8_t dev, uint8_t func)
{
    struct pci_dev *it;
    for (it = pci->devices; it; it = it->next) {
        if (it->bus == bus && it->dev == dev && it->func == func) {
            return it;
        }
    }

    return NULL;
}

int get_pch_sbreg_addr(struct pci_access *pci, pciaddr_t *sbreg_addr)
{
    struct pci_dev *d31f1 = pci_get_dev(pci, 0, 0, 31, 1);
    pci_fill_info(d31f1, PCI_FILL_IDENT);
    if (d31f1->vendor_id == 0xffff) {
        printf("Cannot find D31:F1, assuming it is hidden by firmware\n");

        uint32_t p2sb_ctrl = pci_read_long(d31f1, REG_P2SB_CTRL);
        printf("P2SB_CTRL=%02x\n", p2sb_ctrl);
        if (!(p2sb_ctrl & REG_P2SB_CTRL_HIDE)) {
            fprintf(stderr, "D31:F1 is hidden but P2SB_E1 is not 0xff, bailing out\n");
            return -1;
        }

        printf("Unhiding P2SB\n");
        pci_write_long(d31f1, REG_P2SB_CTRL, p2sb_ctrl & ~REG_P2SB_CTRL_HIDE);

        p2sb_ctrl = pci_read_long(d31f1, REG_P2SB_CTRL);
        printf("P2SB_CTRL=%02x\n", p2sb_ctrl);
        if (p2sb_ctrl & REG_P2SB_CTRL_HIDE) {
            fprintf(stderr, "Cannot unhide PS2B\n");
            return -1;
        }

        pci_fill_info(d31f1, PCI_FILL_RESCAN | PCI_FILL_IDENT);
        if (d31f1->vendor_id == 0xffff) {
            fprintf(stderr, "P2SB unhidden but does not enumerate, bailing out\n");
            return -1;
        }
    }

    pci_fill_info(d31f1, PCI_FILL_RESCAN | PCI_FILL_IDENT | PCI_FILL_BASES);
    if (d31f1->vendor_id != 0x8086) {
        fprintf(stderr, "Vendor of D31:F1 is not Intel\n");
        return -1;
    } else if ((uint32_t)d31f1->base_addr[0] == 0xffffffff) {
        fprintf(stderr, "SBREG_BAR is not implemented in D31:F1\n");
        return -1;
    }

    *sbreg_addr = d31f1->base_addr[0] &~ 0xf;
    printf("SBREG_ADDR=%08lx\n", *sbreg_addr);

#if 1
    //printf("Hiding P2SB again\n");
    uint32_t p2sb_ctrl = pci_read_long(d31f1, REG_P2SB_CTRL);
    pci_write_long(d31f1, REG_P2SB_CTRL, p2sb_ctrl | REG_P2SB_CTRL_HIDE);
    pci_fill_info(d31f1, PCI_FILL_RESCAN | PCI_FILL_IDENT);
    if (d31f1->vendor_id != 0xffff) {
        fprintf(stderr, "Cannot hide P2SB\n");
        //return -1;
    }
#endif
    return 0;
}
//fd000000+0xae<<16+0xc 
uint32_t sideband_read(void *sbmap, uint8_t port, uint16_t reg)
{
    return *(volatile uint32_t*)((uintptr_t)sbmap + (port << P2SB_PORTID_SHIFT) + reg);
}

void sideband_write(void *sbmap, uint8_t port, uint16_t reg, uint32_t data)
{
    *(volatile uint32_t*)((uintptr_t)sbmap + (port << P2SB_PORTID_SHIFT) + reg)
        = data;
}

int try_pch(struct pci_access *pci, unsigned int idx, unsigned int level) {
    pciaddr_t sbreg_addr;
    if (get_pch_sbreg_addr(pci, &sbreg_addr)) {
        printf("Re-enumerating PCI devices will probably crash the system\n");
        fprintf(stderr, "Probing Intel PCH failed\n");
        return -1;
    }
    int memfd = open("/dev/mem", O_RDWR);
    if (memfd == -1) {
        fprintf(stderr, "Cannot open /dev/mem\n");
        return -1;
    }

    void *sbmap = mmap((void*)sbreg_addr, 1 << 24, PROT_READ|PROT_WRITE, MAP_SHARED, memfd, sbreg_addr);
    if (sbmap == MAP_FAILED) {
        if (errno == EPERM) {
            // The requirement might be relaxed to CONFIG_IO_DEVMEM_STRICT=n, but I'm not sure.
            printf("Is your kernel configured with CONFIG_DEVMEM_STRICT=n?\n");
        }
        fprintf(stderr, "Cannot map SBREG\n");
        return -1;
    }

    close(memfd);

#if 0
    int i = 0;
    for (i = 0; i < sizeof(g_smbus_pads)/sizeof(g_smbus_pads[0]); i++) {
	    uint16_t port_id = g_smbus_pads[i].port_id;
	    uint32_t padbar = sideband_read(sbmap, port_id, REG_PCH_GPIO_PADBAR);
	    printf("%s PADBAR=0x%x\n", g_smbus_pads[i].name, padbar);
	    uint32_t dw0 = sideband_read(sbmap, port_id, padbar + g_smbus_pads[i].number * 8);
            printf("dw0 = 0x%x\n", dw0);
	    if ((dw0 & REG_PCH_GPIO_DW0_PMODE) != MODE1) {
		    printf("set to mode1\n");
		dw0 &= ~REG_PCH_GPIO_DW0_PMODE;
		dw0 |= MODE1;
	    }
	    if ((dw0 & REG_PCH_GPIO_DW0_RXDIS) == 0) {
		// RX enabled, disable it
		dw0 |= REG_PCH_GPIO_DW0_RXDIS;
	    }
	    if ((dw0 & REG_PCH_GPIO_DW0_TXDIS) != 0) {
		// Tx disabled, enable it
		dw0 &= ~REG_PCH_GPIO_DW0_TXDIS;
	    }
	    // set level to Tx
	    if (level != 0) {
		dw0 |= REG_PCH_GPIO_DW0_TXSTATE;
	    } else {
		dw0 &= ~REG_PCH_GPIO_DW0_TXSTATE;
	    }
	    // write dw0
		    printf("write dw0 = 0x%x\n", dw0);
	    sideband_write(sbmap, port_id, padbar + g_smbus_pads[i].number * 8, dw0);
	    dw0 = sideband_read(sbmap, port_id, padbar + g_smbus_pads[i].number * 8);
		    printf("readback dw0 = 0x%x\n", dw0);
    }
#endif

    printf("sbmap=%x\n", sbmap);//fd000000
    uint16_t port_id = g_smbus_pads[idx].port_id;
    //fdae0000 + C
    uint32_t padbar = sideband_read(sbmap, port_id, REG_PCH_GPIO_PADBAR);
    printf("GPIO%d_PADBAR=%x\n", 1, padbar);//0x400
    //fd000000 + 0xae0000 + 0x400+37*8
    uint32_t dw0 = sideband_read(sbmap, port_id, padbar + g_smbus_pads[idx].number * 8);
    printf("dw0=%x\n", dw0);//44000201
    if ((dw0 & REG_PCH_GPIO_DW0_PMODE) != 0) {
        // Not GPIO mode, set it
        dw0 &= ~REG_PCH_GPIO_DW0_PMODE;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_RXDIS) == 0) {
        // RX enabled, disable it
        dw0 |= REG_PCH_GPIO_DW0_RXDIS;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_TXDIS) != 0) {
        // Tx disabled, enable it
        dw0 &= ~REG_PCH_GPIO_DW0_TXDIS;
    }
    // set level to Tx
    if (level != 0) {
        dw0 |= REG_PCH_GPIO_DW0_TXSTATE;
    } else {
        dw0 &= ~REG_PCH_GPIO_DW0_TXSTATE;
    }
    // write dw0
    printf("dw0=%x\n", dw0);
    sideband_write(sbmap, port_id, padbar + g_smbus_pads[idx].number * 8, dw0);

    return 0;
}

int create_pci(int method, struct pci_access **pci_out)
{
    struct pci_access *pci = pci_alloc();
    pci->method = method;
    pci_init(pci);
    pci_scan_bus(pci);

    struct pci_dev *d31f0 = pci_find_dev(pci, 0, 31, 0);
    if (!d31f0) {
        fprintf(stderr, "Cannot find D31:F0\n");
        return -1;
    }

    pci_fill_info(d31f0, PCI_FILL_IDENT | PCI_FILL_BASES);
    if (d31f0->vendor_id != 0x8086) {
        fprintf(stderr, "Vendor of D31:F0 is not Intel\n");
        return -1;
    }

    *pci_out = pci;

    return 0;
}

void usage(char* filename)
{
    printf("usage: %s <GPP_D>(0(13)~1(14)) <state>(0/1)\n", filename);
}

int main(int argc, char* argv[])
{
    if (argc < 3) {
        usage(basename(argv[0]));
        return 0;
    }
 
    unsigned int idx = strtol(argv[1], NULL, 0);
    if (!((idx >= 0) && (idx <= 1))) {
        usage(basename(argv[0]));
        return 0;
    }
    unsigned int level = strtol(argv[2], NULL, 0);

    // Letting Linux discover P2SB (and reassign its BAR) hangs the system,
    // so we need to enumerate the device bypassing it.
    struct pci_access *pci;
    if (create_pci(PCI_ACCESS_I386_TYPE1, &pci)) {
        return 1;
    }

    if (try_pch(pci, idx, level)) {
        return 1;
    }

    printf("[+] Done\n");
    return 0;
}

