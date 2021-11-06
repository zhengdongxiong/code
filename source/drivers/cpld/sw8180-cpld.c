#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/device.h>
#include <linux/string.h>
#include <linux/jiffies.h>
#include <linux/delay.h>
#include <linux/stat.h>
#include <linux/sizes.h>
#include <linux/i2c.h>

/* 公共寄存器地址 */
#define CPLD_VERSION_REG		0x01
#define REBOOT_TYPE_REG			0x1E

/* 交换卡寄存器 */
#define SYS_INT_REG				0x06
#define FAN0_SPD_REG			0x08
#define FAN1_SPD_REG			0x09
#define FAN2_SPD_REG			0x0A
#define FAN3_SPD_REG			0x0B
#define FAN4_SPD_REG			0x0C
#define FAN5_SPD_REG			0x0D
#define FAN_STATUS_REG			0x0E
#define LED_CONTROL_REG			0x0F
#define BOOT_IMAGE_REG			0x1D
#define SLOT_INT_ERG			0x20
#define SLOT_PWREN_REG			0x21
#define SLOT_PRESENT_REG		0x22
#define SLOT_POWGD_REG			0x23
#define SLOT_RST_REG			0x24

/* 高速卡光模块在位寄存器 */
#define DS250_RST_REG			0x05
#define SFP28_PRESENT1_REG		0x11
#define SFP28_PRESENT2_REG		0x12
#define SFP28_PRESENT3_REG		0x13
#define SFP28_PRESENT4_REG		0x14
#define SFP28_PRESENT5_REG		0x15
#define SFP28_RXLOS1_REG		0x16
#define SFP28_RXLOS2_REG		0x17
#define SFP28_RXLOS3_REG		0x18
#define SFP28_RXLOS4_REG		0x19
#define SFP28_RXLOS5_REG		0x1A
#define SFP28_TXFAULT1_REG		0x1B
#define SFP28_TXFAULT2_REG		0x1C
#define SFP28_TXFAULT3_REG		0x1D
#define SFP28_TXFAULT4_REG		0x1E
#define SFP28_TXFAULT5_REG		0x1F
#define SFP28_TX_DIS0_REG		0x20
#define SFP28_TX_DIS1_REG		0x21
#define SFP28_TX_DIS2_REG		0x22
#define HS_SFP_RETIMER_MUX_REG	0x30
#define DS250_TX_RETIMER		0x25	/* retimer 选通写入值 */

/* 低速卡光模块在位寄存器 */
#define LS_PHY_RST_REG			0x05
#define SFP_PRESENT_REG			0x11
#define SFP28_RXLOS_REG			0x1A
#define LS_SFP_RETIMER_MUX_REG	0x1B
#define SFP28_TX_DIS_REG		0x31

/* 电源板寄存器 */
#define PSU_POWER_GOOD_REG		0x00	/* input port 0 */
#define PSU_PRESENT_REG			0x01	/* input port 1 */
#define PIO9535_OUT_REG0		0x02
#define PIO9535_OUT_REG1		0x03
#define PIO9535_DIR_REG0		0x06	/* IO0.0~IO0.7 */
#define PIO9535_DIR_REG1		0x07	/* IO1.0~IO1.7 */

/* SFP寄存器地址 */
#define SFP_INFO_ADDR			0x50 
#define SFP_STATUS_ADDR			0x51
#define SFP_EEPROM_SIZE			SZ_256

/* 线卡配置信息 */
#define SLOT_STATUS				0xFC

enum sw8180_i2cdev{
	cpld,
	hs_cpld,
	ls_cpld,
	pio9535,
};

struct sw8180_slot {
	struct delayed_work work;
	struct i2c_client *client;
};

