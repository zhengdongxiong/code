
PHONY := all
all :

# Global Makefile flags
# ---------------------------------------------------------------------------
Q         := @
MAKEFLAGS += --no-print-directory
MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += --no-builtin-variables

export Q

# Project name and Library name and Compile opts
# ---------------------------------------------------------------------------
libname   := pa8910
version   := 0.0.1
lib-flags :=
lib-libs  :=

export libname version lib-flags lib-libs


# All subdir
# ---------------------------------------------------------------------------
hdr_dir   := include
lib_dir   := lib
tools_dir := tools
inst_path := install

export hdr_dir lib_dir tools_dir inst_path

# Define Global Compiler and Compile opts
# ---------------------------------------------------------------------------
CC       := $(CROSS_COMPILE)gcc
LD       := $(CROSS_COMPILE)ld
AR       := $(CROSS_COMPILE)ar
CPPFLAGS += -I $(hdr_dir)/
CFLAGS   += -fPIC
LDFLAGS  += -L $(lib_dir)/
LIBS     += -l$(libname)

export CC LD AR CPPFLAGS CFLAGS LDFLAGS LIBS

# Include Makefile libs
# ---------------------------------------------------------------------------
include scripts/Makefile.lib


# Make target
# ---------------------------------------------------------------------------
build_dir  := $(addprefix _build_, $(lib_dir) $(tools_dir))
clean_dir  := $(addprefix _clean_, $(lib_dir) $(tools_dir))
hdr_inst   := $(addprefix _hdrinst_, $(hdr_dir))
lib_inst   := $(addprefix _libinst_, $(lib_dir))
bin_inst   := $(addprefix _bininst_, $(tools_dir))
uninst_dir := $(addprefix _uninst_, $(inst_path))


all : $(build_dir)

clean : $(clean_dir)

install : $(hdr_inst) $(lib_inst) $(bin_inst)

uninstall : $(uninst_dir)

$(build_dir) :
	$(Q)$(MAKE) $(build)=$(patsubst _build_%,%,$@)

$(clean_dir) :
	$(Q)$(MAKE) $(clean)=$(patsubst _clean_%,%,$@)

$(hdr_inst) :
	$(Q)$(MAKE) $(hdrinst)=$(patsubst _hdrinst_%,%,$@)

$(lib_inst) :
	$(Q)$(MAKE) $(libinst)=$(patsubst _libinst_%,%,$@)

$(bin_inst) :
	$(Q)$(MAKE) $(bininst)=$(patsubst _bininst_%,%,$@)

$(uninst_dir) :
	$(Q)$(MAKE) $(uninst)=$(patsubst _uninst_%,%,$@)


FORCE :


PHONY += clean install uninstall FORCE
PHONY += $(build_dir) $(clean_dir) $(hdr_inst) $(lib_inst) $(bin_inst) $(uninst_dir)

.PHONY : $(PHONY)
