
all: lib

lib: pagemap.cpp types.hpp
	g++ --std=c++23 -fPIC -shared -O3 pagemap.cpp -o librss.so

lib_smaps: smaps.cpp types.hpp
	g++ --std=c++23 -fPIC -shared -O3 smaps.cpp -o librss.so

exec_pagemap: pagemap.cpp types.hpp
	g++ --std=c++23 -O3 pagemap.cpp -o pagemap

clean:
	rm -f librss.so pagemap smaps
