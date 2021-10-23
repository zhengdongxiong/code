#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/device.h>
#include <linux/string.h>
#include <linux/jiffies.h>
#include <linux/stat.h>
#include <linux/sizes.h>
#include <linux/i2c.h>

/* 公共地址 */
#define CPLD_VERSION_REG		0x01

/* 交换卡寄存器 */
#define FAN0_SPD_REG			0x08
#define FAN1_SPD_REG			0x09
#define FAN2_SPD_REG			0x0A
#define FAN3_SPD_REG			0x0B
#define FAN4_SPD_REG			0x0C
#define FAN5_SPD_REG			0x0D
#define FAN_STATUS_REG			0x0E
#define SLOT_PRESENT_REG		0x22
#define SLOT_POWER_REG			0x23

/* 高速卡光模块在位寄存器 */
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
#define HS_MUX_SFP_REG			0x30

/* 低速卡光模块在位寄存器 */
#define SFP_PRESENT_REG			0x11
#define SFP28_RXLOS_REG			0x1A
#define LS_MUX_SFP_REG			0x1B

/* 电源板寄存器 */
#define PSU_POWER_GOOD_REG		0x00
#define PSU_PRESENT				0x01

/* SFP寄存器地址 */
#define SFP_INFO_ADDR			0x50 
#define SFP_STATUS_ADDR			0x51
#define SFP_EEPROM_SIZE			SZ_256


enum sw8180_i2cdev{
	cpld,
	hs_cpld,
	ls_cpld,
	sw_psu,
};

struct sw8180_cpld {
	struct mutex lock;
	enum sw8180_i2cdev kind;
};

static const struct i2c_device_id sw8180_ids[] = {
	[cpld]    = { "8180-cpld", cpld,    },
	[hs_cpld] = { "8180-hs",   hs_cpld, },
	[ls_cpld] = { "8180-ls",   ls_cpld, },
	[sw_psu]  = { "8180-psu",  sw_psu,  },
	{ /* END OF LIST */ }
};
MODULE_DEVICE_TABLE(i2c, sw8180_ids);

#define SW8180_SYS_SHOW(_name, _reg, _size) \
static ssize_t _name##_show(struct device *dev, \
				struct device_attribute *attr, char *buf) \
{ \
	struct i2c_client * client = to_i2c_client(dev); \
	struct sw8180_cpld *data   = dev_get_drvdata(dev); \
	uint16_t value; \
\
	mutex_lock(&data->lock); \
\
	value = i2c_smbus_read_##_size##_data(client, _reg); \
	if(value < 0) { \
		dev_err(dev, "Read addr 0x%hX, reg 0x%hX fail\n", client->addr, _reg); \
		mutex_unlock(&data->lock); \
		return value; \
	} \
\
	mutex_unlock(&data->lock); \
\
	return sprintf(buf, "0x%04X\n", value); \
} \
static DEVICE_ATTR_RO(_name);

#define SW8180_SYS_RW(_name, _reg, _size) \
static ssize_t _name##_show(struct device *dev, \
				struct device_attribute *attr, char *buf) \
{ \
	struct i2c_client * client = to_i2c_client(dev); \
	struct sw8180_cpld *data   = dev_get_drvdata(dev); \
	uint16_t value; \
\
	mutex_lock(&data->lock); \
\
	value = i2c_smbus_read_##_size##_data(client, _reg); \
	if(value < 0) { \
		dev_err(dev, "Read addr 0x%hX, reg 0x%hX fail\n", client->addr, _reg); \
		mutex_unlock(&data->lock); \
		return value; \
	} \
\
	mutex_unlock(&data->lock); \
\
	return sprintf(buf, "0x%04X\n", value); \
} \
\
static ssize_t _name##_store(struct device *dev, \
				struct device_attribute *attr, const char *buf, size_t count) \
{ \
	struct i2c_client *client = to_i2c_client(dev); \
	struct sw8180_cpld *data  = dev_get_drvdata(dev); \
	int ret; \
	uint16_t value; \
\
	mutex_lock(&data->lock); \
\
	ret = sscanf(buf, "%hi", &value); \
	if (ret != 1) { \
		mutex_unlock(&data->lock); \
		return -EINVAL; \
	} \
\
	ret = i2c_smbus_write_##_size##_data(client, _reg, value); \
	if (ret) { \
		dev_err(dev, "Write addr 0x%hX, reg 0x%X, value 0x%hX fail\n", \
				client->addr, _reg, value); \
		mutex_unlock(&data->lock); \
		return ret; \
	} \
\
	mutex_unlock(&data->lock);	\
\
	return count; \
} \
static DEVICE_ATTR_RW(_name);

