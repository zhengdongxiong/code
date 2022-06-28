#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <getopt.h>
#include <pthread.h>
#include <errno.h>
#include <libgen.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <stdint.h>

#include "fpga_common.h"

#define FPGA_BAR_VALID 		1
#define FPGA_ARRD_VALID		2
#define FPGA_VALUE_VALID	4
#define FPGA_READ_VALID		8
#define FPGA_WRITE_VALID	16

#define FPGA_DEV "/dev/fpga-pa8910"

static int show_usage(const char *name)
{
    printf("Usage: %s -b pcie_bar -a addr -r(read)\n", name);
	printf("                   -b pcie_bar -a addr -w(write) -v value\n");

    return 0;
}

int fpga_pci_read(uint8_t bar, uint32_t offset)
{
	struct fpga_rw fpga_read;
	fpga_read.bar = bar;
	fpga_read.offset = offset;
	int fd = 0;
	int rc;
	
	fd = open(FPGA_DEV, O_RDWR);
	if (fd < 0) {
		printf("pci read open fpga error\n");
		return -1;
	}

	rc = ioctl(fd, FPGA_IOCX_READ, &fpga_read);
	if(rc < 0)
		printf("pci read ioctl fpga error\n");
	else
		printf("0x%x\n",fpga_read.value);

	close(fd);

	return rc;
	
}

int fpga_pci_write(uint8_t bar, uint32_t offset, uint16_t value)
{
	struct fpga_rw fpga_write;
	fpga_write.bar = bar;
	fpga_write.offset = offset;
	fpga_write.value = value;
	int fd = 0;
	int rc;
	
	fd = open(FPGA_DEV, O_RDWR);
	if (fd < 0) {
		printf("pci write open fpga error\n");
		return -1;
	}

	rc = ioctl(fd, FPGA_IOCX_WRITE, &fpga_write);
	if (rc < 0)
		printf("pci write ioctl fpga error\n");

	close(fd);

	return rc;
	
}


int main(int argc, char *argv[])
{
	char c;
	int opt_flag = 0;
	uint8_t fpga_bar;
	uint32_t fpga_offset;
	uint16_t fpga_value;
	
	while ( (( c = getopt( argc, argv, "b:a:v:rw" ) ) > 0)&&(c != 255) ) 
	{
		switch ( c ) 
		{
			case 'b':
				opt_flag |= FPGA_BAR_VALID;
				fpga_bar = strtoul(optarg, 0, 0);
				break;
			case 'a':
				opt_flag |= FPGA_ARRD_VALID;
				fpga_offset = strtoul(optarg, 0, 0);
				/* FPGA access offset
				 * user: 0x20
				 * fpga: 0x08(0x20 >> 2)
				 * fpgarw set (offset <<= 2), keep the reg offset same
				 */
				fpga_offset <<= 2; 
				break;
			case 'v':
			    opt_flag |= FPGA_VALUE_VALID;
				fpga_value = strtoul(optarg, 0, 0);
			   break;
			case 'r':
			   opt_flag |= FPGA_READ_VALID;
			   break;
			case 'w':
			   opt_flag |= FPGA_WRITE_VALID;
			   break;
			default:
			   printf("Invalid Args\n");
			   show_usage(argv[0]);
			       return -1;
		}
	}

	if (!(opt_flag & FPGA_BAR_VALID) || !(opt_flag & FPGA_ARRD_VALID) \
		|| ((!(opt_flag & FPGA_WRITE_VALID) || !(opt_flag & FPGA_VALUE_VALID)) \
		&& !(opt_flag & FPGA_READ_VALID))) {
		
        printf( "Invalid Args!\n");
        show_usage(argv[0]);
        return -1;
	}

	if ((opt_flag & FPGA_READ_VALID)) {
        fpga_pci_read(fpga_bar, fpga_offset);
    }else if (opt_flag & FPGA_WRITE_VALID) {
        fpga_pci_write(fpga_bar, fpga_offset, fpga_value);
    }

	return 0;
}