static struct sw8180_slot slot_status;
static uint8_t slot_present;
static uint8_t add_slot;
static uint8_t remove_slot;
static ushort  delay_work_seconds = 2;
module_param(delay_work_seconds, ushort, S_IRUGO | S_IWUSR);
MODULE_PARM_DESC(delay_work_seconds, "Delay (in seconds), Check the SLOT_PRESENT_REG (default 2s)");


struct sw8180_cpld {
	struct mutex lock;
	enum sw8180_i2cdev kind;
};

static const struct i2c_device_id sw8180_ids[] = {
	[cpld]    = { "8180-cpld", cpld,    },
	[hs_cpld] = { "8180-hs",   hs_cpld, },
	[ls_cpld] = { "8180-ls",   ls_cpld, },
	[pio9535] = { "8180-pio",  pio9535, },
	{ /* END OF LIST */ }
};
MODULE_DEVICE_TABLE(i2c, sw8180_ids);

#define SW8180_SHOW_BYTE(_name, _reg)	SW8180_SYS_SHOW(_name, _reg, byte)
#define SW8180_SHOW_WORD(_name, _reg)	SW8180_SYS_SHOW(_name, _reg, word)
#define SW8180_RW_BYTE(_name, _reg)		SW8180_SYS_RW(_name, _reg, byte)
#define SW8180_RW_WORD(_name, _reg)		SW8180_SYS_RW(_name, _reg, word)

#define SW8180_SYS_SHOW(_name, _reg, _size) \
static ssize_t _name##_show(struct device *dev, \
				struct device_attribute *attr, char *buf) \
{ \
	struct i2c_client * client = to_i2c_client(dev); \
	int16_t value; \
\
	value = i2c_smbus_read_##_size##_data(client, _reg); \
	if(value < 0) { \
		dev_err(dev, "Read addr 0x%hX, reg 0x%hX fail\n", client->addr, _reg); \
		return value; \
	} \
\
	return sprintf(buf, "0x%X\n", value); \
} \
static DEVICE_ATTR_RO(_name);

#define SW8180_SYS_RW(_name, _reg, _size) \
static ssize_t _name##_show(struct device *dev, \
				struct device_attribute *attr, char *buf) \
{ \
	struct i2c_client * client = to_i2c_client(dev); \
	int16_t value; \
\
	value = i2c_smbus_read_##_size##_data(client, _reg); \
	if(value < 0) { \
		dev_err(dev, "Read addr 0x%hX, reg 0x%hX fail\n", client->addr, _reg); \
		return value; \
	} \
\
	return sprintf(buf, "0x%X\n", value); \
} \
\
static ssize_t _name##_store(struct device *dev, \
				struct device_attribute *attr, const char *buf, size_t count) \
{ \
	struct i2c_client *client = to_i2c_client(dev); \
	int16_t ret; \
	uint16_t value; \
\
	ret = sscanf(buf, "%hi", &value); \
	if (ret != 1) { \
		return -EINVAL; \
	} \
\
	/* cpld需要写16bit */		\
	ret = i2c_smbus_write_##_size##_data(client, _reg, value); \
	if (ret) { \
		dev_err(dev, "Write addr 0x%hX, reg 0x%X, value 0x%hX fail\n", \
				client->addr, _reg, value); \
		return ret; \
	} \
\
	return count; \
} \
static DEVICE_ATTR_RW(_name);

#if 0
static s32 sw8180_i2c_write_byte(const struct i2c_client *client, u16 addr,
				  u8 command, u8 value)
{
	union i2c_smbus_data data;
	data.byte = value;
	return i2c_smbus_xfer(client->adapter, addr, client->flags,
			      I2C_SMBUS_WRITE, command,
			      I2C_SMBUS_BYTE_DATA, &data);
}
#endif

