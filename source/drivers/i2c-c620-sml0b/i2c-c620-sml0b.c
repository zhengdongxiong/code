/* platform device */

#include <linux/debugfs.h>
#include <linux/ioport.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/platform_device.h>

#define PADBAR 0x00c
#define P2SB_PORTID_SHIFT 16
#define P2SB_PORT_GPIO1 0xAE

#define PADGRP_OFFSET_SML0BCLK  ( 24 /* GPP_C */ + 13 /* GPP_D */)
#define PADGRP_OFFSET_SML0BDATA ( 24 /* GPP_C */ + 14 /* GPP_D */)

#define sbreg_addr      0xfd000000 /*Address Base*/

/*Community 1*/
#define C620_GPIO_COMMUNITY1_OFFSET (sbreg_addr + (P2SB_PORT_GPIO1 << P2SB_PORTID_SHIFT))
#define C620_GPIO_COMMUNITY1_SIZE   0x00010000

static struct resource c620_gpio_community2_dev_res[] = {
    DEFINE_RES_MEM_NAMED(C620_GPIO_COMMUNITY1_OFFSET, C620_GPIO_COMMUNITY1_SIZE, NULL),
};

static void c620_sml0b_i2c_device_release(struct device *dev)
{

}

static struct platform_device c620_sml0b_i2c_device = {
    .name       = "c620-sml0b-i2c",
    .id         = -1,
    .resource   = c620_gpio_community2_dev_res,
    .num_resources  = ARRAY_SIZE(c620_gpio_community2_dev_res),
    .dev = {
        .release    =  c620_sml0b_i2c_device_release,
    }
};

/* platform driver */
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/delay.h>
#include <linux/platform_device.h>
#include <linux/slab.h>
#include <linux/io.h>

#include <linux/i2c.h>
//#include <linux/i2c-algo-bit.h>
#include "i2c-algo-bit-im.h"

struct c620_sml0b_i2c_data {
    struct resource             *res;
    void __iomem                *regs;
    u32                         padbar;
    struct i2c_adapter          adap;
    struct i2c_algo_bit_data    bit;
};

#define REG_PCH_GPIO_DW0_PMODE    0x0C00
#define REG_PCH_GPIO_DW0_RXDIS    0x0200
#define REG_PCH_GPIO_DW0_TXDIS    0x0100
#define REG_PCH_GPIO_DW0_RXSTATE  0x0002
#define REG_PCH_GPIO_DW0_TXSTATE  0x0001

#define setscl(adap, val)	adap.setscl(adap.data, val)
#define getsda(adap)		adap.getsda(adap.data)


static int c620_sml0b_init_gpio(struct c620_sml0b_i2c_data *pd)
{
    void __iomem *regs = pd->regs;
    void __iomem *padcfg;
    u32 padbar;
    u32 dw0;

    padbar = readl(regs + PADBAR);
    pd->padbar = padbar;

    // SML0BCLK
    padcfg = regs + padbar + PADGRP_OFFSET_SML0BCLK * 8;
    dw0 = readl(padcfg);
    if ((dw0 & REG_PCH_GPIO_DW0_PMODE) != 0) {
        // Not GPIO mode, set it
        dw0 &= ~REG_PCH_GPIO_DW0_PMODE;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_RXDIS) == 0) {
        // RX enabled, disable it
        dw0 |= REG_PCH_GPIO_DW0_RXDIS;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_TXDIS) == 0) {
        // Tx enabled, disable it
        dw0 |= REG_PCH_GPIO_DW0_TXDIS;
    }
    writel(dw0, padcfg);

    // SML0BDATA
    padcfg = regs + padbar + PADGRP_OFFSET_SML0BDATA * 8;
    dw0 = readl(padcfg);
    if ((dw0 & REG_PCH_GPIO_DW0_PMODE) != 0) {
        // Not GPIO mode, set it
        dw0 &= ~REG_PCH_GPIO_DW0_PMODE;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_RXDIS) == 0) {
        // RX enabled, disable it
        dw0 |= REG_PCH_GPIO_DW0_RXDIS;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_TXDIS) == 0) {
        // Tx enabled, disable it
        dw0 |= REG_PCH_GPIO_DW0_TXDIS;
    }
    writel(dw0, padcfg);

    return 0;
}

/* i2c bit-bus functions */
static void c620_sml0b_i2c_setsda(void *pw, int state)
{
    struct c620_sml0b_i2c_data *pd = pw;
    void __iomem *padcfg;
    u32 dw0;

    // SML0BDATA
    padcfg = pd->regs + pd->padbar + PADGRP_OFFSET_SML0BDATA * 8;
    dw0 = readl(padcfg);
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
    // set Tx
    if (state != 0) {
        dw0 |= REG_PCH_GPIO_DW0_TXSTATE;
    } else {
        dw0 &= ~REG_PCH_GPIO_DW0_TXSTATE;
    }
    writel(dw0, padcfg);
}

static void c620_sml0b_i2c_setscl(void *pw, int state)
{
    struct c620_sml0b_i2c_data *pd = pw;
    void __iomem *padcfg;
    u32 dw0;

    // SML0BCLK
    padcfg = pd->regs + pd->padbar + PADGRP_OFFSET_SML0BCLK * 8;
    dw0 = readl(padcfg);
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
    // set Tx
    if (state != 0) {
        dw0 |= REG_PCH_GPIO_DW0_TXSTATE;
    } else {
        dw0 &= ~REG_PCH_GPIO_DW0_TXSTATE;
    }
    writel(dw0, padcfg);
}

