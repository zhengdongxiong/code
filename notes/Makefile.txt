
makefile 运行依赖于时间，目标文件比依赖列表新 则不运行
makefile 中每一行都是一个进程
make -n 只显示命令不执行
执行步骤
	1.读入所有Makefile
	2.读入被include的其他Makefile
	3.初始化变量
	4.推到规则,分析规则
	5.所有目标文件创建依赖关系
	6.根据依赖关系,决定哪些目标需要重新生成
	7.生成
基本规则：
目标：所依赖的列表
	（tab键）命令列表
	
A: B C D
	gcc ...

B:b1
	@（不打印此条命令）gcc ...

第一条规则中的“目标”会成为终极目标


变量

赋值：
$ --> 去取变量的值
A = 10
B = $A --> B = 10 --> = 延迟赋值 等待A有值时B才有
C := $A --> := 立即赋值 若A没有值则为空
D ?= $A --> ?= 条件赋值 如果D之前有值就不赋值给D
E += $A --> += 追加赋值 原本E有值 在拼接上A  A值拼接在E值上

foo := a.o b.o c.o
bar := $(foo:%.o=%.c)
	变量替换 bar里面所有.o替换成a.c b.c c.c 只是名字的替换
	
CUR_DIR=$(shell pwd)
	使用shell命令

%.o:%.c
	表示把任意一个.c文件编译成.o
	%匹配任何非空字符串, makefile中的模式规则包含%
	依赖和目标中含有模式规则, 则将依赖中的%传递给目标
	一个模式规则包含/, 先去除/, 在匹配
		src/eat 模式e%t的依赖 则%为src/a
		目标模式c%r 则为src/car
a%.o
	以a开头的所有.o文件
	
$@ 表示规则中的目标名
$< 表示规则中的第一个依赖名字, 如果依赖目标是模式定义, 则符合模式一个个取出
$^ 所有依赖文件, 去除重复依赖
$? 所有比目标新的依赖 
$$ 表示$符号/表示shell中变量
$* 表示模式规则中的所有%匹配的部分, 文件名带有一个可识别的后缀, $*表示除后缀以外的部分

.PHONY: clean (避免和同名文件冲突)
	.PHONY为伪目标 仅仅是为了执行其所在的规则下的命令，不应该让make来判断是否存在/生成(减少make判断，否则需要make自行判断是否执行或生成
		防止文件下有clean文件夹且最新，则不执行clean)

条件语法
	ifeq ($1,$2) #如果$1 == $2执行
	...
	endif
	ifeq ($1,$2) #如果$1 == $2执行, 否则执行
	...
	else
	...
	endif
	ifdef/ifndef <cmd> #如果定义/无定义cmd执行 
	...
	endif

函数调用
	$(<fun> <arguments>)
	
	$(subst <from>,<to>,<test>) 
		字符串替换
		$(subst ee,EE,feet on the street) --> fEEt on the strEEt
	$(patsubst <pattern>,<replacement>,<test>) 
		模式字符串替换
		单词以空格, tab, 回车, 换行分割, 是否符合<pattern>, 如果匹配替换
		如果pattern中包括通配符%, 那么replacement中的%即为pattern中
		$(patsubst %.c,%.o,x.c.c bar.c) --> x.o c.o bar.o
	$(strip <string>) 
		去掉string字符串中开头和结尾空字符
		$(strip abc ) --> "abc"
	$(findstring <find>,<in>) 
		从<in>中找<find>字符串, 找到返回<find>
		$(findstring a,a b c) --> a
		$(findstring a,b c) --> 返回空
	$(filter <pattern...>,<text>) 
		从<text>中过滤出<pattern>
		$(filter %.c %.s,foo.c bar.c baz.s ugh.h) --> foo.c bar.c baz.s
	$(filter-out <pattern...>,<text>) 
		反过滤
	$(sort <list>) 
		给<list>排序(升序)同时去掉<list>中相同
	$(word <n>,<text>) 
		从<text>中取第<n>个单词(从一开始), n比单词数大, 则为空
		$(word 2, foo bar baz) --> bar
	$(wordlist <s>,<e>,<text>) 
		取单词串, 从s到e的单词串, s比text大返回空, e比text大从s到结束
		$(wordlist 2, 3, foo bar baz) --> bar baz
	$(words <text>)
		统计单词个数
	$(firstword <text>)
		取首个单词
	$(dir <names...>)
		取目录函数, 最后一个/
		$(dir src/foo.c hacks) --> src/ 和 ./
	$(notdir <names...>)
		取非目录部分
		$(notdir src/foo.c hacks) --> foo.c hacks
	$(suffix <names...>)
		取后缀, 若无后缀则返回空
		$(suffix src/foo.c src-1.0/bar.c hacks) --> .c .c
	$(basename <names...>)
		取前缀
		$(basename src/foo.c src-1.0/bar.c hacks) --> src/foo src-1.0/bar hacks
	$(addsuffix <suffix>,<names...>)
		加后缀
		$(addsuffix .c,foo bar) --> foo.c bar.c
	$(addprefix <prefix>,<names...>)
		加前缀
		$(addprefix src/,foo bar) --> src/foo src/bar
	$(join <list1>,<list2>)
		list2中的单词依次加入到list1中
		$(join aabb cc45,11) --> aabb11 cc45
	$(foreach <var>,<list>,<text>)
		循环
		从<list>中取出, 放入<var>中, 执行<test>
		$(foreach n,a b c,$(n).o) --> a.o b.o c.o
	$(if <condition>,<then-part>,<else-part>)
		两个参数不包含else, <condition>为非空执行<then-part>, <then-part>结果
	$(call <expression>,<parm1>,<parm...>)
		创建新参数化函数, <expression>中的$(1)..$(n)依次被<parm..>替代
		reverse = $(1) $(2)
		$(call reverse,a,b) --> a b
	$(origin <var>)
		返回变量定义
		$(origin CC) --> default
	$(shell <cmd>)
		执行shell命令
	$(error <text>) / $(warning <text>)
		退出/警告makefile并显示<text>

