/*
 * WAQ Runtime Library - Implementation
 *
 * This runtime provides support functions for WASM programs compiled by waq.
 */

#include "wasm_runtime.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <fenv.h>

/* ============== Memory state ============== */

uint8_t* __wasm_memory = NULL;
uint32_t __wasm_memory_size = 0;
static uint32_t memory_pages = 0;

/* ============== Table state ============== */

void** __wasm_table = NULL;
uint32_t __wasm_table_size = 0;

/* ============== Integer intrinsics ============== */

int32_t __wasm_i32_clz(int32_t x) {
    if (x == 0) return 32;
    return __builtin_clz((unsigned int)x);
}

int32_t __wasm_i32_ctz(int32_t x) {
    if (x == 0) return 32;
    return __builtin_ctz((unsigned int)x);
}

int32_t __wasm_i32_popcnt(int32_t x) {
    return __builtin_popcount((unsigned int)x);
}

int32_t __wasm_i32_rotl(int32_t x, int32_t y) {
    uint32_t ux = (uint32_t)x;
    uint32_t shift = (uint32_t)y & 31;
    return (int32_t)((ux << shift) | (ux >> (32 - shift)));
}

int32_t __wasm_i32_rotr(int32_t x, int32_t y) {
    uint32_t ux = (uint32_t)x;
    uint32_t shift = (uint32_t)y & 31;
    return (int32_t)((ux >> shift) | (ux << (32 - shift)));
}

int64_t __wasm_i64_clz(int64_t x) {
    if (x == 0) return 64;
    return __builtin_clzll((unsigned long long)x);
}

int64_t __wasm_i64_ctz(int64_t x) {
    if (x == 0) return 64;
    return __builtin_ctzll((unsigned long long)x);
}

int64_t __wasm_i64_popcnt(int64_t x) {
    return __builtin_popcountll((unsigned long long)x);
}

int64_t __wasm_i64_rotl(int64_t x, int64_t y) {
    uint64_t ux = (uint64_t)x;
    uint64_t shift = (uint64_t)y & 63;
    return (int64_t)((ux << shift) | (ux >> (64 - shift)));
}

int64_t __wasm_i64_rotr(int64_t x, int64_t y) {
    uint64_t ux = (uint64_t)x;
    uint64_t shift = (uint64_t)y & 63;
    return (int64_t)((ux >> shift) | (ux << (64 - shift)));
}

/* ============== Float intrinsics ============== */

float __wasm_f32_abs(float x) { return fabsf(x); }
float __wasm_f32_neg(float x) { return -x; }
float __wasm_f32_ceil(float x) { return ceilf(x); }
float __wasm_f32_floor(float x) { return floorf(x); }
float __wasm_f32_trunc(float x) { return truncf(x); }
float __wasm_f32_nearest(float x) { return nearbyintf(x); }
float __wasm_f32_sqrt(float x) { return sqrtf(x); }

float __wasm_f32_min(float x, float y) {
    if (isnan(x)) return x;
    if (isnan(y)) return y;
    return fminf(x, y);
}

float __wasm_f32_max(float x, float y) {
    if (isnan(x)) return x;
    if (isnan(y)) return y;
    return fmaxf(x, y);
}

float __wasm_f32_copysign(float x, float y) { return copysignf(x, y); }

double __wasm_f64_abs(double x) { return fabs(x); }
double __wasm_f64_neg(double x) { return -x; }
double __wasm_f64_ceil(double x) { return ceil(x); }
double __wasm_f64_floor(double x) { return floor(x); }
double __wasm_f64_trunc(double x) { return trunc(x); }
double __wasm_f64_nearest(double x) { return nearbyint(x); }
double __wasm_f64_sqrt(double x) { return sqrt(x); }

double __wasm_f64_min(double x, double y) {
    if (isnan(x)) return x;
    if (isnan(y)) return y;
    return fmin(x, y);
}

double __wasm_f64_max(double x, double y) {
    if (isnan(x)) return x;
    if (isnan(y)) return y;
    return fmax(x, y);
}

double __wasm_f64_copysign(double x, double y) { return copysign(x, y); }

/* ============== Saturating truncation ============== */

