/*
 * WAQ Runtime Library
 *
 * Provides runtime support for WASM programs compiled with waq.
 * Link this with your compiled WASM object files to create executables.
 *
 * Usage:
 *   waq --emit obj program.wat -o program.o
 *   cc -o program program.o waq_runtime.c
 *
 * Or use --emit exe to do this automatically.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>

/* WASM memory (64KB pages) */
#define WASM_PAGE_SIZE 65536
#define WASM_MAX_PAGES 65536

/* Exported memory pointer - accessed by compiled WASM code */
uint8_t *__wasm_memory = NULL;
uint32_t __wasm_memory_size_pages = 0;

/* Integer intrinsics */

int32_t __wasm_i32_clz(int32_t x) {
    if (x == 0) return 32;
    return __builtin_clz((uint32_t)x);
}

int32_t __wasm_i32_ctz(int32_t x) {
    if (x == 0) return 32;
    return __builtin_ctz((uint32_t)x);
}

int32_t __wasm_i32_popcnt(int32_t x) {
    return __builtin_popcount((uint32_t)x);
}

int64_t __wasm_i64_clz(int64_t x) {
    if (x == 0) return 64;
    return __builtin_clzll((uint64_t)x);
}

int64_t __wasm_i64_ctz(int64_t x) {
    if (x == 0) return 64;
    return __builtin_ctzll((uint64_t)x);
}

int64_t __wasm_i64_popcnt(int64_t x) {
    return __builtin_popcountll((uint64_t)x);
}

/* Rotate operations */

int32_t __wasm_i32_rotl(int32_t x, int32_t y) {
    uint32_t ux = (uint32_t)x;
    uint32_t shift = (uint32_t)y & 31;  /* WASM specifies mod 32 */
    if (shift == 0) return x;
    return (int32_t)((ux << shift) | (ux >> (32 - shift)));
}

int32_t __wasm_i32_rotr(int32_t x, int32_t y) {
    uint32_t ux = (uint32_t)x;
    uint32_t shift = (uint32_t)y & 31;  /* WASM specifies mod 32 */
    if (shift == 0) return x;
    return (int32_t)((ux >> shift) | (ux << (32 - shift)));
}

int64_t __wasm_i64_rotl(int64_t x, int64_t y) {
    uint64_t ux = (uint64_t)x;
    uint64_t shift = (uint64_t)y & 63;  /* WASM specifies mod 64 */
    if (shift == 0) return x;
    return (int64_t)((ux << shift) | (ux >> (64 - shift)));
}

int64_t __wasm_i64_rotr(int64_t x, int64_t y) {
    uint64_t ux = (uint64_t)x;
    uint64_t shift = (uint64_t)y & 63;  /* WASM specifies mod 64 */
    if (shift == 0) return x;
    return (int64_t)((ux >> shift) | (ux << (64 - shift)));
}

/* Float intrinsics - f32 */

float __wasm_f32_abs(float x) {
    return fabsf(x);
}

float __wasm_f32_ceil(float x) {
    return ceilf(x);
}

float __wasm_f32_floor(float x) {
    return floorf(x);
}

float __wasm_f32_trunc(float x) {
    return truncf(x);
}

float __wasm_f32_nearest(float x) {
    return nearbyintf(x);
}

float __wasm_f32_sqrt(float x) {
    return sqrtf(x);
}

float __wasm_f32_min(float a, float b) {
    if (isnan(a) || isnan(b)) return NAN;
    return fminf(a, b);
}

float __wasm_f32_max(float a, float b) {
    if (isnan(a) || isnan(b)) return NAN;
    return fmaxf(a, b);
}

float __wasm_f32_copysign(float a, float b) {
    return copysignf(a, b);
}

/* Float intrinsics - f64 */

double __wasm_f64_abs(double x) {
    return fabs(x);
}

double __wasm_f64_ceil(double x) {
    return ceil(x);
}

double __wasm_f64_floor(double x) {
    return floor(x);
}

double __wasm_f64_trunc(double x) {
    return trunc(x);
}

double __wasm_f64_nearest(double x) {
    return nearbyint(x);
}

