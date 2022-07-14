#include <stdio.h>
#include <hello.h>


int main (int argc, char *argv[])
{
	printf("aaaa\n");
	hello513();
	hello794();
#ifdef __PA8910__
	printf("define success\n");
#endif
	

	return 0;
}