static ssize_t sfp_mux_show(struct device *dev,
				struct device_attribute *attr, char *buf)
{
	struct i2c_client * client = to_i2c_client(dev);
	struct sw8180_cpld *data   = dev_get_drvdata(dev);
	uint16_t value;
	uint8_t reg;

	switch (data->kind) {
	case hs_cpld: 
		reg = HS_MUX_SFP_REG;
		break;
	case ls_cpld:
		reg = LS_MUX_SFP_REG;
		break;
	default:
		return -EINVAL;
	}

	mutex_lock(&data->lock);

	value = i2c_smbus_read_word_data(client, reg);
	if(value < 0) {
		dev_err(dev, "Read addr 0x%hX, reg 0x%X fail\n", client->addr, reg);
		mutex_unlock(&data->lock);
		return value;
	}
	
	mutex_unlock(&data->lock);

	return sprintf(buf, "0x%04X\n", value);;
}

static ssize_t sfp_mux_store(struct device *dev,
				struct device_attribute *attr, const char *buf, size_t count)
{
	struct i2c_client * client = to_i2c_client(dev);
	struct sw8180_cpld *data   = dev_get_drvdata(dev);
	uint16_t value;
	uint8_t reg;
	int ret;

	switch (data->kind) {
	case hs_cpld: 
		reg = HS_MUX_SFP_REG;
		break;
	case ls_cpld:
		reg = LS_MUX_SFP_REG;
		break;
	default:
		return -EINVAL;
	}

	mutex_lock(&data->lock); 

	ret = sscanf(buf, "%hi", &value); 
	if (ret != 1) { 
		ret = -EINVAL;
		goto sfp_info_stroe_err;
	} 

	ret = i2c_smbus_write_word_data(client, reg, value); 
	if (ret) { 
		dev_err(dev, "Write addr 0x%hX, reg 0x%hX, value 0x%hX fail\n", 
				client->addr, reg, value); 
		goto sfp_info_stroe_err;
	} 
	
	mutex_unlock(&data->lock);	
	
	return count;

sfp_info_stroe_err:
	mutex_unlock(&data->lock); 
	return ret;
}

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

#define SW8180_DEVICE_BIN_ATTR(_name) \
	struct bin_attribute bin_attr_##_name = { \
	.attr  = { .name = __stringify(_name), .mode = S_IRUGO | S_IWUSR }, \
	.size  = SFP_EEPROM_SIZE,	 \
	.read  = _name##_read,			\
	.write = _name##_write, 			\
}