static int c620_sml0b_i2c_getsda(void *pw)
{
    struct c620_sml0b_i2c_data *pd = pw;
    void __iomem *padcfg;
    u32 dw0;
    u32 dw0_old;

    // SML0BDATA
    padcfg = pd->regs + pd->padbar + PADGRP_OFFSET_SML0BDATA * 8;
    dw0_old = dw0 = readl(padcfg);
    if ((dw0 & REG_PCH_GPIO_DW0_PMODE) != 0) {
        // Not GPIO mode, set it
        dw0 &= ~REG_PCH_GPIO_DW0_PMODE;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_RXDIS) != 0) {
        // RX disabled, enable it
        dw0 &= ~REG_PCH_GPIO_DW0_RXDIS;
    }
    if ((dw0 & REG_PCH_GPIO_DW0_TXDIS) == 0) {
        // Tx enabled, disable it
        dw0 |= REG_PCH_GPIO_DW0_TXDIS;
    }
    if (dw0_old != dw0) {
        writel(dw0, padcfg);
        udelay((pd->bit.udelay + 1) / 2);
        //udelay(pd->bit.udelay);
        readl(padcfg);
        //printk("Turn Around\n");
    }
    // get Tx
    dw0 = readl(padcfg);
    return ((dw0 & REG_PCH_GPIO_DW0_RXSTATE) ? 1 : 0);
}

static int c620_sml0b_i2c_probe(struct platform_device *dev)
{
    struct c620_sml0b_i2c_data *pd;
    struct resource *res;
    int size;
    int ret;
    int i;

    pd = kzalloc(sizeof(struct c620_sml0b_i2c_data), GFP_KERNEL);
    if (pd == NULL)
        return -ENOMEM;

    platform_set_drvdata(dev, pd);

    res = platform_get_resource(dev, IORESOURCE_MEM, 0);
    if (res == NULL) {
        dev_err(&dev->dev, "cannot find IO resource\n");
        ret = -ENOENT;
        goto err;
    }

    size = resource_size(res);

    pd->res = request_mem_region(res->start, size, dev->name);
    if (pd->res == NULL) {
        dev_err(&dev->dev, "cannot request mem region 0x%llx\n", res->start);
        ret = -ENXIO;
        goto err;
    }

	pd->regs = ioremap(res->start, size);
	if (pd->regs == NULL) {
		dev_err(&dev->dev, "cannot map IO\n");
		ret = -ENXIO;
		goto err_res;
	}

    // init for GPIO mode
    ret = c620_sml0b_init_gpio(pd);

    /* setup the private data */
    pd->adap.owner = THIS_MODULE;
    pd->adap.algo_data = &pd->bit;
    pd->adap.dev.parent = &dev->dev;

    strlcpy(pd->adap.name, "C620 SML0B I2C", sizeof(pd->adap.name));

    pd->bit.data   = pd;
    pd->bit.setsda = c620_sml0b_i2c_setsda;
    pd->bit.setscl = c620_sml0b_i2c_setscl;
    pd->bit.getsda = c620_sml0b_i2c_getsda;
    //pd->bit.getscl = ;
    pd->bit.timeout = HZ;
    pd->bit.udelay  = 20;

        
    if (!getsda(pd->bit)) {
        for (i = 0; i <= 9 ; i++) {
            setscl(pd->bit, 1);
            udelay((pd->bit.udelay) / 2);
            setscl(pd->bit, 0);
            udelay((pd->bit.udelay) / 2);
        }
        setscl(pd->bit, 1);
        udelay((pd->bit.udelay) / 2);
    }
    
    
    ret = i2c_bit_im_add_bus(&pd->adap);
    if (ret)
        goto err_all;

    return 0;

err_all:
	iounmap(pd->regs);

err_res:
    release_mem_region(pd->res->start, size);

err:
    kfree(pd);
    return ret;
}

static int c620_sml0b_i2c_remove(struct platform_device *dev)
{
    struct c620_sml0b_i2c_data *pd = platform_get_drvdata(dev);

    i2c_del_adapter(&pd->adap);

    iounmap(pd->regs);
    release_mem_region(pd->res->start, resource_size(pd->res));
    kfree(pd);

    return 0;
}

static struct platform_driver c620_sml0b_i2c_driver = {
    .driver = {
        .name = "c620-sml0b-i2c",
    },
    .probe = c620_sml0b_i2c_probe,
    .remove = c620_sml0b_i2c_remove,
};

static int c620_sml0b_i2c_init(void)
{
    int ret; 
    ret = platform_device_register(&c620_sml0b_i2c_device);

    if (ret < 0) {
        return ret;
    }

    return platform_driver_register(&c620_sml0b_i2c_driver);
}
module_init(c620_sml0b_i2c_init);

static void __exit c620_sml0b_i2c_exit(void)
{
    platform_driver_unregister(&c620_sml0b_i2c_driver);
    platform_device_unregister(&c620_sml0b_i2c_device);
}

module_exit(c620_sml0b_i2c_exit);

MODULE_DESCRIPTION("C620 SML0B I2C Bus driver");
MODULE_AUTHOR("Hu.liupeng <hu.liupeng@embedway.com>");
MODULE_LICENSE("GPL");
MODULE_ALIAS("platform:c620-sml0b-i2c");
MODULE_VERSION("0.8.0");