double __wasm_f64_sqrt(double x) {
    return sqrt(x);
}

double __wasm_f64_min(double a, double b) {
    if (isnan(a) || isnan(b)) return NAN;
    return fmin(a, b);
}

double __wasm_f64_max(double a, double b) {
    if (isnan(a) || isnan(b)) return NAN;
    return fmax(a, b);
}

double __wasm_f64_copysign(double a, double b) {
    return copysign(a, b);
}

/* Trap handlers */

void __wasm_trap_unreachable(void) {
    fprintf(stderr, "wasm trap: unreachable\n");
    abort();
}

void __wasm_trap_div_by_zero(void) {
    fprintf(stderr, "wasm trap: integer divide by zero\n");
    abort();
}

void __wasm_trap_integer_overflow(void) {
    fprintf(stderr, "wasm trap: integer overflow\n");
    abort();
}

void __wasm_trap_invalid_conversion(void) {
    fprintf(stderr, "wasm trap: invalid conversion to integer\n");
    abort();
}

void __wasm_trap_out_of_bounds(void) {
    fprintf(stderr, "wasm trap: out of bounds memory access\n");
    abort();
}

/* Memory operations */

int32_t __wasm_memory_grow(int32_t delta) {
    if (delta < 0) return -1;

    uint32_t old_pages = __wasm_memory_size_pages;
    uint32_t new_pages = old_pages + (uint32_t)delta;

    if (new_pages > WASM_MAX_PAGES) return -1;

    size_t new_size = (size_t)new_pages * WASM_PAGE_SIZE;
    uint8_t *new_memory = realloc(__wasm_memory, new_size);

    if (new_memory == NULL && new_size > 0) return -1;

    /* Zero-initialize new pages */
    if (new_memory != NULL && delta > 0) {
        memset(new_memory + (old_pages * WASM_PAGE_SIZE), 0,
               (size_t)delta * WASM_PAGE_SIZE);
    }

    __wasm_memory = new_memory;
    __wasm_memory_size_pages = new_pages;

    return (int32_t)old_pages;
}

int32_t __wasm_memory_size(void) {
    return (int32_t)__wasm_memory_size_pages;
}

/* Memory base pointer for compiled code */
uint8_t *__wasm_memory_base(void) {
    return __wasm_memory;
}

/* Initialize runtime */
void __wasm_runtime_init(uint32_t initial_pages) {
    if (initial_pages > 0) {
        __wasm_memory_grow((int32_t)initial_pages);
    }
}

/* Cleanup runtime */
void __wasm_runtime_cleanup(void) {
    free(__wasm_memory);
    __wasm_memory = NULL;
    __wasm_memory_size_pages = 0;
}

/* Table support */
#define WASM_MAX_TABLE_SIZE 65536

/* Exported table pointer - accessed by compiled WASM code */
void **__wasm_table = NULL;
uint32_t __wasm_table_size = 0;

int32_t __wasm_table_grow(int32_t delta, void *init_val) {
    if (delta < 0) return -1;

    uint32_t old_size = __wasm_table_size;
    uint32_t new_size = old_size + (uint32_t)delta;

    if (new_size > WASM_MAX_TABLE_SIZE) return -1;

    void **new_table = realloc(__wasm_table, new_size * sizeof(void *));
    if (new_table == NULL && new_size > 0) return -1;

    /* Initialize new entries */
    for (uint32_t i = old_size; i < new_size; i++) {
        new_table[i] = init_val;
    }

    __wasm_table = new_table;
    __wasm_table_size = new_size;

    return (int32_t)old_size;
}

int32_t __wasm_table_size_op(void) {
    return (int32_t)__wasm_table_size;
}

void *__wasm_table_get(int32_t idx) {
    if (idx < 0 || (uint32_t)idx >= __wasm_table_size) {
        __wasm_trap_out_of_bounds();
    }
    return __wasm_table[idx];
}

void __wasm_table_set(int32_t idx, void *val) {
    if (idx < 0 || (uint32_t)idx >= __wasm_table_size) {
        __wasm_trap_out_of_bounds();
    }
    __wasm_table[idx] = val;
}
