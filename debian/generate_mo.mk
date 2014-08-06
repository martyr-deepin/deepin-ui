# generate locale file 

gen_locale_mo:
	if [ -d dtk/tools ];then cd dtk/tools && python generate_mo.py; fi
