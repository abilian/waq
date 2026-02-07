/*
 * WAQ Runtime Library - Header
 *
 * This runtime provides support functions for WASM programs compiled by waq.
 */

#ifndef WASM_RUNTIME_H
#define WASM_RUNTIME_H

#include <stdint.h>
#include <stddef.h>

/* Memory configuration */
#define WASM_PAGE_SIZE 65536
#define WASM_MAX_PAGES 65536  /* 4GB max */

/* Initial memory (can be overridden) */
#ifndef WASM_INITIAL_PAGES
#define WASM_INITIAL_PAGES 1
#endif

/* Memory exports */
extern uint8_t* __wasm_memory;
extern uint32_t __wasm_memory_size;  /* in bytes */

/* Table exports */
extern void** __wasm_table;
extern uint32_t __wasm_table_size;

/* ============== Integer intrinsics ============== */

int32_t __wasm_i32_clz(int32_t x);
int32_t __wasm_i32_ctz(int32_t x);
int32_t __wasm_i32_popcnt(int32_t x);
int32_t __wasm_i32_rotl(int32_t x, int32_t y);
int32_t __wasm_i32_rotr(int32_t x, int32_t y);

int64_t __wasm_i64_clz(int64_t x);
int64_t __wasm_i64_ctz(int64_t x);
int64_t __wasm_i64_popcnt(int64_t x);
int64_t __wasm_i64_rotl(int64_t x, int64_t y);
int64_t __wasm_i64_rotr(int64_t x, int64_t y);

/* ============== Float intrinsics ============== */

float __wasm_f32_abs(float x);
float __wasm_f32_neg(float x);
float __wasm_f32_ceil(float x);
float __wasm_f32_floor(float x);
float __wasm_f32_trunc(float x);
float __wasm_f32_nearest(float x);
float __wasm_f32_sqrt(float x);
float __wasm_f32_min(float x, float y);
float __wasm_f32_max(float x, float y);
float __wasm_f32_copysign(float x, float y);

double __wasm_f64_abs(double x);
double __wasm_f64_neg(double x);
double __wasm_f64_ceil(double x);
double __wasm_f64_floor(double x);
double __wasm_f64_trunc(double x);
double __wasm_f64_nearest(double x);
double __wasm_f64_sqrt(double x);
double __wasm_f64_min(double x, double y);
double __wasm_f64_max(double x, double y);
double __wasm_f64_copysign(double x, double y);

/* ============== Saturating truncation ============== */

int32_t __wasm_i32_trunc_sat_f32_s(float x);
uint32_t __wasm_i32_trunc_sat_f32_u(float x);
int32_t __wasm_i32_trunc_sat_f64_s(double x);
uint32_t __wasm_i32_trunc_sat_f64_u(double x);
int64_t __wasm_i64_trunc_sat_f32_s(float x);
uint64_t __wasm_i64_trunc_sat_f32_u(float x);
int64_t __wasm_i64_trunc_sat_f64_s(double x);
uint64_t __wasm_i64_trunc_sat_f64_u(double x);

/* ============== Memory operations ============== */

int32_t __wasm_memory_size_pages(void);
int32_t __wasm_memory_grow(int32_t pages);
void __wasm_memory_init_seg(int32_t seg, int32_t dest, int32_t src, int32_t len);
void __wasm_data_drop(int32_t seg);
void __wasm_memory_copy(int32_t dest, int32_t src, int32_t len);
void __wasm_memory_fill(int32_t dest, int32_t val, int32_t len);

/* ============== Table operations ============== */

void* __wasm_table_get(int32_t idx);
void __wasm_table_set(int32_t idx, void* val);
void __wasm_table_init(int32_t table, int32_t elem, int32_t dest, int32_t src, int32_t len);
void __wasm_elem_drop(int32_t elem);
void __wasm_table_copy(int32_t dest_table, int32_t src_table, int32_t dest, int32_t src, int32_t len);
int32_t __wasm_table_grow(int32_t table, void* val, int32_t delta);
int32_t __wasm_table_size_op(int32_t table);
void __wasm_table_fill(int32_t table, int32_t dest, void* val, int32_t len);

/* ============== Traps ============== */

void __wasm_trap_unreachable(void) __attribute__((noreturn));
void __wasm_trap_div_by_zero(void) __attribute__((noreturn));
void __wasm_trap_integer_overflow(void) __attribute__((noreturn));
void __wasm_trap_invalid_conversion(void) __attribute__((noreturn));
void __wasm_trap_out_of_bounds(void) __attribute__((noreturn));
void __wasm_trap_null_reference(void) __attribute__((noreturn));

/* ============== Exception handling ============== */

void __wasm_push_exception_handler(void* label);
void __wasm_pop_exception_handler(void);
void __wasm_throw(int32_t tag, void* values) __attribute__((noreturn));
void __wasm_rethrow(void) __attribute__((noreturn));
void* __wasm_get_exception(void);

/* ============== GC operations ============== */

void* __wasm_struct_new(int32_t type_idx, int32_t num_fields);
void* __wasm_struct_new_default(int32_t type_idx, int32_t num_fields);
void* __wasm_array_new(int32_t type_idx, int32_t init_value, int32_t length);
void* __wasm_array_new_default(int32_t type_idx, int32_t length);
int64_t __wasm_ref_i31(int32_t value);
int32_t __wasm_i31_get_s(int64_t ref);
int32_t __wasm_i31_get_u(int64_t ref);
int32_t __wasm_ref_test(void* ref, int32_t type_idx);
int32_t __wasm_ref_test_null(void* ref, int32_t type_idx);
void* __wasm_ref_cast(void* ref, int32_t type_idx);
void* __wasm_ref_cast_null(void* ref, int32_t type_idx);

/* ============== Initialization ============== */

void __wasm_init(int32_t initial_pages);
void __wasm_fini(void);

#endif /* WASM_RUNTIME_H */
