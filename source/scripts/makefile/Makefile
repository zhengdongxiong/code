


PHONY := all
all :


MAKEFLAGS += --no-print-directory
MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += --no-builtin-variables

# Project name and Library name and Compile opts
# ---------------------------------------------------------------------------
libname   := pa8910
version   := 0.0.1
lib-flags :=
lib-libs  :=

export libname version lib-flags lib-libs


# All subdir
# ---------------------------------------------------------------------------
lib_dir   := lib
tools_dir := tools


# Define Global Compiler and Compile opts
# ---------------------------------------------------------------------------
CC       := $(CROSS_COMPILE)gcc
LD       := $(CROSS_COMPILE)ld
AR       := $(CROSS_COMPILE)ar
CPPFLAGS +=
CFLAGS   += -fPIC
LDFLAGS  += -L $(lib_dir)/
LIBS     += -l$(libname)

export CC LD AR CPPFLAGS CFLAGS LDFLAGS LIBS 

# Include Makefile libs
# ---------------------------------------------------------------------------
include scripts/Makefile.lib


# Make target
# ---------------------------------------------------------------------------
subdir    := $(lib_dir) $(tools_dir)
build_dir := $(subdir)
clean_dir := $(addprefix _clean_, $(subdir))




all : $(build_dir)

clean : $(clean_dir)

$(build_dir) :
	@$(MAKE) $(build)=$@
$(clean_dir) :
	@$(MAKE) $(clean)=$(patsubst _clean_%,%,$@)

install :
	$(call cmd,make,install)

FORCE :

PHONY += clean help FORCE $(build_dir) $(clean_dir)

.PHONY : $(PHONY)






