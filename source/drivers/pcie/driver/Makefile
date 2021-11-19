
DEBUG = y

ifeq ($(DEBUG),y)
	EXTRA_CFLAGS += -DDEBUG
endif

ifneq ($(KERNELRELEASE),)
	obj-m :=fpga_pci.o
else
	KERNELDIR ?= /lib/modules/$(shell uname -r)/build
	PWD := $(shell pwd)

default:  
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules
 
clean :	 
	$(MAKE) -C $(KERNELDIR) M=$(PWD) clean 
endif
