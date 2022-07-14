<!--
	空格缩进
		&nbsp; 空格
	标题
		# 一级标题
		### 三级标题
	分割线
		---
	图片
		![图片下面文字](图片地址 "图片标题")
	超链接
		[超链接名](超链接地址 "超链接标题")
	表格
	| 表头 | 表头 | 表头 | 表头 |
	| :--- | ---: | :---: | --- |
	| 左对齐 | 右对齐 | 居中 | 默认 |
	| 左对齐 | 右对齐 | 居中 | 默认 |
-->

### makefile编写
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;编译单个文件: foo.c ==> foo
```Makefile
	obj += foo.o
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;编译多个依赖文件: foo-1 foo-2 ==> foo
```Makefile
	obj += foo.o
	foo-objs := foo-1.o foo-2.o
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;添加下一层目录
```Makefile
	subdir += test
```