隐晦规则(make自动推导执行, 不需要写)
	<n>.o的目标依赖为<n>.c, 并生成命令$(CC) -c $(CPPFLAGS) $(CFLAGS)
	<n>目标依赖<n>.o, 并生成$(CC) $(LDFLAGS) <n>.o $(LOADLIBES) $(LDLIBES)
		x : y.o z.o 将自动执行以下命令, 若目录无x.c报错(隐晦规则第2, 1条)
			cc -c x.c -o x.o
			cc -c y.c -o y.o
			cc -c z.c -o z.o
			cc x.o y.o z.o -o x
			rm -f *.o
	预定义变量
		AR, AS, CC, CXX, RM, ARFLAGS, ASFLAGS, CFLAGS, CPPFLGS(预编译选项), CXXFLAGS
-------------------------------------------------------------------------------------------------------

开始make时候 先加载include的东西

由于makefile中没有头文件依赖，若头文件更新，重新make时不会运行。
因此需要依赖头文件，使得头文件更新时，make可以运行

下面规则说明，头文件更新，使得所有依赖于它的文件被重新生成(以免更新头文件，不重新生成目标)
%.d : %.c
	gcc -MM $^($<) > $@
	
-MM自动寻源文件中包含的头文件，并生成一个依赖关系 -M会包含标准文件
.d文件包含对应.c文件所需要的依赖

将上面规则中的结果包含进当前文件中
include --> 直接把内容粘贴过来

include $(srcs:%.c=%.d)
-inculde $(srcs:%.c=%.d)
sinclude $(srcs:%.c=%.d)  找不到不报错
----------------------------------------------------------------------
define类似函数用法
$(call 函数名,参数) 将参数传入函数名替换工作 带有$全部被替换.视位置解析为makefile/shell命令
$(eval 内容) 执行命令 内容将作为makefile的一部分而被make解析和执行。


pointer := pointed_value

define foo 
	var := 123
	arg := $1
	$$($1) := ooooo
endef 

$(info $(call foo,pointer))
#$(eval $(call foo,pointer))

target:
    @echo -----------------------------
	@echo var: $(var), arg: $(arg)
	@echo pointer: $(pointer), pointed_value: $(pointed_value)
	@echo done.
	@echo -----------------------------

	$(foo) #调用foo,解析为shell命令



----------------------------------------------------------------------

#主Makefile:作用是制定规则来说明如何在当前目录下生产终极目标文件
# Makefile----------------------------
#	|----Makefile(主)
#	|----head
#	|		|----head.h
#	|		
#	|----main
#	|		|----main.c
#	|
#	|----tst
#	|		|----tst.c
#	|		|----Makefile(子)
#	|		|----foo
#	|		|		|---foo.c


TGT = a.out
#指定子目录
SUB_DIR = main tst

#当前所在目录
TOP_DIR = $(shell pwd)

SUB_TGT = built.o

#头文件所在目录
HEAD_DIR = $(TOP_DIR)/head

#CROSS_COMPILER = arm-linux-
CC = $(CROSS_COMPILER)gcc

#编译选项
CFLAGS = -I$(HEAD_DIR) -Wall
#指定连接器
LD = ld
#指定链接选项
LDFLAGS = 

#作为全局给子makefile
export SUB_TGT HEAD_DIR CC CFLAGS LD LDFLAGS

$(TGT) : $(SUB_DIR)
	$(CC) $(CFLAGS) $(^:=/$(SUB_TGT))
	
	
.PHONY:clean $(SUB_DIR)

#用来告诉make需要进入子目录make
#-C让make进入后面的指定目录
$(SUB_DIR):
	make -C $@
	
clean:
	rm -vf $(TGT)
	for dir in $(SUB_DIR);\
	do \
	#shell中将$(SUB_DIR)存放在dir中 读取为$dir 由于在make中需要$$代表$
		make -C $$dir clean;\
	done
	
----------------------------------------------------
#子makefile 告诉make如何生成当前目录下的子目标

SRCS = tst.c
SUB_DIR = foo

#$ld 链接两个 .o 变成$@
$(SUB_TGT):$(SRCS:.c=.o) $(SUB_DIR)
	$(LD) $(SRCS:.c=.o) $(SUB_DIR:=/$(SUB_TGT)) -r -o $@
	
%.o : %.c
	$(CC) $(CFLAGS) $< -c
	
%.d : %.c
	$(CC) -MM $(CFLAGS) $< > $@
sinclude $(SRCS:.c=.d)
	

.PHONY:clean $(SUB_DIR)

#不加伪目标 若有foo为最新 不执行此规则 无法进入foo执行make命令
#进入foo文件
$(SUB_DIR):
	make -C $(SUB_DIR)

clean:
	rm -vf $(SUB_TGT) $(SRCS:.c=.d) $(SRCS:.c=.o)
	#用shell中for函数
	for dir in $(SUB_TGT); \
	do\
		make -C $$dir clean; \
	done
	
	