static s32 sw8180_i2c_read(const struct i2c_client *client, u16 addr,
					u8 pos, u16 length, u8 *values)
{
	union i2c_smbus_data data;
	int status;

	if (length > I2C_SMBUS_BLOCK_MAX)
		length = I2C_SMBUS_BLOCK_MAX;		
	data.block[0] = length;
	
	status = i2c_smbus_xfer(client->adapter, addr, client->flags,
				I2C_SMBUS_READ, pos, I2C_SMBUS_I2C_BLOCK_DATA, &data);
	if (status < 0)
		return status;

	memcpy(values, &data.block[1], data.block[0]);
	return data.block[0];
}

static s32 sw8180_i2c_write(const struct i2c_client *client, u16 addr, 
					u8 pos, u16 length, const u8 *values)
{
	union i2c_smbus_data data;
	int status;

	if (length > I2C_SMBUS_BLOCK_MAX)
		length = I2C_SMBUS_BLOCK_MAX;
	data.block[0] = length;
	
	memcpy(data.block + 1, values, length);

	status = i2c_smbus_xfer(client->adapter, addr, client->flags,
				I2C_SMBUS_WRITE, pos, I2C_SMBUS_I2C_BLOCK_DATA, &data);
	if (status < 0)
		return status;			
  
	return data.block[0];
}

#define SW8180_SFP_INFO(_name, _sfp_addr) \
static ssize_t _name##_read(struct file *filp, struct kobject *kobj, \
				  struct bin_attribute *attr, \
				  char *buf, loff_t off, size_t count) \
{ \
	struct i2c_client *client = kobj_to_i2c_client(kobj); \
	struct sw8180_cpld *data  = i2c_get_clientdata(client); \
	uint8_t pos   = off; \
	uint16_t size = count; \
	int length    = 0; \
\
	mutex_lock(&data->lock); \
	while (size) { \
		length = sw8180_i2c_read(client, _sfp_addr, pos, size, buf); \
		if (length < 0) { \
			mutex_unlock(&data->lock); \
			dev_err(&client->dev, \
					"%s Card SFP Read reg 0x%02llX, count %lu fail. Check sfp_retimer_mux reg\n", \
					data->kind == hs_cpld ? "High-speed" : "Low-speed", off, count); \
			return length; \
		} \
		pos += length; \
		buf += length; \
		size -= length; \
	} \
	mutex_unlock(&data->lock); \
\
	dev_dbg(&client->dev, "SFP Read reg 0x%02llX, count %lu\n", off, count); \
\
	return count; \
} \
\
static ssize_t _name##_write(struct file *filp, struct kobject *kobj, \
				   struct bin_attribute *attr, \
				   char *buf, loff_t off, size_t count) \
{ \
	struct i2c_client *client = kobj_to_i2c_client(kobj); \
	struct sw8180_cpld *data  = i2c_get_clientdata(client); \
	uint8_t pos   = off; \
	uint16_t size = count; \
	int length    = 0; \
\
	mutex_lock(&data->lock); \
	while (size) { \
		length = sw8180_i2c_write(client, _sfp_addr, pos, size, buf); \
		if (length < 0) { \
			mutex_unlock(&data->lock); 			\
			dev_err(&client->dev, 			\
					"%s Card SFP Write reg 0x%02llX, count %lu fail. Check sfp_retimer_mux reg\n", \
					data->kind == hs_cpld ? "High-speed" : "Low-speed", off, count); \
			return length; \
		} \
		pos += length; \
		buf += length; \
		size -= length; \
	} \
	mutex_unlock(&data->lock); \
\
	dev_dbg(&client->dev, "SFP Write reg 0x%02llX, count %lu\n", off, count); \
\
	return count; \
} \
static struct bin_attribute bin_attr_##_name = { \
	.attr  = { .name = __stringify(_name), .mode = S_IRUGO | S_IWUSR, }, \
	.size  = SFP_EEPROM_SIZE,	 \
	.read  = _name##_read,			\
	.write = _name##_write, 			\
};

