# /bin/bash

# valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all --suppressions=./valgrind-python.supp python3 ./testcreationdestruction.py --with-valgrind
valgrind --tool=memcheck --suppressions=./valgrind-python.supp python3 ./testcreationdestruction.py --with-valgrind