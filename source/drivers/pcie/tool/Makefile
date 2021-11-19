
TGT = fpgarw
SRCS = fpgarw.c
CFLAGS = -I$(shell pwd)/../driver/ -O3


$(TGT) : $(SRCS:.c=.o)
	$(CC) $(CFLAGS) $< -o $@

%.o : %.c
	$(CC) $(CFLAGS) $< -c
    
%.d : %.c
	$(CC) -MM $(CFLAGS) $< > $@
sinclude $(SRCS:.c=.d)

.PHONY:clean help

clean:
	@rm -rf $(TGT) *.o *.d
	@echo "clean success"


