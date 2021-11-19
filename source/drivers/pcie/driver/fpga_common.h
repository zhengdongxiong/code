#ifndef __FPGA_COMMON_H__
#define __FPGA_COMMON_H__

#include <linux/ioctl.h>


/* ioctl types */
#define FPGA_CMD_READ		1
#define FPGA_CMD_WRITE		2


/* ioctl CMDs */
#define FPGA_IOCX_BASE			0x66
#define FPGA_IOCX_READ			_IOR(FPGA_IOCX_BASE, FPGA_CMD_READ, int)
#define FPGA_IOCX_WRITE			_IOW(FPGA_IOCX_BASE, FPGA_CMD_WRITE, int)


/* IOC CMD-to-STR array */
#define FPGA_IOC2STR { \
    [FPGA_CMD_READ] = "FPGA_CMD_LOAD_IMGLIB", \
    [FPGA_CMD_WRITE] = "FPGA_CMD_RESET_FR", \
}

#define IMGMATCH_QUERY_ID_ANY 0xFFFFFFFF


struct fpga_rw {
	uint8_t bar;
	uint32_t offset;
	uint16_t value;
};

#endif 
