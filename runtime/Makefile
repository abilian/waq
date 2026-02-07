# WAQ Runtime Makefile

CC = clang
CFLAGS = -O2 -Wall -Wextra -std=c11

# Object file
RUNTIME_OBJ = wasm_runtime.o

# Build the runtime object file
$(RUNTIME_OBJ): wasm_runtime.c wasm_runtime.h
	$(CC) $(CFLAGS) -c wasm_runtime.c -o $(RUNTIME_OBJ)

# Static library (alternative)
libwasm_runtime.a: $(RUNTIME_OBJ)
	ar rcs $@ $^

.PHONY: clean
clean:
	rm -f $(RUNTIME_OBJ) libwasm_runtime.a

.PHONY: all
all: $(RUNTIME_OBJ)