int32_t __wasm_i32_trunc_sat_f32_s(float x) {
    if (isnan(x)) return 0;
    if (x >= (float)INT32_MAX) return INT32_MAX;
    if (x <= (float)INT32_MIN) return INT32_MIN;
    return (int32_t)x;
}

uint32_t __wasm_i32_trunc_sat_f32_u(float x) {
    if (isnan(x) || x <= 0.0f) return 0;
    if (x >= (float)UINT32_MAX) return UINT32_MAX;
    return (uint32_t)x;
}

int32_t __wasm_i32_trunc_sat_f64_s(double x) {
    if (isnan(x)) return 0;
    if (x >= (double)INT32_MAX) return INT32_MAX;
    if (x <= (double)INT32_MIN) return INT32_MIN;
    return (int32_t)x;
}

uint32_t __wasm_i32_trunc_sat_f64_u(double x) {
    if (isnan(x) || x <= 0.0) return 0;
    if (x >= (double)UINT32_MAX) return UINT32_MAX;
    return (uint32_t)x;
}

int64_t __wasm_i64_trunc_sat_f32_s(float x) {
    if (isnan(x)) return 0;
    if (x >= (float)INT64_MAX) return INT64_MAX;
    if (x <= (float)INT64_MIN) return INT64_MIN;
    return (int64_t)x;
}

uint64_t __wasm_i64_trunc_sat_f32_u(float x) {
    if (isnan(x) || x <= 0.0f) return 0;
    if (x >= (float)UINT64_MAX) return UINT64_MAX;
    return (uint64_t)x;
}

int64_t __wasm_i64_trunc_sat_f64_s(double x) {
    if (isnan(x)) return 0;
    if (x >= (double)INT64_MAX) return INT64_MAX;
    if (x <= (double)INT64_MIN) return INT64_MIN;
    return (int64_t)x;
}

uint64_t __wasm_i64_trunc_sat_f64_u(double x) {
    if (isnan(x) || x <= 0.0) return 0;
    if (x >= (double)UINT64_MAX) return UINT64_MAX;
    return (uint64_t)x;
}

/* ============== Memory operations ============== */

int32_t __wasm_memory_size_pages(void) {
    return (int32_t)memory_pages;
}

int32_t __wasm_memory_grow(int32_t pages) {
    if (pages < 0) return -1;

    uint32_t old_pages = memory_pages;
    uint32_t new_pages = old_pages + (uint32_t)pages;

    if (new_pages > WASM_MAX_PAGES) return -1;

    size_t new_size = (size_t)new_pages * WASM_PAGE_SIZE;
    uint8_t* new_mem = realloc(__wasm_memory, new_size);
    if (!new_mem) return -1;

    /* Zero new pages */
    memset(new_mem + (old_pages * WASM_PAGE_SIZE), 0,
           (size_t)pages * WASM_PAGE_SIZE);

    __wasm_memory = new_mem;
    __wasm_memory_size = (uint32_t)new_size;
    memory_pages = new_pages;

    return (int32_t)old_pages;
}

void __wasm_memory_init_seg(int32_t seg, int32_t dest, int32_t src, int32_t len) {
    /* TODO: Implement data segment handling */
    (void)seg; (void)dest; (void)src; (void)len;
}

void __wasm_data_drop(int32_t seg) {
    /* TODO: Implement data segment dropping */
    (void)seg;
}

void __wasm_memory_copy(int32_t dest, int32_t src, int32_t len) {
    if (len <= 0) return;
    if ((uint32_t)(dest + len) > __wasm_memory_size ||
        (uint32_t)(src + len) > __wasm_memory_size) {
        __wasm_trap_out_of_bounds();
    }
    memmove(__wasm_memory + dest, __wasm_memory + src, (size_t)len);
}

void __wasm_memory_fill(int32_t dest, int32_t val, int32_t len) {
    if (len <= 0) return;
    if ((uint32_t)(dest + len) > __wasm_memory_size) {
        __wasm_trap_out_of_bounds();
    }
    memset(__wasm_memory + dest, val & 0xFF, (size_t)len);
}

/* ============== Table operations ============== */

