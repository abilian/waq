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

static uint8_t *wasm_memory = NULL;
static uint32_t wasm_memory_pages = 0;

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

    uint32_t old_pages = wasm_memory_pages;
    uint32_t new_pages = old_pages + (uint32_t)delta;

    if (new_pages > WASM_MAX_PAGES) return -1;

    size_t new_size = (size_t)new_pages * WASM_PAGE_SIZE;
    uint8_t *new_memory = realloc(wasm_memory, new_size);

    if (new_memory == NULL && new_size > 0) return -1;

    /* Zero-initialize new pages */
    if (new_memory != NULL && delta > 0) {
        memset(new_memory + (old_pages * WASM_PAGE_SIZE), 0,
               (size_t)delta * WASM_PAGE_SIZE);
    }

    wasm_memory = new_memory;
    wasm_memory_pages = new_pages;

    return (int32_t)old_pages;
}

int32_t __wasm_memory_size(void) {
    return (int32_t)wasm_memory_pages;
}

/* Memory base pointer for compiled code */
uint8_t *__wasm_memory_base(void) {
    return wasm_memory;
}

/* Initialize runtime */
void __wasm_runtime_init(uint32_t initial_pages) {
    if (initial_pages > 0) {
        __wasm_memory_grow((int32_t)initial_pages);
    }
}

/* Cleanup runtime */
void __wasm_runtime_cleanup(void) {
    free(wasm_memory);
    wasm_memory = NULL;
    wasm_memory_pages = 0;
}