#define SW8180_SFP_INFO(_name, _sfp_addr) \
static ssize_t _name##_read(struct file *filp, struct kobject *kobj, \
				  struct bin_attribute *attr, \
				  char *buf, loff_t off, size_t count) \
{ \
	struct i2c_client *client = kobj_to_i2c_client(kobj); \
	struct sw8180_cpld *data  = i2c_get_clientdata(client); \
	uint16_t pos  = off; \
	uint16_t size = count; \
	int length    = 0; \
	uint16_t current_sfp; \
	uint8_t reg; \
\
	switch (data->kind) { \
	case hs_cpld: \
		reg = HS_MUX_SFP_REG; \
		break; \
	case ls_cpld: \
		reg = LS_MUX_SFP_REG; \
		break; \
	default: \
		return -EINVAL; \
	} \
\
	mutex_lock(&data->lock); \
\
	current_sfp = i2c_smbus_read_word_data(client, reg); \
	if(current_sfp < 0) { \
		dev_err(&client->dev, "Read addr 0x%hX, reg 0x%hX fail\n", \
					client->addr, reg); \
		mutex_unlock(&data->lock); \
		return length; \
	} \
\
	while (size > 0) { \
		length = sw8180_i2c_read(client, _sfp_addr, pos, size, buf); \
		if (length < 0) { \
			dev_err(&client->dev, "%s Card SFP %hd Read reg 0x%02llX, count %lu fail\n", \
					data->kind == hs_cpld ? "High-speed" : "Low-speed", \
					current_sfp, off, count); \
			mutex_unlock(&data->lock); \
			return length; \
		} \
		pos += length; \
		buf += length; \
		size -= length; \
	} \
\
	dev_dbg(&client->dev, "SFP Read reg 0x%02llX, count %lu\n", off, count); \
\
	mutex_unlock(&data->lock); \
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
	uint16_t pos  = off; \
	uint16_t size = count; \
	int length    = 0; \
	uint16_t current_sfp; \
	uint8_t reg; \
\
	switch (data->kind) { \
	case hs_cpld: \
		reg = HS_MUX_SFP_REG; \
		break; \
	case ls_cpld: \
		reg = LS_MUX_SFP_REG; \
		break; \
	default: \
		return -EINVAL; \
	} \
\
	mutex_lock(&data->lock); \
\
	current_sfp = i2c_smbus_read_word_data(client, reg); \
	if(current_sfp < 0) { \
		dev_err(&client->dev, "Read addr 0x%hX, reg 0x%hX fail\n", \
					client->addr, reg); \
		mutex_unlock(&data->lock); \
		return length; \
	} \
\
	while (size > 0) { \
		length = sw8180_i2c_write(client, _sfp_addr, pos, size, buf); \
		if (length < 0) { \
			dev_err(&client->dev, "%s Card SFP %hd Read reg 0x%02llX, count %lu fail\n", \
					data->kind == hs_cpld ? "High-speed" : "Low-speed", \
					current_sfp, off, count); \
			mutex_unlock(&data->lock); \
			return length; \
		} \
		pos += length; \
		buf += length; \
		size -= length;  \
	} \
\
	dev_dbg(&client->dev, "SFP Write reg 0x%02llX, count %lu\n", off, count); \
\
	mutex_unlock(&data->lock); \
\
	return count; \
} \
static SW8180_DEVICE_BIN_ATTR(_name);


SW8180_SYS_SHOW(cpld_version, CPLD_VERSION_REG, byte)
static DEVICE_ATTR_RW(sfp_mux);

/* 交换卡cpld */
SW8180_SYS_SHOW(fan0, FAN0_SPD_REG, byte)
SW8180_SYS_SHOW(fan1, FAN1_SPD_REG, byte)
SW8180_SYS_SHOW(fan2, FAN2_SPD_REG, byte)
SW8180_SYS_SHOW(fan3, FAN3_SPD_REG, byte)
SW8180_SYS_SHOW(fan4, FAN4_SPD_REG, byte)
SW8180_SYS_SHOW(fan5, FAN5_SPD_REG, byte)
SW8180_SYS_RW(fan_speed, FAN_STATUS_REG, word)
SW8180_SYS_SHOW(slot_present, SLOT_PRESENT_REG, byte)
SW8180_SYS_SHOW(slot_power, SLOT_POWER_REG, byte)

/* 高速卡cpld */
SW8180_SYS_SHOW(sfp0_7_present, SFP28_PRESENT1_REG, byte)
SW8180_SYS_SHOW(sfp8_15_present, SFP28_PRESENT2_REG, byte)
SW8180_SYS_SHOW(sfp16_23_present, SFP28_PRESENT3_REG, byte)
SW8180_SYS_SHOW(sfp24_31_present, SFP28_PRESENT4_REG, byte)
SW8180_SYS_SHOW(sfp32_35_present, SFP28_PRESENT5_REG, byte)
SW8180_SYS_SHOW(sfp0_7_rxlos, SFP28_RXLOS1_REG, byte)
SW8180_SYS_SHOW(sfp8_15_rxlos, SFP28_RXLOS2_REG, byte)
SW8180_SYS_SHOW(sfp16_23_rxlos, SFP28_RXLOS3_REG, byte)
SW8180_SYS_SHOW(sfp24_31_rxlos, SFP28_RXLOS4_REG, byte)
SW8180_SYS_SHOW(sfp32_35_rxlos, SFP28_RXLOS5_REG, byte)
SW8180_SYS_SHOW(sfp0_7_txfault, SFP28_TXFAULT1_REG, byte)
SW8180_SYS_SHOW(sfp8_15_txfault, SFP28_TXFAULT2_REG, byte)
SW8180_SYS_SHOW(sfp16_23_txfault, SFP28_TXFAULT3_REG, byte)
SW8180_SYS_SHOW(sfp24_31_txfault, SFP28_TXFAULT4_REG, byte)
SW8180_SYS_SHOW(sfp32_35_txfault, SFP28_TXFAULT5_REG, byte)