static ssize_t sfp_retimer_mux_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	struct i2c_client * client = to_i2c_client(dev);
	struct sw8180_cpld *data   = dev_get_drvdata(dev);
	int16_t value;
	uint8_t reg;

	switch (data->kind) {
	case hs_cpld: 
		reg = HS_SFP_RETIMER_MUX_REG;
		break;
	case ls_cpld:
		reg = LS_SFP_RETIMER_MUX_REG;
		break;
	default:
		return -EINVAL;
	}

	value = i2c_smbus_read_word_data(client, reg);
	if(value < 0) {
		dev_err(dev, "Read addr 0x%hX, reg 0x%X fail\n", client->addr, reg);
		return value;
	}

	return sprintf(buf, "0x%X\n", value);
}

static ssize_t sfp_retimer_mux_store(struct device *dev,
				struct device_attribute *attr, const char *buf, size_t count)
{
	struct i2c_client * client = to_i2c_client(dev);
	struct sw8180_cpld *data   = dev_get_drvdata(dev);
	uint16_t value;
	uint8_t reg;
	int16_t ret;

	switch (data->kind) {
	case hs_cpld: 
		reg = HS_SFP_RETIMER_MUX_REG;
		break;
	case ls_cpld:
		reg = LS_SFP_RETIMER_MUX_REG;
		break;
	default:
		return -EINVAL;
	}

	ret = sscanf(buf, "%hi", &value); 
	if (ret != 1) { 
		return -EINVAL;
	} 

	mutex_lock(&data->lock);
	ret = i2c_smbus_write_word_data(client, reg, value);
	mutex_unlock(&data->lock);

	if (ret) { 
		dev_err(dev, "Write addr 0x%hX, reg 0x%hX, value 0x%hX fail\n", 
				client->addr, reg, value); 
		return ret;
	} 

	return count;
}

#if 0
static ssize_t ds250_tx_config(struct i2c_client *client, uint8_t addr)
{
	char reg[]   = { 0xFF, 0xFC, 0x0A, 0x2F, 0x1F, 0x31, 0x1E, 0x0A, 0x3D, 0x3E, 0x3F };
	char value[] = { 0x03, 0x01, 0x0C, 0x54, 0x0B, 0x40, 0x02, 0x00, 0x96, 0x46, 0x43 };
	s32 ret = 0;
	int i   = 0;
	
	ret = i2c_smbus_write_word_data(client, HS_MUX_SFP_REG, DS250_TX_RETIMER);
	if (ret) {
		dev_err(&client->dev, "Set sfp_retimer_mux fail\n");
		goto tx_config_exit;
	}
	
	for (i = 0; i < ARRAY_SIZE(reg); i++) {
		ret = sw8180_i2c_write_byte(client, addr, reg[i], value[i]);
		if (ret) {
			dev_err(&client->dev, "Set tx retimer fail\n");
			break;
		}
	}
	
tx_config_exit:
	return ret;
}

static ssize_t ds250_retimer_store(struct device *dev,
				struct device_attribute *attr, const char *buf, size_t count)
{
	struct i2c_client * client = to_i2c_client(dev); 
	struct sw8180_cpld *data   = dev_get_drvdata(dev); 
	
	mutex_lock(&data->lock); 
	count = ds250_tx_config(client, 0x18); 
	mutex_unlock(&data->lock); 

	return count;
}				
#endif

static inline void sw8180_noify(struct device *dev, enum kobject_action action, 
				uint8_t update_msg, uint8_t *udev_data)
{

	do {
		*udev_data = update_msg & (~(update_msg - 1));
		kobject_uevent(&dev->kobj, action);
		msleep_interruptible(5);
		update_msg = update_msg & (update_msg -1);
		
		dev_dbg(dev, "update bit 0x%X, add/remove slot 0x%X/0x%X\n",
			update_msg, add_slot, remove_slot);
			
	}while(update_msg);	
}

