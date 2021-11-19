#include <linux/time.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/device.h>
#include <linux/pci.h>
#include <linux/miscdevice.h>

#include "fpga_common.h"

#define FPGA_DRIVER_NAME    "Fpga Recognition"

#define FPGA_VENDOR_ID 0x1172
#define FPGA_DEVICE_ID 0x0000


/* Altera FPGA BAR defs */
#define FPGA_FPGA_BAR_NUM	6
#define FPGA_BAR_ID_DMACTL	0
#define FPGA_BAR_ID_IMGCTL	4


static unsigned int fpga_misc = 88;
module_param(fpga_misc, uint, (S_IRUSR | S_IRGRP));
MODULE_PARM_DESC(fpga_misc, "misc minor (default 88)");

#define to_fpga_dev(fp) container_of(fp->private_data, struct fpga, miscdev)

struct fpga {
	struct pci_dev *pci_dev;

	/* misc device */
	struct miscdevice	miscdev;

	/* pci device info */
	u8 revision;
	u8 irq_pin;
	u8 irq_line;

	/* pci bar */
	resource_size_t bar_start[FPGA_FPGA_BAR_NUM];
	size_t bar_length[FPGA_FPGA_BAR_NUM];
	void __iomem *bar[FPGA_FPGA_BAR_NUM];
	uint8_t bar_num;

	struct mutex lock;
};

static int fpga_ioctl_read(struct fpga *fr, unsigned long arg)
{
	struct fpga_rw fpga_read;
	uint8_t bar;
	uint32_t offset;
	uint16_t value;	
	size_t len;
	int ret = 0;
	uint8_t bar_num = fr->bar_num;
	void __iomem *fpga_addr = NULL;

	
	copy_from_user(&fpga_read, (struct fpga_rw *)arg, sizeof(struct fpga_rw));

	bar = fpga_read.bar;
	len = fr->bar_length[bar];
	offset = fpga_read.offset;
	if (bar >= bar_num || offset >= len) {
		ret = -EINVAL;
		goto read_exit;
	}
	
	fpga_addr = fr->bar[bar];
	value = ioread16(fpga_addr + offset);
	fpga_read.value = value;

	dev_dbg(&fr->pci_dev->dev, "Read offset=0x%x, value=0x%x", offset, value);
	
	copy_to_user((struct fpga_rw *)arg, &fpga_read, sizeof(struct fpga_rw));
	
read_exit:
	
	return ret;
}


static int fpga_ioctl_write(struct fpga *fr, unsigned long arg)
{
	struct fpga_rw fpga_write;
	uint8_t bar;
	uint32_t offset;
	uint16_t value;		
	size_t len;
	int ret = 0;
	uint8_t bar_num = fr->bar_num;
	void __iomem *fpga_addr = NULL;

	
	copy_from_user(&fpga_write, (struct fpga_rw *)arg, sizeof(struct fpga_rw));

	bar = fpga_write.bar;
	len = fr->bar_length[bar];
	offset = fpga_write.offset;
	if (bar >= bar_num || offset >= len) {
		ret = -EINVAL;
		goto write_exit;
	}
	
	fpga_addr = fr->bar[bar];
	value = fpga_write.value;
		
	iowrite16(value, fpga_addr + offset);

	dev_dbg(&fr->pci_dev->dev, "Write offset=0x%x, value=0x%x", offset, value);

write_exit:
	
	return ret;
}

static long fpga_ioctl(struct file *file,
			    unsigned int cmd, unsigned long arg)
{
	struct fpga *fr = to_fpga_dev(file);

	switch (cmd) {
		case FPGA_IOCX_READ:
			return fpga_ioctl_read(fr, arg);
		case FPGA_IOCX_WRITE:
			return fpga_ioctl_write(fr, arg);
		default:
			return -EINVAL;
	}
}

static int fpga_open(struct inode *inode, struct file *file)
{
	return 0;
}

static int fpga_release(struct inode *inode, struct file *file)
{
	return 0;
}

static const struct file_operations fpga_misc_fops = {
	.owner	= THIS_MODULE,
	.read	= NULL,
	.write	= NULL,
	.open	= fpga_open,
	.release	= fpga_release,
	.unlocked_ioctl	= fpga_ioctl,
};

static void unmap_bars(struct pci_dev *dev)
{	
	struct fpga *fr = pci_get_drvdata(dev);	
	uint8_t bar_num = fr->bar_num;
	int i;
	
	for (i = 0; i < bar_num; i++) {
		pci_iounmap(dev, fr->bar[i]);
		fr->bar[i] = NULL;
	}
}

