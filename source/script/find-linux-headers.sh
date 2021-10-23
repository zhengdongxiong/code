#!/bin/sh

test -f .config && echo ".config"
test -f Module.symvers && echo "Module.symvers"

find . \( -path "./include" -o -path "./tools" -o -path "./scripts" \) -prune \
	   -o -name "*.h"         -print \
	   -o -name "Makefile*"   -print \
	   -o -name "Kbuild*"     -print \
	   -o -name "Kconfig*"    -print \
       -o -name "module.lds*" -print

test -d include && find include -type f -print
test -d tools   && find tools   -type f -a ! -name "*.o*" -a ! -name "*.cmd" -print
test -d scripts && find scripts -type f -a ! -name "*.o*" -a ! -name "*.cmd" -print