static void sw8180_slot_notify_work(struct work_struct *work)
{
	struct sw8180_slot *slot_status = container_of(work, struct sw8180_slot, work.work);	
	struct i2c_client *client = slot_status->client;
	int16_t current_present;
	uint8_t update_bit;
#ifdef READ_POWER_OK	
	int16_t pwr_gd;
#endif
	
	current_present = i2c_smbus_read_byte_data(client, SLOT_PRESENT_REG);
#ifdef READ_POWER_OK	
	pwr_gd 			= i2c_smbus_read_byte_data(client, SLOT_POWGD_REG);
#endif	
	
#ifdef READ_POWER_OK
	if(current_present < 0 || pwr_gd < 0) {
		dev_err(&client->dev, "Read addr 0x%hX, err code: %d, %d\n", 
					client->addr, current_present, pwr_gd);
		return ;
	}
#else
	if (current_present < 0) {
		dev_err(&client->dev, "Read addr 0x%hX, err code: %d\n", 
				client->addr, current_present);
		return ;
	}
#endif

	current_present &= SLOT_STATUS;
	
#ifdef READ_POWER_OK	
	pwr_gd			&= SLOT_STATUS;
#endif

	/*
	 * SLOT_PWREN_REG 默认为0xFC 不需要操作
	 * SLOT_POWGD_REG 高速/低速卡上电pwr_gd 为1/0 ???
	 *		目前   pwr_gd = 0x08 = 0000 1000 ---+
	 *                                        & remove_slot = 0x0
	 *		remove_slot = 0x20 = 0010 0000 ---+
	 *                                        & remove_slot = 0x20
	 *		正常   pwr_gd = 0x28 = 0010 1000 ---+
	 */
#ifdef READ_POWER_OK 
	update_bit = current_present ^ slot_present;
	if (update_bit) {
		add_slot    = slot_present & update_bit;	
		remove_slot = current_present & update_bit;

		dev_dbg(&client->dev, "update bit 0x%X, add/remove slot 0x%X/0x%X\n",
			update_bit, add_slot, remove_slot);
			
		if(add_slot) {
			add_slot |= pwr_gd;		/* write to SLOT_PWREN_REG */
			pwr_gd   = add_slot;	
			kobject_uevent(&client->dev.kobj, KOBJ_ONLINE);
		}
		
		if(remove_slot) {
			remove_slot = ~remove_slot & pwr_gd;	/* write to SLOT_PWREN_REG */
			kobject_uevent(&client->dev.kobj, KOBJ_OFFLINE);
		}
		
		dev_dbg(&client->dev, "after update bit 0x%X, add/remove slot 0x%X/0x%X\n",
			update_bit, add_slot, remove_slot);
		
		slot_present = current_present;
	}
#endif
	/*
	 * 0在位, 1不在位
	 * slot_present    = 0x31 = 0011 0001 ---+ 
	 *                                       ^ update_bit = 0x71 = 0111 0001
	 * current_present = 0x40 = 0100 0000 ---+ (6拔出, 5,4,0插入)
	 *
	 * slot_present    = 0x31 = 0011 0001 ---+
	 *                                       & add_slot = 0011 0001 (5,4,0为插入)
	 * update_bit      = 0x71 = 0111 0001 ---+	
	 *                                       & remove_slot = 0100 0000 (6拔出)
	 * current_present = 0x40 = 0100 0000 ---+
	 */
	update_bit = current_present ^ slot_present;
	if (update_bit) {
		add_slot    = slot_present & update_bit;	
		remove_slot = current_present & update_bit;

		if(add_slot)
			sw8180_noify(&client->dev, KOBJ_ONLINE, add_slot, &add_slot);

		
		if(remove_slot)
			sw8180_noify(&client->dev, KOBJ_OFFLINE, remove_slot, &remove_slot);

				
		slot_present = current_present;
	}
	
	schedule_delayed_work(&slot_status->work, delay_work_seconds * HZ);
	
}