static int map_bars(struct pci_dev *dev)
{
	struct fpga *fr = pci_get_drvdata(dev);
	uint8_t bar_num = fr->bar_num;
	int i;

	for (i = 0; i < bar_num; i++) {
	
		fr->bar[i] = pci_iomap(dev, i, 0);	
		if (!fr->bar[i]) {
			goto pci_map_err;
		} 
		
		dev_notice(&dev->dev, "BAR[%d] mapped to 0x%p, length 0x%lx\n",
		        i, fr->bar[i], fr->bar_length[i]);
	}

	return 0;
	
pci_map_err:
	while (--i >= 0) {
		pci_iounmap(dev, fr->bar[i]);
		fr->bar[i] = NULL;
	}
	return -EBUSY;
}

static int scan_bars(struct pci_dev *dev)
{
	struct fpga *fr = pci_get_drvdata(dev);	
	int i;

	for (i = 0; i < FPGA_FPGA_BAR_NUM; i++) {
		fr->bar_start[i] = pci_resource_start(dev, i);
		if (!fr->bar_start[i])
			break;
			
		fr->bar_length[i] = pci_resource_len(dev, i);
				
		dev_notice
		    (&dev->dev, "BAR[%d] 0x%08llx, length 0x%lx\n",
		     i, fr->bar_start[i], fr->bar_length[i]);
	}

	fr->bar_num = i;
	
	return 0;
}

static int fpga_probe(struct pci_dev *dev,
			       const struct pci_device_id *id)
{
	int rc = 0;
	struct fpga *fr = NULL;


	fr = kzalloc(sizeof(struct fpga), GFP_KERNEL);
	if (!fr) {
		dev_warn(&dev->dev, "alloc fpga failed\n");	
		return -EBUSY;
	}

	fr->pci_dev = dev;
	pci_set_drvdata(dev, fr);

	pci_read_config_byte(dev, PCI_REVISION_ID, &fr->revision);
	pci_read_config_byte(dev, PCI_INTERRUPT_PIN, &fr->irq_pin);
	pci_read_config_byte(dev, PCI_INTERRUPT_LINE, &fr->irq_line);


	dev_dbg(&dev->dev, "irq pin: %d line: %d num: %d\n",
			fr->irq_pin, fr->irq_line, dev->irq);

	rc = pci_enable_device(dev);
	if (rc) {
		dev_warn(&dev->dev, "enable device failed\n");
		goto enable_dev_exit;
	}

	rc = pci_request_regions(dev, FPGA_DRIVER_NAME);
	if (rc) {
		dev_err(&dev->dev, "request regions failed\n");
		goto pci_request_err;
	}

	pci_set_master(dev);

	scan_bars(dev);
	rc = map_bars(dev);
	if (rc) {
		dev_err(&dev->dev, "could not map BAR\n");
		goto map_err;
	}

	
	fr->miscdev.minor	= fpga_misc;
	fr->miscdev.name	= "fpga-pa8910";
	fr->miscdev.fops	= &fpga_misc_fops;
	
	rc = misc_register(&fr->miscdev);
	if (rc) {
		dev_err(&dev->dev, "misc_register failed\n");
		goto misc_err;
	}
	
	return 0;
	
misc_err:
	unmap_bars(dev);
map_err:
	pci_release_regions(dev);
pci_request_err:
	pci_disable_device(dev);
enable_dev_exit:
	kfree(fr);	
	return rc;
}

static void __exit fpga_remove(struct pci_dev *dev)
{
	struct fpga *fr = pci_get_drvdata(dev);

	misc_deregister(&fr->miscdev);

	unmap_bars(dev);
	
	pci_release_regions(dev);
	
	pci_disable_device(dev);

	kfree(fr);
}

static struct pci_device_id pci_ids[] = {
	{PCI_DEVICE(FPGA_VENDOR_ID, FPGA_DEVICE_ID)},
	{ /* end of list */ },
};
MODULE_DEVICE_TABLE(pci, pci_ids);


static struct pci_driver fpga_driver = {
	.name = FPGA_DRIVER_NAME,
	.id_table = pci_ids,
	.probe = fpga_probe,
	.remove = fpga_remove,
};

static int __init fpga_init(void)
{
	return pci_register_driver(&fpga_driver);
}

static void __exit fpga_exit(void)
{
	pci_unregister_driver(&fpga_driver);				 
}

module_init(fpga_init);
module_exit(fpga_exit);

MODULE_AUTHOR("");
MODULE_DESCRIPTION("PA8910 FPGA Driver");
MODULE_VERSION("0.1");
MODULE_LICENSE("Dual BSD/GPL");