void* __wasm_table_get(int32_t idx) {
    if (idx < 0 || (uint32_t)idx >= __wasm_table_size) {
        __wasm_trap_out_of_bounds();
    }
    return __wasm_table[idx];
}

void __wasm_table_set(int32_t idx, void* val) {
    if (idx < 0 || (uint32_t)idx >= __wasm_table_size) {
        __wasm_trap_out_of_bounds();
    }
    __wasm_table[idx] = val;
}

void __wasm_table_init(int32_t table, int32_t elem, int32_t dest, int32_t src, int32_t len) {
    /* TODO: Implement element segment initialization */
    (void)table; (void)elem; (void)dest; (void)src; (void)len;
}

void __wasm_elem_drop(int32_t elem) {
    /* TODO: Implement element segment dropping */
    (void)elem;
}

void __wasm_table_copy(int32_t dest_table, int32_t src_table, int32_t dest, int32_t src, int32_t len) {
    /* TODO: Implement table copy */
    (void)dest_table; (void)src_table; (void)dest; (void)src; (void)len;
}

int32_t __wasm_table_grow(int32_t table, void* val, int32_t delta) {
    /* TODO: Implement table grow */
    (void)table; (void)val; (void)delta;
    return -1;
}

int32_t __wasm_table_size_op(int32_t table) {
    (void)table;
    return (int32_t)__wasm_table_size;
}

void __wasm_table_fill(int32_t table, int32_t dest, void* val, int32_t len) {
    /* TODO: Implement table fill */
    (void)table; (void)dest; (void)val; (void)len;
}

/* ============== Traps ============== */

void __wasm_trap_unreachable(void) {
    fprintf(stderr, "wasm trap: unreachable\n");
    exit(1);
}

void __wasm_trap_div_by_zero(void) {
    fprintf(stderr, "wasm trap: integer divide by zero\n");
    exit(1);
}

void __wasm_trap_integer_overflow(void) {
    fprintf(stderr, "wasm trap: integer overflow\n");
    exit(1);
}

void __wasm_trap_invalid_conversion(void) {
    fprintf(stderr, "wasm trap: invalid conversion to integer\n");
    exit(1);
}

void __wasm_trap_out_of_bounds(void) {
    fprintf(stderr, "wasm trap: out of bounds memory access\n");
    exit(1);
}

void __wasm_trap_null_reference(void) {
    fprintf(stderr, "wasm trap: null reference\n");
    exit(1);
}

/* ============== Exception handling ============== */

/* Simple exception handler stack */
#define MAX_EXCEPTION_HANDLERS 256
static void* exception_handlers[MAX_EXCEPTION_HANDLERS];
static int exception_handler_count = 0;
static void* current_exception = NULL;

void __wasm_push_exception_handler(void* label) {
    if (exception_handler_count >= MAX_EXCEPTION_HANDLERS) {
        fprintf(stderr, "wasm trap: exception handler stack overflow\n");
        exit(1);
    }
    exception_handlers[exception_handler_count++] = label;
}

void __wasm_pop_exception_handler(void) {
    if (exception_handler_count > 0) {
        exception_handler_count--;
    }
}

void __wasm_throw(int32_t tag, void* values) {
    (void)tag;
    current_exception = values;
    if (exception_handler_count > 0) {
        /* In a real implementation, we'd longjmp to the handler */
        fprintf(stderr, "wasm trap: unhandled exception (tag=%d)\n", tag);
        exit(1);
    }
    fprintf(stderr, "wasm trap: unhandled exception (tag=%d)\n", tag);
    exit(1);
}

void __wasm_rethrow(void) {
    fprintf(stderr, "wasm trap: rethrow with no exception\n");
    exit(1);
}

void* __wasm_get_exception(void) {
    return current_exception;
}

/* ============== GC operations ============== */

/* Simple header for GC objects */
typedef struct {
    int32_t type_idx;
    int32_t length;  /* For arrays */
} GCHeader;