static ssize_t add_slot_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	return sprintf(buf, "0x%X\n", add_slot);
}
static ssize_t remove_slot_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	return sprintf(buf, "0x%X\n", remove_slot);
}
static DEVICE_ATTR_RO(add_slot);
static DEVICE_ATTR_RO(remove_slot);



static DEVICE_ATTR_RW(sfp_retimer_mux);
SW8180_SHOW_BYTE(cpld_version, CPLD_VERSION_REG)
SW8180_RW_WORD(reboot_type, REBOOT_TYPE_REG)

/* 交换卡cpld */
SW8180_SHOW_BYTE(sys_int, SYS_INT_REG)
SW8180_SHOW_BYTE(fan0, FAN0_SPD_REG)
SW8180_SHOW_BYTE(fan1, FAN1_SPD_REG)
SW8180_SHOW_BYTE(fan2, FAN2_SPD_REG)
SW8180_SHOW_BYTE(fan3, FAN3_SPD_REG)
SW8180_SHOW_BYTE(fan4, FAN4_SPD_REG)
SW8180_SHOW_BYTE(fan5, FAN5_SPD_REG)
SW8180_RW_WORD(fan_speed, FAN_STATUS_REG)
SW8180_RW_WORD(led_control, LED_CONTROL_REG)
SW8180_RW_WORD(boot_image, BOOT_IMAGE_REG)
SW8180_SHOW_BYTE(slot_int, SLOT_INT_ERG)
SW8180_RW_WORD(slot_pwr_en, SLOT_PWREN_REG)
SW8180_SHOW_BYTE(slot_present, SLOT_PRESENT_REG)
SW8180_SHOW_BYTE(slot_pwr_gd, SLOT_POWGD_REG)
SW8180_RW_WORD(slot_reset, SLOT_RST_REG)

/* 高速卡cpld */
SW8180_RW_WORD(ds250_reset, DS250_RST_REG)
SW8180_SHOW_BYTE(sfp0_7_present, SFP28_PRESENT1_REG)
SW8180_SHOW_BYTE(sfp8_15_present, SFP28_PRESENT2_REG)
SW8180_SHOW_BYTE(sfp16_23_present, SFP28_PRESENT3_REG)
SW8180_SHOW_BYTE(sfp24_31_present, SFP28_PRESENT4_REG)
SW8180_SHOW_BYTE(sfp32_35_present, SFP28_PRESENT5_REG)
SW8180_SHOW_BYTE(sfp0_7_rxlos, SFP28_RXLOS1_REG)
SW8180_SHOW_BYTE(sfp8_15_rxlos, SFP28_RXLOS2_REG)
SW8180_SHOW_BYTE(sfp16_23_rxlos, SFP28_RXLOS3_REG)
SW8180_SHOW_BYTE(sfp24_31_rxlos, SFP28_RXLOS4_REG)
SW8180_SHOW_BYTE(sfp32_35_rxlos, SFP28_RXLOS5_REG)
SW8180_SHOW_BYTE(sfp0_7_txfault, SFP28_TXFAULT1_REG)
SW8180_SHOW_BYTE(sfp8_15_txfault, SFP28_TXFAULT2_REG)
SW8180_SHOW_BYTE(sfp16_23_txfault, SFP28_TXFAULT3_REG)
SW8180_SHOW_BYTE(sfp24_31_txfault, SFP28_TXFAULT4_REG)
SW8180_SHOW_BYTE(sfp32_35_txfault, SFP28_TXFAULT5_REG)
SW8180_RW_WORD(sfp0_15_txdisable, SFP28_TX_DIS0_REG)
SW8180_RW_WORD(sfp16_31_txdisable, SFP28_TX_DIS1_REG)
SW8180_RW_WORD(sfp32_35_txdisable, SFP28_TX_DIS2_REG)

/* 低速卡cpld */
SW8180_RW_WORD(phy_reset, LS_PHY_RST_REG)
SW8180_SHOW_WORD(sfp0_11_present, SFP_PRESENT_REG)
SW8180_SHOW_WORD(sfp0_11_rxlos, SFP28_RXLOS_REG)
SW8180_RW_WORD(sfp0_11_txdisable, SFP28_TX_DIS_REG)