/* 低速卡cpld */
SW8180_SYS_SHOW(sfp0_11_present, SFP_PRESENT_REG, word)
SW8180_SYS_SHOW(sfp0_11_rxlos, SFP28_RXLOS_REG, word)

/* 电源板信息 */
SW8180_SYS_SHOW(psu_power_good, PSU_POWER_GOOD_REG, byte)
SW8180_SYS_SHOW(psu_present, PSU_PRESENT, byte)

/* 光模块信息 */
SW8180_SFP_INFO(sfp_info_50, SFP_INFO_ADDR)
SW8180_SFP_INFO(sfp_info_51, SFP_STATUS_ADDR)


static struct attribute *switch_attrs[] = {
	&dev_attr_cpld_version.attr,
	&dev_attr_fan0.attr,
	&dev_attr_fan1.attr,
	&dev_attr_fan2.attr,
	&dev_attr_fan3.attr,
	&dev_attr_fan4.attr,
	&dev_attr_fan5.attr,
	&dev_attr_fan_speed.attr,
	&dev_attr_slot_present.attr,
	&dev_attr_slot_power.attr,
	NULL
};

static struct attribute *high_speed_attrs[] = {
	&dev_attr_cpld_version.attr,
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
	&dev_attr_sfp_mux.attr,
	NULL
};

static struct attribute *low_speed_attrs[] = {
	&dev_attr_cpld_version.attr,
	&dev_attr_sfp0_11_present.attr,
	&dev_attr_sfp0_11_rxlos.attr,
	&dev_attr_sfp_mux.attr,
	NULL
};

static struct attribute *psu_attrs[] = {
	&dev_attr_psu_power_good.attr,
	&dev_attr_psu_present.attr,
	NULL
};

static struct bin_attribute *bin_sfp_attrs[] = {
	&bin_attr_sfp_info_50,
	&bin_attr_sfp_info_51,
	NULL
};

static struct attribute_group switch_group = {
	.attrs = switch_attrs,
};

static struct attribute_group high_speed_group = {
	.attrs = high_speed_attrs,
	.bin_attrs = bin_sfp_attrs,
};

static struct attribute_group low_speed_group = {
	.attrs = low_speed_attrs,
	.bin_attrs = bin_sfp_attrs,
};

static struct attribute_group psu_group = {
	.attrs = psu_attrs,
};

static inline int sw8180_create_sys(struct device *dev, 
							   struct attribute_group *group)
{	
	return sysfs_create_group(&dev->kobj, group);
}

static inline void sw8180_remove_sys(struct device *dev, 
							   struct attribute_group *group)
{
	return sysfs_remove_group(&dev->kobj, group);
}

static int sw8180_probe(struct i2c_client *client)
{	
	const struct i2c_device_id *id = i2c_match_id(sw8180_ids, client);	
	struct attribute_group *group = NULL;
	struct sw8180_cpld *data;
	
	data = devm_kzalloc(&client->dev, sizeof(struct sw8180_cpld), GFP_KERNEL);
	if (!data)
		return -ENOMEM;
	
	mutex_init(&data->lock);

	data->kind   = id->driver_data;

	i2c_set_clientdata(client, data);

	switch (data->kind) {
	case cpld:
		group = &switch_group;
		break;
	case hs_cpld: 
		group = &high_speed_group;
		break;
	case ls_cpld:
		group = &low_speed_group;
		break;
	case sw_psu:
		group = &psu_group;
		break;	
	}
	
	return sw8180_create_sys(&client->dev, group);
}

static int sw8180_remove(struct i2c_client *client)
{
	struct sw8180_cpld *data = i2c_get_clientdata(client);
	struct attribute_group *group = NULL;
	
	switch (data->kind) {
	case cpld:
		group = &switch_group;
		break;
	case hs_cpld: 
		group = &high_speed_group;
		break;
	case ls_cpld:
		group = &low_speed_group;
		break;
	case sw_psu:
		group = &psu_group;
		break;	
	}

	sw8180_remove_sys(&client->dev, group);
	
	return 0;
}

static struct i2c_driver sw8180_driver = {
	.driver = {
		.name = "sw8180-cpld",
	},
	.probe_new = sw8180_probe,	
	.remove = sw8180_remove,
	.id_table = sw8180_ids,
};
module_i2c_driver(sw8180_driver);

MODULE_DESCRIPTION("SW8180 I2C devices");
MODULE_AUTHOR("");
MODULE_LICENSE("GPL");