void* __wasm_struct_new(int32_t type_idx, int32_t num_fields) {
    size_t size = sizeof(GCHeader) + (size_t)num_fields * sizeof(int64_t);
    GCHeader* obj = calloc(1, size);
    if (!obj) {
        fprintf(stderr, "wasm trap: out of memory\n");
        exit(1);
    }
    obj->type_idx = type_idx;
    obj->length = num_fields;
    return (void*)(obj + 1);  /* Return pointer after header */
}

void* __wasm_struct_new_default(int32_t type_idx, int32_t num_fields) {
    return __wasm_struct_new(type_idx, num_fields);  /* Already zeroed by calloc */
}

void* __wasm_array_new(int32_t type_idx, int32_t init_value, int32_t length) {
    size_t size = sizeof(GCHeader) + (size_t)length * sizeof(int64_t);
    GCHeader* obj = malloc(size);
    if (!obj) {
        fprintf(stderr, "wasm trap: out of memory\n");
        exit(1);
    }
    obj->type_idx = type_idx;
    obj->length = length;

    /* Initialize all elements */
    int64_t* data = (int64_t*)(obj + 1);
    for (int32_t i = 0; i < length; i++) {
        data[i] = init_value;
    }
    return (void*)data;
}

void* __wasm_array_new_default(int32_t type_idx, int32_t length) {
    size_t size = sizeof(GCHeader) + (size_t)length * sizeof(int64_t);
    GCHeader* obj = calloc(1, size);
    if (!obj) {
        fprintf(stderr, "wasm trap: out of memory\n");
        exit(1);
    }
    obj->type_idx = type_idx;
    obj->length = length;
    return (void*)(obj + 1);
}

/* i31ref: tagged pointer with low bit set */
int64_t __wasm_ref_i31(int32_t value) {
    /* Use low bit as tag, store 31-bit signed value */
    return ((int64_t)(value & 0x7FFFFFFF) << 1) | 1;
}

int32_t __wasm_i31_get_s(int64_t ref) {
    int32_t val = (int32_t)((ref >> 1) & 0x7FFFFFFF);
    /* Sign extend from 31 bits */
    if (val & 0x40000000) {
        val |= 0x80000000;
    }
    return val;
}

int32_t __wasm_i31_get_u(int64_t ref) {
    return (int32_t)((ref >> 1) & 0x7FFFFFFF);
}

int32_t __wasm_ref_test(void* ref, int32_t type_idx) {
    if (!ref) return 0;
    GCHeader* header = ((GCHeader*)ref) - 1;
    return header->type_idx == type_idx;
}

int32_t __wasm_ref_test_null(void* ref, int32_t type_idx) {
    if (!ref) return 1;
    GCHeader* header = ((GCHeader*)ref) - 1;
    return header->type_idx == type_idx;
}

void* __wasm_ref_cast(void* ref, int32_t type_idx) {
    if (!ref) {
        __wasm_trap_null_reference();
    }
    GCHeader* header = ((GCHeader*)ref) - 1;
    if (header->type_idx != type_idx) {
        fprintf(stderr, "wasm trap: ref.cast failed\n");
        exit(1);
    }
    return ref;
}

void* __wasm_ref_cast_null(void* ref, int32_t type_idx) {
    if (!ref) return NULL;
    GCHeader* header = ((GCHeader*)ref) - 1;
    if (header->type_idx != type_idx) {
        fprintf(stderr, "wasm trap: ref.cast failed\n");
        exit(1);
    }
    return ref;
}

/* ============== Initialization ============== */

void __wasm_init(int32_t initial_pages) {
    if (initial_pages <= 0) initial_pages = WASM_INITIAL_PAGES;

    memory_pages = 0;
    __wasm_memory = NULL;
    __wasm_memory_size = 0;

    if (__wasm_memory_grow(initial_pages) < 0) {
        fprintf(stderr, "wasm: failed to initialize memory\n");
        exit(1);
    }

    /* Initialize table (default size) */
    __wasm_table_size = 64;
    __wasm_table = calloc(__wasm_table_size, sizeof(void*));
}

void __wasm_fini(void) {
    free(__wasm_memory);
    __wasm_memory = NULL;
    __wasm_memory_size = 0;
    memory_pages = 0;

    free(__wasm_table);
    __wasm_table = NULL;
    __wasm_table_size = 0;
}