/* 电源板信息 */
SW8180_SHOW_BYTE(psu_power_good, PSU_POWER_GOOD_REG)
SW8180_SHOW_BYTE(psu_present, PSU_PRESENT_REG)
SW8180_RW_BYTE(pio_output0, PIO9535_OUT_REG0)
SW8180_RW_BYTE(pio_output1, PIO9535_OUT_REG1)
SW8180_RW_BYTE(pio_dir0, PIO9535_DIR_REG0)
SW8180_RW_BYTE(pio_dir1, PIO9535_DIR_REG0)

/*
 * 添加retimer DS250
 * 		retimer操作(0x18 ~ 0x20)
 *			1.用户操作选通 echo          > sfp_retimer_mux
 *			2.retimer 操作
 */


/*
 * 添加DS100(低速卡上)
 * 		翻转线序寄存器()rx_retimer 0x20
 *		tx_retimer 0x21
 */

/* 光模块信息 */
SW8180_SFP_INFO(sfp_info_50, SFP_INFO_ADDR)
SW8180_SFP_INFO(sfp_info_51, SFP_STATUS_ADDR)

static struct attribute *sw_cpld_attrs[] = {
	&dev_attr_cpld_version.attr,
	&dev_attr_sys_int.attr,
	&dev_attr_fan0.attr,
	&dev_attr_fan1.attr,
	&dev_attr_fan2.attr,
	&dev_attr_fan3.attr,
	&dev_attr_fan4.attr,
	&dev_attr_fan5.attr,
	&dev_attr_fan_speed.attr,
	&dev_attr_led_control.attr,
	&dev_attr_boot_image.attr,
	&dev_attr_reboot_type.attr,
	&dev_attr_slot_int.attr,
	&dev_attr_slot_pwr_en.attr,
	&dev_attr_slot_present.attr,
	&dev_attr_slot_pwr_gd.attr,
	&dev_attr_slot_reset.attr,
	&dev_attr_add_slot.attr,
	&dev_attr_remove_slot.attr,
	NULL
};

static struct attribute *hs_cpld_attrs[] = {
	&dev_attr_cpld_version.attr,
	&dev_attr_ds250_reset.attr,
	&dev_attr_sfp0_7_present.attr,
	&dev_attr_sfp8_15_present.attr,
	&dev_attr_sfp16_23_present.attr,
	&dev_attr_sfp24_31_present.attr,
	&dev_attr_sfp32_35_present.attr,
	&dev_attr_sfp0_7_rxlos.attr,
	&dev_attr_sfp8_15_rxlos.attr,
	&dev_attr_sfp16_23_rxlos.attr,
	&dev_attr_sfp24_31_rxlos.attr,
	&dev_attr_sfp32_35_rxlos.attr,
	&dev_attr_sfp0_7_txfault.attr,
	&dev_attr_sfp8_15_txfault.attr,
	&dev_attr_sfp16_23_txfault.attr,
	&dev_attr_sfp24_31_txfault.attr,
	&dev_attr_sfp32_35_txfault.attr,
	&dev_attr_sfp0_15_txdisable.attr,
	&dev_attr_sfp16_31_txdisable.attr,
	&dev_attr_sfp32_35_txdisable.attr,
	&dev_attr_sfp_retimer_mux.attr,
	&dev_attr_reboot_type.attr,
	/* 补充retimer */
	NULL	
};

static struct attribute *ls_cpld_attrs[] = {
	&dev_attr_cpld_version.attr,
	&dev_attr_phy_reset.attr,
	&dev_attr_sfp0_11_present.attr,
	&dev_attr_sfp0_11_rxlos.attr,
	&dev_attr_sfp_retimer_mux.attr,
	&dev_attr_sfp0_11_txdisable.attr,
	/* 补充retimer */
	NULL
};

static struct attribute *pio9535_attrs[] = {
	&dev_attr_psu_power_good.attr,
	&dev_attr_psu_present.attr,
	&dev_attr_pio_output0.attr,
	&dev_attr_pio_output1.attr,
	&dev_attr_pio_dir0.attr,
	&dev_attr_pio_dir1.attr,
	NULL
};

static struct bin_attribute *bin_sfp_attrs[] = {
	&bin_attr_sfp_info_50,
	&bin_attr_sfp_info_51,
	NULL
};

static struct attribute_group sw_cpld_group = {
	.attrs = sw_cpld_attrs,
};

static struct attribute_group hs_cpld_group = {
	.attrs = hs_cpld_attrs,
	.bin_attrs = bin_sfp_attrs,
};

static struct attribute_group ls_cpld_group = {
	.attrs = ls_cpld_attrs,
	.bin_attrs = bin_sfp_attrs,
};

static struct attribute_group pio9535_group = {
	.attrs = pio9535_attrs,
};

static inline int sw8180_create_sys(struct device *dev, 
							  const struct attribute_group *group)
{	
	return sysfs_create_group(&dev->kobj, group);
}

static inline void sw8180_remove_sys(struct device *dev, 
							  const struct attribute_group *group)
{
	return sysfs_remove_group(&dev->kobj, group);
}

static int sw8180_probe(struct i2c_client *client)
{	
	const struct i2c_device_id *id = i2c_match_id(sw8180_ids, client);	
	struct attribute_group *group = NULL;
	struct sw8180_cpld *data;
	int ret;

	if (i2c_smbus_read_byte_data(client, 0x0) < 0)
		return -ENODEV;

	data = devm_kzalloc(&client->dev, sizeof(struct sw8180_cpld), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	mutex_init(&data->lock);

	data->kind = id->driver_data;

	i2c_set_clientdata(client, data);

	switch (data->kind) {
	case cpld:
		group = &sw_cpld_group;
		slot_present = SLOT_STATUS;
		slot_status.client = client;
		INIT_DEFERRABLE_WORK(&slot_status.work, sw8180_slot_notify_work);
		break;
	case hs_cpld: 
		group = &hs_cpld_group;
		break;
	case ls_cpld:
		group = &ls_cpld_group;
		break;
	case pio9535:
		group = &pio9535_group;
		break;
	}

	ret = sw8180_create_sys(&client->dev, group);
	if (ret)
		return ret;

	switch (data->kind) {
	case cpld:
		schedule_delayed_work(&slot_status.work, delay_work_seconds * HZ);
		break;	
	case ls_cpld:
	case pio9535:
		kobject_uevent(&client->dev.kobj, KOBJ_BIND);
		break;
	default:
		break;
	}
	
	return 0;
}

static int sw8180_remove(struct i2c_client *client)
{
	struct sw8180_cpld *data = i2c_get_clientdata(client);
	struct attribute_group *group = NULL;
	
	switch (data->kind) {
	case cpld:
		group = &sw_cpld_group;
		cancel_delayed_work(&slot_status.work);
		break;
	case hs_cpld: 
		group = &hs_cpld_group;
		break;
	case ls_cpld:
		group = &ls_cpld_group;
		break;
	case pio9535:
		group = &pio9535_group;
		break;	
	}

	sw8180_remove_sys(&client->dev, group);
	
	return 0;
}

static struct i2c_driver sw8180_driver = {
	.driver = {
		.name = "sw8180-i2c-dev",
	},
	.probe_new = sw8180_probe,	
	.remove = sw8180_remove,
	.id_table = sw8180_ids,
};
module_i2c_driver(sw8180_driver);

MODULE_DESCRIPTION("SW8180 I2C devices");
MODULE_AUTHOR("");
MODULE_LICENSE("GPL");
