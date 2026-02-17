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
#include <stddef.h>  /* For SIZE_MAX */
#include <math.h>
#include <string.h>

/* WASM memory (64KB pages) */
#define WASM_PAGE_SIZE 65536
#define WASM_MAX_PAGES 65536

/* Exported memory pointer - accessed by compiled WASM code */
uint8_t *__wasm_memory = NULL;
uint32_t __wasm_memory_size_pages = 0;

/*
 * Defense-in-depth bounds checking.
 * Enable by compiling with -DWAQ_RUNTIME_BOUNDS_CHECK
 * This adds runtime overhead but catches compiler bugs that could
 * otherwise lead to memory corruption.
 */
#ifdef WAQ_RUNTIME_BOUNDS_CHECK

static inline void __wasm_check_memory_bounds(uint64_t addr, uint32_t size) {
    uint64_t mem_size = (uint64_t)__wasm_memory_size_pages * WASM_PAGE_SIZE;
    if (addr > mem_size || size > mem_size - addr) {
        fprintf(stderr, "wasm bounds check failed: addr=%llu size=%u mem_size=%llu\n",
                (unsigned long long)addr, size, (unsigned long long)mem_size);
        __wasm_trap_out_of_bounds();
    }
}

/* Checked memory access functions */
uint8_t __wasm_load_i8(uint64_t addr) {
    __wasm_check_memory_bounds(addr, 1);
    return __wasm_memory[addr];
}

uint16_t __wasm_load_i16(uint64_t addr) {
    __wasm_check_memory_bounds(addr, 2);
    uint16_t val;
    memcpy(&val, __wasm_memory + addr, 2);
    return val;
}

uint32_t __wasm_load_i32(uint64_t addr) {
    __wasm_check_memory_bounds(addr, 4);
    uint32_t val;
    memcpy(&val, __wasm_memory + addr, 4);
    return val;
}

uint64_t __wasm_load_i64(uint64_t addr) {
    __wasm_check_memory_bounds(addr, 8);
    uint64_t val;
    memcpy(&val, __wasm_memory + addr, 8);
    return val;
}

float __wasm_load_f32(uint64_t addr) {
    __wasm_check_memory_bounds(addr, 4);
    float val;
    memcpy(&val, __wasm_memory + addr, 4);
    return val;
}

double __wasm_load_f64(uint64_t addr) {
    __wasm_check_memory_bounds(addr, 8);
    double val;
    memcpy(&val, __wasm_memory + addr, 8);
    return val;
}

void __wasm_store_i8(uint64_t addr, uint8_t val) {
    __wasm_check_memory_bounds(addr, 1);
    __wasm_memory[addr] = val;
}

void __wasm_store_i16(uint64_t addr, uint16_t val) {
    __wasm_check_memory_bounds(addr, 2);
    memcpy(__wasm_memory + addr, &val, 2);
}

void __wasm_store_i32(uint64_t addr, uint32_t val) {
    __wasm_check_memory_bounds(addr, 4);
    memcpy(__wasm_memory + addr, &val, 4);
}

void __wasm_store_i64(uint64_t addr, uint64_t val) {
    __wasm_check_memory_bounds(addr, 8);
    memcpy(__wasm_memory + addr, &val, 8);
}

void __wasm_store_f32(uint64_t addr, float val) {
    __wasm_check_memory_bounds(addr, 4);
    memcpy(__wasm_memory + addr, &val, 4);
}

void __wasm_store_f64(uint64_t addr, double val) {
    __wasm_check_memory_bounds(addr, 8);
    memcpy(__wasm_memory + addr, &val, 8);
}

#endif /* WAQ_RUNTIME_BOUNDS_CHECK */

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
    uint32_t delta_u = (uint32_t)delta;

    /* Check for overflow BEFORE addition */
    if (delta_u > WASM_MAX_PAGES - old_pages) return -1;

    uint32_t new_pages = old_pages + delta_u;

    /* Redundant check, but defensive */
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
    uint32_t delta_u = (uint32_t)delta;

    /* Check for overflow BEFORE addition */
    if (delta_u > WASM_MAX_TABLE_SIZE - old_size) return -1;

    uint32_t new_size = old_size + delta_u;

    /* Redundant check, but defensive */
    if (new_size > WASM_MAX_TABLE_SIZE) return -1;

    /* Check for allocation size overflow */
    if (new_size > SIZE_MAX / sizeof(void *)) return -1;

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

/* ============================================================================
 * EXCEPTION HANDLING (WASM 3.0)
 * ============================================================================
 * Uses setjmp/longjmp for stack unwinding.
 */

#include <setjmp.h>

/* Maximum exception payload size */
#define WASM_EXCEPTION_PAYLOAD_MAX 64

/* Exception data structure */
typedef struct {
    uint32_t tag_index;
    uint8_t payload[WASM_EXCEPTION_PAYLOAD_MAX];
    size_t payload_size;
} WasmException;

/* Exception handler frame */
typedef struct WasmExceptionFrame {
    jmp_buf env;
    struct WasmExceptionFrame *prev;
    WasmException exception;
    int caught;
} WasmExceptionFrame;

/* Thread-local exception handler stack */
static __thread WasmExceptionFrame *__wasm_exception_stack = NULL;
static __thread WasmException __wasm_current_exception;

/* Push a new exception handler frame */
int32_t __wasm_push_exception_handler(void) {
    /* Allocate frame on heap (could optimize with stack allocation) */
    WasmExceptionFrame *frame = malloc(sizeof(WasmExceptionFrame));
    if (!frame) {
        fprintf(stderr, "wasm trap: out of memory for exception handler\n");
        abort();
    }
    frame->prev = __wasm_exception_stack;
    frame->caught = 0;
    __wasm_exception_stack = frame;

    /* Return result of setjmp (0 = normal, non-zero = exception caught) */
    if (setjmp(frame->env) != 0) {
        /* Exception was caught - copy exception data */
        __wasm_current_exception = frame->exception;
        return 1;
    }
    return 0;
}

/* Pop the current exception handler */
void __wasm_pop_exception_handler(void) {
    if (__wasm_exception_stack) {
        WasmExceptionFrame *frame = __wasm_exception_stack;
        __wasm_exception_stack = frame->prev;
        free(frame);
    }
}

/* Throw an exception with the given tag */
void __wasm_throw(int32_t tag_index) {
    if (!__wasm_exception_stack) {
        fprintf(stderr, "wasm trap: uncaught exception (tag %d)\n", tag_index);
        abort();
    }

    WasmExceptionFrame *frame = __wasm_exception_stack;
    frame->exception.tag_index = tag_index;
    frame->exception.payload_size = 0;
    frame->caught = 1;

    longjmp(frame->env, 1);
}

/* Throw an exception with payload */
void __wasm_throw_with_payload(int32_t tag_index, void *payload, size_t size) {
    if (!__wasm_exception_stack) {
        fprintf(stderr, "wasm trap: uncaught exception (tag %d)\n", tag_index);
        abort();
    }

    WasmExceptionFrame *frame = __wasm_exception_stack;
    frame->exception.tag_index = tag_index;
    if (size > WASM_EXCEPTION_PAYLOAD_MAX) {
        size = WASM_EXCEPTION_PAYLOAD_MAX;
    }
    if (payload && size > 0) {
        memcpy(frame->exception.payload, payload, size);
    }
    frame->exception.payload_size = size;
    frame->caught = 1;

    longjmp(frame->env, 1);
}

/* Rethrow the current exception */
void __wasm_rethrow(void) {
    if (!__wasm_exception_stack) {
        fprintf(stderr, "wasm trap: rethrow without exception\n");
        abort();
    }

    /* Find the previous handler and throw to it */
    WasmExceptionFrame *current = __wasm_exception_stack;
    WasmException exc = current->exception;

    /* Pop current handler */
    __wasm_exception_stack = current->prev;
    free(current);

    if (!__wasm_exception_stack) {
        fprintf(stderr, "wasm trap: uncaught rethrown exception (tag %u)\n", exc.tag_index);
        abort();
    }

    /* Throw to the outer handler */
    __wasm_exception_stack->exception = exc;
    __wasm_exception_stack->caught = 1;
    longjmp(__wasm_exception_stack->env, 1);
}

/* Get the current exception reference */
void *__wasm_get_exception(void) {
    return &__wasm_current_exception;
}

/* Get the tag index of the current exception */
int32_t __wasm_get_exception_tag(void) {
    return (int32_t)__wasm_current_exception.tag_index;
}

/* Get pointer to exception payload */
void *__wasm_get_exception_payload(void) {
    return __wasm_current_exception.payload;
}

/* ============================================================================
 * GARBAGE COLLECTION (WASM GC)
 * ============================================================================
 * Simple bump allocator with no collection (for now).
 * TODO: Integrate with Boehm GC for real garbage collection.
 */

/* GC heap */
#define WASM_GC_HEAP_SIZE (64 * 1024 * 1024)  /* 64MB initial heap */

static uint8_t *__wasm_gc_heap = NULL;
static size_t __wasm_gc_heap_ptr = 0;
static size_t __wasm_gc_heap_size = 0;

/* Object header for GC objects */
typedef struct {
    uint32_t type_index;  /* Type index for runtime type checking */
    uint32_t flags;       /* GC flags (mark bit, etc.) */
} WasmGCHeader;

#define WASM_GC_HEADER_SIZE sizeof(WasmGCHeader)

/* Initialize GC heap */
void __wasm_gc_init(void) {
    if (!__wasm_gc_heap) {
        __wasm_gc_heap = malloc(WASM_GC_HEAP_SIZE);
        if (!__wasm_gc_heap) {
            fprintf(stderr, "wasm trap: failed to initialize GC heap\n");
            abort();
        }
        __wasm_gc_heap_ptr = 0;
        __wasm_gc_heap_size = WASM_GC_HEAP_SIZE;
    }
}

/* Allocate GC-managed memory */
void *__wasm_gc_alloc(size_t size) {
    if (!__wasm_gc_heap) {
        __wasm_gc_init();
    }

    /* Align to 8 bytes */
    size = (size + 7) & ~7;

    if (__wasm_gc_heap_ptr + size > __wasm_gc_heap_size) {
        /* Out of memory - try to expand heap */
        size_t new_size = __wasm_gc_heap_size * 2;
        uint8_t *new_heap = realloc(__wasm_gc_heap, new_size);
        if (!new_heap) {
            fprintf(stderr, "wasm trap: GC heap exhausted\n");
            abort();
        }
        __wasm_gc_heap = new_heap;
        __wasm_gc_heap_size = new_size;
    }

    void *ptr = __wasm_gc_heap + __wasm_gc_heap_ptr;
    __wasm_gc_heap_ptr += size;

    /* Zero-initialize */
    memset(ptr, 0, size);

    return ptr;
}

/* Allocate a struct */
void *__wasm_struct_new(int32_t type_idx, int32_t num_fields) {
    size_t size = WASM_GC_HEADER_SIZE + (size_t)num_fields * 8;
    void *obj = __wasm_gc_alloc(size);

    /* Set header */
    WasmGCHeader *header = (WasmGCHeader *)obj;
    header->type_index = (uint32_t)type_idx;
    header->flags = 0;

    /* Return pointer past header (to field data) */
    return (uint8_t *)obj + WASM_GC_HEADER_SIZE;
}

/* Allocate a struct with default (zero) values */
void *__wasm_struct_new_default(int32_t type_idx, int32_t num_fields) {
    /* Same as struct_new, memory is already zeroed */
    return __wasm_struct_new(type_idx, num_fields);
}

/* Array header: type_index (4) + flags (4) + length (4) + padding (4) = 16 bytes */
typedef struct {
    uint32_t type_index;
    uint32_t flags;
    uint32_t length;
    uint32_t _padding;
} WasmArrayHeader;

#define WASM_ARRAY_HEADER_SIZE sizeof(WasmArrayHeader)

/* Allocate an array */
void *__wasm_array_new(int32_t type_idx, int32_t length, int64_t init_value) {
    size_t elem_size = 8;  /* All elements stored as 64-bit for simplicity */
    size_t data_size = (size_t)length * elem_size;
    size_t total_size = WASM_ARRAY_HEADER_SIZE + data_size;

    void *obj = __wasm_gc_alloc(total_size);

    /* Set header */
    WasmArrayHeader *header = (WasmArrayHeader *)obj;
    header->type_index = (uint32_t)type_idx;
    header->flags = 0;
    header->length = (uint32_t)length;

    /* Initialize elements */
    int64_t *data = (int64_t *)((uint8_t *)obj + WASM_ARRAY_HEADER_SIZE);
    for (int32_t i = 0; i < length; i++) {
        data[i] = init_value;
    }

    /* Return pointer to length field (for array.len to work) */
    return &header->length;
}

/* Allocate an array with default values */
void *__wasm_array_new_default(int32_t type_idx, int32_t length) {
    return __wasm_array_new(type_idx, length, 0);
}

/* i31 operations - encode/decode 31-bit integers in pointers */
/* i31 is encoded as: (value << 1) | 1 */

int64_t __wasm_ref_i31(int32_t value) {
    /* Truncate to 31 bits, shift and set tag */
    int64_t i31 = (int64_t)(value & 0x7FFFFFFF);
    return (i31 << 1) | 1;
}

int32_t __wasm_i31_get_s(int64_t ref) {
    /* Shift right to remove tag, sign extend */
    int64_t val = ref >> 1;
    /* Sign extend from 31 bits */
    if (val & 0x40000000) {
        val |= 0xFFFFFFFF80000000ULL;
    }
    return (int32_t)val;
}

int32_t __wasm_i31_get_u(int64_t ref) {
    /* Shift right to remove tag, mask to 31 bits */
    return (int32_t)((ref >> 1) & 0x7FFFFFFF);
}

/* Reference type testing and casting */

/* Check if a reference is an i31 */
static int __wasm_is_i31(int64_t ref) {
    return (ref & 1) != 0;
}

/* Get header from object pointer */
static WasmGCHeader *__wasm_get_header(void *obj) {
    if (!obj) return NULL;
    return (WasmGCHeader *)((uint8_t *)obj - WASM_GC_HEADER_SIZE);
}

/* Test if reference is of the given type */
int32_t __wasm_ref_test(int64_t ref, int32_t type_idx) {
    if (ref == 0) return 0;  /* null fails test */
    if (__wasm_is_i31(ref)) return 0;  /* i31 is not a struct/array */

    WasmGCHeader *header = __wasm_get_header((void *)ref);
    if (!header) return 0;

    /* Simple equality check - could be extended for subtyping */
    return header->type_index == (uint32_t)type_idx ? 1 : 0;
}

/* Test if nullable reference is of the given type (null passes) */
int32_t __wasm_ref_test_null(int64_t ref, int32_t type_idx) {
    if (ref == 0) return 1;  /* null passes for nullable types */
    return __wasm_ref_test(ref, type_idx);
}

/* Cast reference to given type (traps on failure) */
int64_t __wasm_ref_cast(int64_t ref, int32_t type_idx) {
    if (ref == 0) {
        /* null cast to non-nullable type traps */
        fprintf(stderr, "wasm trap: null reference in ref.cast\n");
        abort();
    }
    if (!__wasm_ref_test(ref, type_idx)) {
        fprintf(stderr, "wasm trap: ref.cast failed (expected type %d)\n", type_idx);
        abort();
    }
    return ref;
}

/* Cast nullable reference (null is ok) */
int64_t __wasm_ref_cast_null(int64_t ref, int32_t type_idx) {
    if (ref == 0) return 0;  /* null is ok for nullable */
    if (!__wasm_ref_test(ref, type_idx)) {
        fprintf(stderr, "wasm trap: ref.cast failed (expected type %d)\n", type_idx);
        abort();
    }
    return ref;
}

/* Null reference trap */
void __wasm_trap_null_reference(void) {
    fprintf(stderr, "wasm trap: null reference\n");
    abort();
}

/* Cast failure trap */
void __wasm_trap_cast_failure(void) {
    fprintf(stderr, "wasm trap: cast failure\n");
    abort();
}

/* ============================================================================
 * MEMORY64 AND MULTI-MEMORY SUPPORT
 * ============================================================================
 */

/* Memory64 variants */
int64_t __wasm_memory_size_pages64(int32_t mem_idx) {
    (void)mem_idx;  /* Currently only single memory supported */
    return (int64_t)__wasm_memory_size_pages;
}

int64_t __wasm_memory_grow64(int32_t mem_idx, int64_t delta) {
    (void)mem_idx;
    if (delta < 0 || delta > WASM_MAX_PAGES) return -1;
    return (int64_t)__wasm_memory_grow((int32_t)delta);
}

/* Multi-memory support - currently just wraps single memory */
uint8_t *__wasm_memory_base_idx(int32_t mem_idx) {
    (void)mem_idx;
    return __wasm_memory;
}

int32_t __wasm_memory_size_pages_idx(int32_t mem_idx) {
    (void)mem_idx;
    return (int32_t)__wasm_memory_size_pages;
}

int32_t __wasm_memory_grow_idx(int32_t mem_idx, int32_t delta) {
    (void)mem_idx;
    return __wasm_memory_grow(delta);
}

/* Bulk memory operations */
void __wasm_memory_copy(int32_t dest, int32_t src, int32_t len) {
    if (!__wasm_memory) return;
    memmove(__wasm_memory + dest, __wasm_memory + src, len);
}

void __wasm_memory_fill(int32_t dest, int32_t val, int32_t len) {
    if (!__wasm_memory) return;
    memset(__wasm_memory + dest, val, len);
}

/* Data segment support */
typedef struct {
    uint8_t *data;
    size_t size;
    int dropped;
} WasmDataSegment;

#define WASM_MAX_DATA_SEGMENTS 256
static WasmDataSegment __wasm_data_segments[WASM_MAX_DATA_SEGMENTS];
static int __wasm_data_segment_count = 0;

void __wasm_register_data_segment(int32_t idx, uint8_t *data, size_t size) {
    if (idx >= 0 && idx < WASM_MAX_DATA_SEGMENTS) {
        __wasm_data_segments[idx].data = data;
        __wasm_data_segments[idx].size = size;
        __wasm_data_segments[idx].dropped = 0;
        if (idx >= __wasm_data_segment_count) {
            __wasm_data_segment_count = idx + 1;
        }
    }
}

void __wasm_memory_init_seg(int32_t seg_idx, int32_t dest, int32_t src_offset, int32_t len) {
    if (seg_idx < 0 || seg_idx >= __wasm_data_segment_count) {
        __wasm_trap_out_of_bounds();
    }
    WasmDataSegment *seg = &__wasm_data_segments[seg_idx];
    if (seg->dropped) {
        __wasm_trap_out_of_bounds();
    }
    if ((size_t)(src_offset + len) > seg->size) {
        __wasm_trap_out_of_bounds();
    }
    if (!__wasm_memory) return;
    memcpy(__wasm_memory + dest, seg->data + src_offset, len);
}

void __wasm_data_drop(int32_t seg_idx) {
    if (seg_idx >= 0 && seg_idx < WASM_MAX_DATA_SEGMENTS) {
        __wasm_data_segments[seg_idx].dropped = 1;
    }
}

/* Element segment support for table initialization */
void __wasm_table_init(int32_t table_idx, int32_t elem_idx, int32_t dest, int32_t src, int32_t len) {
    (void)table_idx;
    (void)elem_idx;
    (void)dest;
    (void)src;
    (void)len;
    /* TODO: Implement element segment initialization */
}

void __wasm_table_copy(int32_t dest_table, int32_t src_table, int32_t dest, int32_t src, int32_t len) {
    (void)dest_table;
    (void)src_table;
    if (!__wasm_table) return;
    memmove(&__wasm_table[dest], &__wasm_table[src], len * sizeof(void *));
}

void __wasm_table_fill(int32_t table_idx, int32_t dest, void *val, int32_t len) {
    (void)table_idx;
    if (!__wasm_table) return;
    for (int32_t i = 0; i < len; i++) {
        if ((uint32_t)(dest + i) < __wasm_table_size) {
            __wasm_table[dest + i] = val;
        }
    }
}

void __wasm_elem_drop(int32_t elem_idx) {
    (void)elem_idx;
    /* TODO: Mark element segment as dropped */
}

/* ============================================================================
 * WASI (WebAssembly System Interface) Preview 1
 * ============================================================================
 * Implements WASI functions for standalone executables.
 */

#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/uio.h>
#include <time.h>
#include <dirent.h>

#ifdef __APPLE__
#include <sys/random.h>
#include <sched.h>
#else
#include <sched.h>
#include <sys/random.h>
#endif

/* WASI Error codes (subset) */
typedef uint16_t __wasi_errno_t;
#define __WASI_ERRNO_SUCCESS        0
#define __WASI_ERRNO_2BIG           1
#define __WASI_ERRNO_ACCES          2
#define __WASI_ERRNO_ADDRINUSE      3
#define __WASI_ERRNO_ADDRNOTAVAIL   4
#define __WASI_ERRNO_AFNOSUPPORT    5
#define __WASI_ERRNO_AGAIN          6
#define __WASI_ERRNO_ALREADY        7
#define __WASI_ERRNO_BADF           8
#define __WASI_ERRNO_BADMSG         9
#define __WASI_ERRNO_BUSY           10
#define __WASI_ERRNO_CANCELED       11
#define __WASI_ERRNO_CHILD          12
#define __WASI_ERRNO_CONNABORTED    13
#define __WASI_ERRNO_CONNREFUSED    14
#define __WASI_ERRNO_CONNRESET      15
#define __WASI_ERRNO_DEADLK         16
#define __WASI_ERRNO_DESTADDRREQ    17
#define __WASI_ERRNO_DOM            18
#define __WASI_ERRNO_DQUOT          19
#define __WASI_ERRNO_EXIST          20
#define __WASI_ERRNO_FAULT          21
#define __WASI_ERRNO_FBIG           22
#define __WASI_ERRNO_HOSTUNREACH    23
#define __WASI_ERRNO_IDRM           24
#define __WASI_ERRNO_ILSEQ          25
#define __WASI_ERRNO_INPROGRESS     26
#define __WASI_ERRNO_INTR           27
#define __WASI_ERRNO_INVAL          28
#define __WASI_ERRNO_IO             29
#define __WASI_ERRNO_ISCONN         30
#define __WASI_ERRNO_ISDIR          31
#define __WASI_ERRNO_LOOP           32
#define __WASI_ERRNO_MFILE          33
#define __WASI_ERRNO_MLINK          34
#define __WASI_ERRNO_MSGSIZE        35
#define __WASI_ERRNO_MULTIHOP       36
#define __WASI_ERRNO_NAMETOOLONG    37
#define __WASI_ERRNO_NETDOWN        38
#define __WASI_ERRNO_NETRESET       39
#define __WASI_ERRNO_NETUNREACH     40
#define __WASI_ERRNO_NFILE          41
#define __WASI_ERRNO_NOBUFS         42
#define __WASI_ERRNO_NODEV          43
#define __WASI_ERRNO_NOENT          44
#define __WASI_ERRNO_NOEXEC         45
#define __WASI_ERRNO_NOLCK          46
#define __WASI_ERRNO_NOLINK         47
#define __WASI_ERRNO_NOMEM          48
#define __WASI_ERRNO_NOMSG          49
#define __WASI_ERRNO_NOPROTOOPT     50
#define __WASI_ERRNO_NOSPC          51
#define __WASI_ERRNO_NOSYS          52
#define __WASI_ERRNO_NOTCONN        53
#define __WASI_ERRNO_NOTDIR         54
#define __WASI_ERRNO_NOTEMPTY       55
#define __WASI_ERRNO_NOTRECOVERABLE 56
#define __WASI_ERRNO_NOTSOCK        57
#define __WASI_ERRNO_NOTSUP         58
#define __WASI_ERRNO_NOTTY          59
#define __WASI_ERRNO_NXIO           60
#define __WASI_ERRNO_OVERFLOW       61
#define __WASI_ERRNO_OWNERDEAD      62
#define __WASI_ERRNO_PERM           63
#define __WASI_ERRNO_PIPE           64
#define __WASI_ERRNO_PROTO          65
#define __WASI_ERRNO_PROTONOSUPPORT 66
#define __WASI_ERRNO_PROTOTYPE      67
#define __WASI_ERRNO_RANGE          68
#define __WASI_ERRNO_ROFS           69
#define __WASI_ERRNO_SPIPE          70
#define __WASI_ERRNO_SRCH           71
#define __WASI_ERRNO_STALE          72
#define __WASI_ERRNO_TIMEDOUT       73
#define __WASI_ERRNO_TXTBSY         74
#define __WASI_ERRNO_XDEV           75
#define __WASI_ERRNO_NOTCAPABLE     76

/* WASI file types */
typedef uint8_t __wasi_filetype_t;
#define __WASI_FILETYPE_UNKNOWN          0
#define __WASI_FILETYPE_BLOCK_DEVICE     1
#define __WASI_FILETYPE_CHARACTER_DEVICE 2
#define __WASI_FILETYPE_DIRECTORY        3
#define __WASI_FILETYPE_REGULAR_FILE     4
#define __WASI_FILETYPE_SOCKET_DGRAM     5
#define __WASI_FILETYPE_SOCKET_STREAM    6
#define __WASI_FILETYPE_SYMBOLIC_LINK    7

/* WASI clock IDs */
#define __WASI_CLOCKID_REALTIME           0
#define __WASI_CLOCKID_MONOTONIC          1
#define __WASI_CLOCKID_PROCESS_CPUTIME_ID 2
#define __WASI_CLOCKID_THREAD_CPUTIME_ID  3

/* WASI open flags */
#define __WASI_OFLAGS_CREAT     (1 << 0)
#define __WASI_OFLAGS_DIRECTORY (1 << 1)
#define __WASI_OFLAGS_EXCL      (1 << 2)
#define __WASI_OFLAGS_TRUNC     (1 << 3)

/* WASI rights */
#define __WASI_RIGHTS_FD_DATASYNC             ((uint64_t)1 << 0)
#define __WASI_RIGHTS_FD_READ                 ((uint64_t)1 << 1)
#define __WASI_RIGHTS_FD_SEEK                 ((uint64_t)1 << 2)
#define __WASI_RIGHTS_FD_FDSTAT_SET_FLAGS     ((uint64_t)1 << 3)
#define __WASI_RIGHTS_FD_SYNC                 ((uint64_t)1 << 4)
#define __WASI_RIGHTS_FD_TELL                 ((uint64_t)1 << 5)
#define __WASI_RIGHTS_FD_WRITE                ((uint64_t)1 << 6)
#define __WASI_RIGHTS_FD_ADVISE               ((uint64_t)1 << 7)
#define __WASI_RIGHTS_FD_ALLOCATE             ((uint64_t)1 << 8)
#define __WASI_RIGHTS_PATH_CREATE_DIRECTORY   ((uint64_t)1 << 9)
#define __WASI_RIGHTS_PATH_CREATE_FILE        ((uint64_t)1 << 10)
#define __WASI_RIGHTS_PATH_LINK_SOURCE        ((uint64_t)1 << 11)
#define __WASI_RIGHTS_PATH_LINK_TARGET        ((uint64_t)1 << 12)
#define __WASI_RIGHTS_PATH_OPEN               ((uint64_t)1 << 13)
#define __WASI_RIGHTS_FD_READDIR              ((uint64_t)1 << 14)
#define __WASI_RIGHTS_PATH_READLINK           ((uint64_t)1 << 15)
#define __WASI_RIGHTS_PATH_RENAME_SOURCE      ((uint64_t)1 << 16)
#define __WASI_RIGHTS_PATH_RENAME_TARGET      ((uint64_t)1 << 17)
#define __WASI_RIGHTS_PATH_FILESTAT_GET       ((uint64_t)1 << 18)
#define __WASI_RIGHTS_PATH_FILESTAT_SET_SIZE  ((uint64_t)1 << 19)
#define __WASI_RIGHTS_PATH_FILESTAT_SET_TIMES ((uint64_t)1 << 20)
#define __WASI_RIGHTS_FD_FILESTAT_GET         ((uint64_t)1 << 21)
#define __WASI_RIGHTS_FD_FILESTAT_SET_SIZE    ((uint64_t)1 << 22)
#define __WASI_RIGHTS_FD_FILESTAT_SET_TIMES   ((uint64_t)1 << 23)
#define __WASI_RIGHTS_PATH_SYMLINK            ((uint64_t)1 << 24)
#define __WASI_RIGHTS_PATH_REMOVE_DIRECTORY   ((uint64_t)1 << 25)
#define __WASI_RIGHTS_PATH_UNLINK_FILE        ((uint64_t)1 << 26)
#define __WASI_RIGHTS_POLL_FD_READWRITE       ((uint64_t)1 << 27)
#define __WASI_RIGHTS_SOCK_SHUTDOWN           ((uint64_t)1 << 28)
#define __WASI_RIGHTS_SOCK_ACCEPT             ((uint64_t)1 << 29)

/* All rights for convenience */
#define __WASI_RIGHTS_ALL ((uint64_t)0x1FFFFFFF)

/* WASI I/O vectors (in WASM linear memory) */
typedef struct {
    uint32_t buf;
    uint32_t buf_len;
} __wasi_iovec_t;

typedef struct {
    uint32_t buf;
    uint32_t buf_len;
} __wasi_ciovec_t;

/* WASI preopen types */
#define __WASI_PREOPENTYPE_DIR 0

typedef struct {
    uint8_t tag;
    uint32_t name_len;
} __wasi_prestat_t;

/* File descriptor table */
#define WASI_MAX_FDS 1024

typedef struct {
    int host_fd;
    __wasi_filetype_t type;
    char *preopen_path;
    uint64_t rights;
} WasiFd;

static WasiFd __wasi_fd_table[WASI_MAX_FDS];
static int __wasi_initialized = 0;

/* Arguments and environment */
static char **__wasi_argv = NULL;
static int __wasi_argc = 0;
static char **__wasi_environ_ptr = NULL;

/* Convert errno to WASI error code */
static __wasi_errno_t errno_to_wasi(int err) {
    switch (err) {
        case 0: return __WASI_ERRNO_SUCCESS;
        case EACCES: return __WASI_ERRNO_ACCES;
        case EAGAIN: return __WASI_ERRNO_AGAIN;
        case EBADF: return __WASI_ERRNO_BADF;
        case EBUSY: return __WASI_ERRNO_BUSY;
        case EEXIST: return __WASI_ERRNO_EXIST;
        case EFAULT: return __WASI_ERRNO_FAULT;
        case EINTR: return __WASI_ERRNO_INTR;
        case EINVAL: return __WASI_ERRNO_INVAL;
        case EIO: return __WASI_ERRNO_IO;
        case EISDIR: return __WASI_ERRNO_ISDIR;
        case ELOOP: return __WASI_ERRNO_LOOP;
        case EMFILE: return __WASI_ERRNO_MFILE;
        case ENAMETOOLONG: return __WASI_ERRNO_NAMETOOLONG;
        case ENFILE: return __WASI_ERRNO_NFILE;
        case ENOENT: return __WASI_ERRNO_NOENT;
        case ENOMEM: return __WASI_ERRNO_NOMEM;
        case ENOSPC: return __WASI_ERRNO_NOSPC;
        case ENOSYS: return __WASI_ERRNO_NOSYS;
        case ENOTDIR: return __WASI_ERRNO_NOTDIR;
        case ENOTEMPTY: return __WASI_ERRNO_NOTEMPTY;
        case ENOTSUP: return __WASI_ERRNO_NOTSUP;
        case EPERM: return __WASI_ERRNO_PERM;
        case EPIPE: return __WASI_ERRNO_PIPE;
        case EROFS: return __WASI_ERRNO_ROFS;
        case ESPIPE: return __WASI_ERRNO_SPIPE;
        default: return __WASI_ERRNO_IO;
    }
}

/* Allocate a WASI file descriptor */
static int wasi_alloc_fd(void) {
    for (int i = 3; i < WASI_MAX_FDS; i++) {
        if (__wasi_fd_table[i].host_fd < 0) {
            return i;
        }
    }
    return -1;
}

/* Initialize WASI runtime */
void __wasi_init(int argc, char **argv, char **environ) {
    if (__wasi_initialized) return;

    /* Initialize all FDs as unused */
    for (int i = 0; i < WASI_MAX_FDS; i++) {
        __wasi_fd_table[i].host_fd = -1;
        __wasi_fd_table[i].preopen_path = NULL;
    }

    /* Set up standard I/O */
    __wasi_fd_table[0].host_fd = STDIN_FILENO;
    __wasi_fd_table[0].type = __WASI_FILETYPE_CHARACTER_DEVICE;
    __wasi_fd_table[0].rights = __WASI_RIGHTS_FD_READ;

    __wasi_fd_table[1].host_fd = STDOUT_FILENO;
    __wasi_fd_table[1].type = __WASI_FILETYPE_CHARACTER_DEVICE;
    __wasi_fd_table[1].rights = __WASI_RIGHTS_FD_WRITE;

    __wasi_fd_table[2].host_fd = STDERR_FILENO;
    __wasi_fd_table[2].type = __WASI_FILETYPE_CHARACTER_DEVICE;
    __wasi_fd_table[2].rights = __WASI_RIGHTS_FD_WRITE;

    /* Set up preopen for current directory */
    int dir_fd = open(".", O_RDONLY | O_DIRECTORY);
    if (dir_fd >= 0) {
        __wasi_fd_table[3].host_fd = dir_fd;
        __wasi_fd_table[3].type = __WASI_FILETYPE_DIRECTORY;
        __wasi_fd_table[3].preopen_path = strdup(".");
        __wasi_fd_table[3].rights = __WASI_RIGHTS_ALL;
    }

    /* Store args and environment */
    __wasi_argc = argc;
    __wasi_argv = argv;
    __wasi_environ_ptr = environ;

    __wasi_initialized = 1;
}

/* ---- Process Control ---- */

void __wasi_proc_exit(int32_t code) {
    exit(code);
}

/* ---- Arguments and Environment ---- */

__wasi_errno_t __wasi_args_sizes_get(uint32_t *argc_out, uint32_t *argv_buf_size_out) {
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    uint32_t *argc_ptr = (uint32_t *)(__wasm_memory + *argc_out);
    uint32_t *buf_size_ptr = (uint32_t *)(__wasm_memory + *argv_buf_size_out);

    *argc_ptr = (uint32_t)__wasi_argc;

    size_t total_size = 0;
    for (int i = 0; i < __wasi_argc; i++) {
        total_size += strlen(__wasi_argv[i]) + 1;
    }
    *buf_size_ptr = (uint32_t)total_size;

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_args_get(uint32_t argv_ptr, uint32_t argv_buf_ptr) {
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    uint32_t *argv = (uint32_t *)(__wasm_memory + argv_ptr);
    uint8_t *buf = __wasm_memory + argv_buf_ptr;

    uint32_t offset = 0;
    for (int i = 0; i < __wasi_argc; i++) {
        argv[i] = argv_buf_ptr + offset;
        size_t len = strlen(__wasi_argv[i]) + 1;
        memcpy(buf + offset, __wasi_argv[i], len);
        offset += len;
    }

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_environ_sizes_get(uint32_t *count_out, uint32_t *buf_size_out) {
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    uint32_t *count_ptr = (uint32_t *)(__wasm_memory + *count_out);
    uint32_t *buf_size_ptr = (uint32_t *)(__wasm_memory + *buf_size_out);

    if (!__wasi_environ_ptr) {
        *count_ptr = 0;
        *buf_size_ptr = 0;
        return __WASI_ERRNO_SUCCESS;
    }

    uint32_t count = 0;
    size_t total_size = 0;
    for (char **env = __wasi_environ_ptr; *env != NULL; env++) {
        count++;
        total_size += strlen(*env) + 1;
    }

    *count_ptr = count;
    *buf_size_ptr = (uint32_t)total_size;

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_environ_get(uint32_t environ_ptr, uint32_t environ_buf_ptr) {
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;
    if (!__wasi_environ_ptr) return __WASI_ERRNO_SUCCESS;

    uint32_t *env = (uint32_t *)(__wasm_memory + environ_ptr);
    uint8_t *buf = __wasm_memory + environ_buf_ptr;

    uint32_t offset = 0;
    int i = 0;
    for (char **e = __wasi_environ_ptr; *e != NULL; e++, i++) {
        env[i] = environ_buf_ptr + offset;
        size_t len = strlen(*e) + 1;
        memcpy(buf + offset, *e, len);
        offset += len;
    }

    return __WASI_ERRNO_SUCCESS;
}

/* ---- File Descriptor Operations ---- */

__wasi_errno_t __wasi_fd_close(int32_t fd) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;

    /* Don't close stdin/stdout/stderr */
    if (fd >= 3) {
        close(__wasi_fd_table[fd].host_fd);
    }

    __wasi_fd_table[fd].host_fd = -1;
    free(__wasi_fd_table[fd].preopen_path);
    __wasi_fd_table[fd].preopen_path = NULL;

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_fd_write(int32_t fd, uint32_t iovs_ptr, uint32_t iovs_len, uint32_t nwritten_ptr) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    __wasi_ciovec_t *iovs = (__wasi_ciovec_t *)(__wasm_memory + iovs_ptr);
    uint32_t *nwritten = (uint32_t *)(__wasm_memory + nwritten_ptr);

    /* Convert WASM iovecs to host iovecs */
    struct iovec *host_iovs = alloca(iovs_len * sizeof(struct iovec));
    for (uint32_t i = 0; i < iovs_len; i++) {
        host_iovs[i].iov_base = __wasm_memory + iovs[i].buf;
        host_iovs[i].iov_len = iovs[i].buf_len;
    }

    ssize_t written = writev(__wasi_fd_table[fd].host_fd, host_iovs, (int)iovs_len);
    if (written < 0) {
        return errno_to_wasi(errno);
    }

    *nwritten = (uint32_t)written;
    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_fd_read(int32_t fd, uint32_t iovs_ptr, uint32_t iovs_len, uint32_t nread_ptr) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    __wasi_iovec_t *iovs = (__wasi_iovec_t *)(__wasm_memory + iovs_ptr);
    uint32_t *nread = (uint32_t *)(__wasm_memory + nread_ptr);

    struct iovec *host_iovs = alloca(iovs_len * sizeof(struct iovec));
    for (uint32_t i = 0; i < iovs_len; i++) {
        host_iovs[i].iov_base = __wasm_memory + iovs[i].buf;
        host_iovs[i].iov_len = iovs[i].buf_len;
    }

    ssize_t read_bytes = readv(__wasi_fd_table[fd].host_fd, host_iovs, (int)iovs_len);
    if (read_bytes < 0) {
        return errno_to_wasi(errno);
    }

    *nread = (uint32_t)read_bytes;
    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_fd_seek(int32_t fd, int64_t offset, uint8_t whence, uint32_t newoffset_ptr) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    int host_whence;
    switch (whence) {
        case 0: host_whence = SEEK_SET; break;
        case 1: host_whence = SEEK_CUR; break;
        case 2: host_whence = SEEK_END; break;
        default: return __WASI_ERRNO_INVAL;
    }

    off_t result = lseek(__wasi_fd_table[fd].host_fd, (off_t)offset, host_whence);
    if (result < 0) {
        return errno_to_wasi(errno);
    }

    uint64_t *newoffset = (uint64_t *)(__wasm_memory + newoffset_ptr);
    *newoffset = (uint64_t)result;

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_fd_tell(int32_t fd, uint32_t offset_ptr) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    off_t result = lseek(__wasi_fd_table[fd].host_fd, 0, SEEK_CUR);
    if (result < 0) {
        return errno_to_wasi(errno);
    }

    uint64_t *offset = (uint64_t *)(__wasm_memory + offset_ptr);
    *offset = (uint64_t)result;

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_fd_sync(int32_t fd) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;

    if (fsync(__wasi_fd_table[fd].host_fd) != 0) {
        return errno_to_wasi(errno);
    }

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_fd_fdstat_get(int32_t fd, uint32_t stat_ptr) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    /* WASI fdstat structure */
    uint8_t *stat = __wasm_memory + stat_ptr;

    /* fs_filetype (1 byte) */
    stat[0] = __wasi_fd_table[fd].type;
    /* fs_flags (2 bytes) */
    stat[1] = 0;
    stat[2] = 0;
    /* padding (1 byte) */
    stat[3] = 0;
    /* fs_rights_base (8 bytes) */
    memcpy(stat + 8, &__wasi_fd_table[fd].rights, 8);
    /* fs_rights_inheriting (8 bytes) */
    memcpy(stat + 16, &__wasi_fd_table[fd].rights, 8);

    return __WASI_ERRNO_SUCCESS;
}

/* ---- Preopen Support ---- */

__wasi_errno_t __wasi_fd_prestat_get(int32_t fd, uint32_t prestat_ptr) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasi_fd_table[fd].preopen_path) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    __wasi_prestat_t *prestat = (__wasi_prestat_t *)(__wasm_memory + prestat_ptr);
    prestat->tag = __WASI_PREOPENTYPE_DIR;
    prestat->name_len = (uint32_t)strlen(__wasi_fd_table[fd].preopen_path);

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_fd_prestat_dir_name(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasi_fd_table[fd].preopen_path) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    size_t len = strlen(__wasi_fd_table[fd].preopen_path);
    if (len > path_len) {
        return __WASI_ERRNO_NAMETOOLONG;
    }

    memcpy(__wasm_memory + path_ptr, __wasi_fd_table[fd].preopen_path, len);

    return __WASI_ERRNO_SUCCESS;
}

/* ---- Path Operations ---- */

__wasi_errno_t __wasi_path_open(
    int32_t dirfd,
    uint32_t dirflags,
    uint32_t path_ptr,
    uint32_t path_len,
    uint32_t oflags,
    uint64_t fs_rights_base,
    uint64_t fs_rights_inheriting,
    uint16_t fdflags,
    uint32_t opened_fd_ptr
) {
    (void)dirflags;
    (void)fs_rights_inheriting;
    (void)fdflags;

    if (dirfd < 0 || dirfd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[dirfd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    /* Copy path to null-terminated string */
    char *path = alloca(path_len + 1);
    memcpy(path, __wasm_memory + path_ptr, path_len);
    path[path_len] = '\0';

    /* Convert WASI flags to POSIX flags */
    int host_flags = 0;
    if (oflags & __WASI_OFLAGS_CREAT) host_flags |= O_CREAT;
    if (oflags & __WASI_OFLAGS_EXCL) host_flags |= O_EXCL;
    if (oflags & __WASI_OFLAGS_TRUNC) host_flags |= O_TRUNC;
    if (oflags & __WASI_OFLAGS_DIRECTORY) host_flags |= O_DIRECTORY;

    /* Determine read/write mode from rights */
    if ((fs_rights_base & __WASI_RIGHTS_FD_READ) &&
        (fs_rights_base & __WASI_RIGHTS_FD_WRITE)) {
        host_flags |= O_RDWR;
    } else if (fs_rights_base & __WASI_RIGHTS_FD_WRITE) {
        host_flags |= O_WRONLY;
    } else {
        host_flags |= O_RDONLY;
    }

    int host_fd = openat(__wasi_fd_table[dirfd].host_fd, path, host_flags, 0666);
    if (host_fd < 0) {
        return errno_to_wasi(errno);
    }

    /* Allocate WASI fd */
    int new_fd = wasi_alloc_fd();
    if (new_fd < 0) {
        close(host_fd);
        return __WASI_ERRNO_NFILE;
    }

    /* Determine file type */
    struct stat st;
    __wasi_filetype_t file_type = __WASI_FILETYPE_UNKNOWN;
    if (fstat(host_fd, &st) == 0) {
        if (S_ISREG(st.st_mode)) file_type = __WASI_FILETYPE_REGULAR_FILE;
        else if (S_ISDIR(st.st_mode)) file_type = __WASI_FILETYPE_DIRECTORY;
        else if (S_ISBLK(st.st_mode)) file_type = __WASI_FILETYPE_BLOCK_DEVICE;
        else if (S_ISCHR(st.st_mode)) file_type = __WASI_FILETYPE_CHARACTER_DEVICE;
        else if (S_ISLNK(st.st_mode)) file_type = __WASI_FILETYPE_SYMBOLIC_LINK;
    }

    __wasi_fd_table[new_fd].host_fd = host_fd;
    __wasi_fd_table[new_fd].type = file_type;
    __wasi_fd_table[new_fd].rights = fs_rights_base;
    __wasi_fd_table[new_fd].preopen_path = NULL;

    uint32_t *opened_fd = (uint32_t *)(__wasm_memory + opened_fd_ptr);
    *opened_fd = (uint32_t)new_fd;

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_path_create_directory(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    char *path = alloca(path_len + 1);
    memcpy(path, __wasm_memory + path_ptr, path_len);
    path[path_len] = '\0';

    if (mkdirat(__wasi_fd_table[fd].host_fd, path, 0777) != 0) {
        return errno_to_wasi(errno);
    }

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_path_unlink_file(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    char *path = alloca(path_len + 1);
    memcpy(path, __wasm_memory + path_ptr, path_len);
    path[path_len] = '\0';

    if (unlinkat(__wasi_fd_table[fd].host_fd, path, 0) != 0) {
        return errno_to_wasi(errno);
    }

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_path_remove_directory(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    char *path = alloca(path_len + 1);
    memcpy(path, __wasm_memory + path_ptr, path_len);
    path[path_len] = '\0';

    if (unlinkat(__wasi_fd_table[fd].host_fd, path, AT_REMOVEDIR) != 0) {
        return errno_to_wasi(errno);
    }

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_path_rename(
    int32_t old_fd, uint32_t old_path_ptr, uint32_t old_path_len,
    int32_t new_fd, uint32_t new_path_ptr, uint32_t new_path_len
) {
    if (old_fd < 0 || old_fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[old_fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (new_fd < 0 || new_fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[new_fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    char *old_path = alloca(old_path_len + 1);
    memcpy(old_path, __wasm_memory + old_path_ptr, old_path_len);
    old_path[old_path_len] = '\0';

    char *new_path = alloca(new_path_len + 1);
    memcpy(new_path, __wasm_memory + new_path_ptr, new_path_len);
    new_path[new_path_len] = '\0';

    if (renameat(__wasi_fd_table[old_fd].host_fd, old_path,
                 __wasi_fd_table[new_fd].host_fd, new_path) != 0) {
        return errno_to_wasi(errno);
    }

    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_path_filestat_get(
    int32_t fd, uint32_t flags, uint32_t path_ptr, uint32_t path_len, uint32_t buf_ptr
) {
    (void)flags;
    if (fd < 0 || fd >= WASI_MAX_FDS) return __WASI_ERRNO_BADF;
    if (__wasi_fd_table[fd].host_fd < 0) return __WASI_ERRNO_BADF;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    char *path = alloca(path_len + 1);
    memcpy(path, __wasm_memory + path_ptr, path_len);
    path[path_len] = '\0';

    struct stat st;
    if (fstatat(__wasi_fd_table[fd].host_fd, path, &st, 0) != 0) {
        return errno_to_wasi(errno);
    }

    /* WASI filestat structure (64 bytes) */
    uint8_t *buf = __wasm_memory + buf_ptr;
    memset(buf, 0, 64);

    /* dev (8 bytes) */
    *(uint64_t *)(buf + 0) = (uint64_t)st.st_dev;
    /* ino (8 bytes) */
    *(uint64_t *)(buf + 8) = (uint64_t)st.st_ino;
    /* filetype (1 byte) */
    if (S_ISREG(st.st_mode)) buf[16] = __WASI_FILETYPE_REGULAR_FILE;
    else if (S_ISDIR(st.st_mode)) buf[16] = __WASI_FILETYPE_DIRECTORY;
    else if (S_ISBLK(st.st_mode)) buf[16] = __WASI_FILETYPE_BLOCK_DEVICE;
    else if (S_ISCHR(st.st_mode)) buf[16] = __WASI_FILETYPE_CHARACTER_DEVICE;
    else if (S_ISLNK(st.st_mode)) buf[16] = __WASI_FILETYPE_SYMBOLIC_LINK;
    /* nlink (8 bytes at offset 24) */
    *(uint64_t *)(buf + 24) = (uint64_t)st.st_nlink;
    /* size (8 bytes at offset 32) */
    *(uint64_t *)(buf + 32) = (uint64_t)st.st_size;
    /* atim (8 bytes at offset 40) */
#ifdef __APPLE__
    *(uint64_t *)(buf + 40) = (uint64_t)st.st_atimespec.tv_sec * 1000000000ULL + st.st_atimespec.tv_nsec;
    *(uint64_t *)(buf + 48) = (uint64_t)st.st_mtimespec.tv_sec * 1000000000ULL + st.st_mtimespec.tv_nsec;
    *(uint64_t *)(buf + 56) = (uint64_t)st.st_ctimespec.tv_sec * 1000000000ULL + st.st_ctimespec.tv_nsec;
#else
    *(uint64_t *)(buf + 40) = (uint64_t)st.st_atim.tv_sec * 1000000000ULL + st.st_atim.tv_nsec;
    *(uint64_t *)(buf + 48) = (uint64_t)st.st_mtim.tv_sec * 1000000000ULL + st.st_mtim.tv_nsec;
    *(uint64_t *)(buf + 56) = (uint64_t)st.st_ctim.tv_sec * 1000000000ULL + st.st_ctim.tv_nsec;
#endif

    return __WASI_ERRNO_SUCCESS;
}

/* ---- Clock Functions ---- */

__wasi_errno_t __wasi_clock_res_get(uint32_t clock_id, uint32_t resolution_ptr) {
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    uint64_t *resolution = (uint64_t *)(__wasm_memory + resolution_ptr);

    /* Return nanosecond resolution for all clocks */
    switch (clock_id) {
        case __WASI_CLOCKID_REALTIME:
        case __WASI_CLOCKID_MONOTONIC:
            *resolution = 1;  /* 1 nanosecond */
            return __WASI_ERRNO_SUCCESS;
        default:
            return __WASI_ERRNO_INVAL;
    }
}

__wasi_errno_t __wasi_clock_time_get(uint32_t clock_id, uint64_t precision, uint32_t time_ptr) {
    (void)precision;
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    uint64_t *time = (uint64_t *)(__wasm_memory + time_ptr);

    struct timespec ts;

#ifdef __APPLE__
    switch (clock_id) {
        case __WASI_CLOCKID_REALTIME:
            clock_gettime(CLOCK_REALTIME, &ts);
            break;
        case __WASI_CLOCKID_MONOTONIC:
            clock_gettime(CLOCK_MONOTONIC, &ts);
            break;
        default:
            return __WASI_ERRNO_INVAL;
    }
#else
    clockid_t host_clock;
    switch (clock_id) {
        case __WASI_CLOCKID_REALTIME:
            host_clock = CLOCK_REALTIME;
            break;
        case __WASI_CLOCKID_MONOTONIC:
            host_clock = CLOCK_MONOTONIC;
            break;
        case __WASI_CLOCKID_PROCESS_CPUTIME_ID:
            host_clock = CLOCK_PROCESS_CPUTIME_ID;
            break;
        case __WASI_CLOCKID_THREAD_CPUTIME_ID:
            host_clock = CLOCK_THREAD_CPUTIME_ID;
            break;
        default:
            return __WASI_ERRNO_INVAL;
    }

    if (clock_gettime(host_clock, &ts) != 0) {
        return errno_to_wasi(errno);
    }
#endif

    *time = (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
    return __WASI_ERRNO_SUCCESS;
}

/* ---- Random ---- */

__wasi_errno_t __wasi_random_get(uint32_t buf_ptr, uint32_t buf_len) {
    if (!__wasm_memory) return __WASI_ERRNO_FAULT;

    uint8_t *buf = __wasm_memory + buf_ptr;

#ifdef __APPLE__
    arc4random_buf(buf, buf_len);
    return __WASI_ERRNO_SUCCESS;
#elif defined(__linux__)
    ssize_t result = getrandom(buf, buf_len, 0);
    if (result < 0 || (size_t)result != buf_len) {
        return __WASI_ERRNO_IO;
    }
    return __WASI_ERRNO_SUCCESS;
#else
    /* Fallback: read from /dev/urandom */
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) {
        return __WASI_ERRNO_IO;
    }
    ssize_t n = read(fd, buf, buf_len);
    close(fd);
    if (n < 0 || (size_t)n != buf_len) {
        return __WASI_ERRNO_IO;
    }
    return __WASI_ERRNO_SUCCESS;
#endif
}

/* ---- Stub functions for less common WASI calls ---- */

__wasi_errno_t __wasi_sched_yield(void) {
    sched_yield();
    return __WASI_ERRNO_SUCCESS;
}

__wasi_errno_t __wasi_poll_oneoff(
    uint32_t in_ptr, uint32_t out_ptr, uint32_t nsubscriptions, uint32_t nevents_ptr
) {
    (void)in_ptr;
    (void)out_ptr;
    (void)nsubscriptions;
    (void)nevents_ptr;
    return __WASI_ERRNO_NOSYS;
}

/* ============================================================================
 * DETERMINISTIC PROFILE
 * ============================================================================
 * Canonical NaN handling for reproducible execution.
 */

/* Canonical NaN values */
#define WASM_CANONICAL_NAN_F32 0x7FC00000
#define WASM_CANONICAL_NAN_F64 0x7FF8000000000000ULL

/* Canonicalize f32 NaN */
float __wasm_canon_nan_f32(float val) {
    if (__builtin_isnan(val)) {
        union { float f; uint32_t i; } u;
        u.i = WASM_CANONICAL_NAN_F32;
        return u.f;
    }
    return val;
}

/* Canonicalize f64 NaN */
double __wasm_canon_nan_f64(double val) {
    if (__builtin_isnan(val)) {
        union { double d; uint64_t i; } u;
        u.i = WASM_CANONICAL_NAN_F64;
        return u.d;
    }
    return val;
}

/* Deterministic float operations */
float __wasm_f32_div_deterministic(float a, float b) {
    return __wasm_canon_nan_f32(a / b);
}

double __wasm_f64_div_deterministic(double a, double b) {
    return __wasm_canon_nan_f64(a / b);
}

float __wasm_f32_sqrt_deterministic(float x) {
    return __wasm_canon_nan_f32(sqrtf(x));
}

double __wasm_f64_sqrt_deterministic(double x) {
    return __wasm_canon_nan_f64(sqrt(x));
}

float __wasm_f32_min_deterministic(float a, float b) {
    return __wasm_canon_nan_f32(fminf(a, b));
}

float __wasm_f32_max_deterministic(float a, float b) {
    return __wasm_canon_nan_f32(fmaxf(a, b));
}

double __wasm_f64_min_deterministic(double a, double b) {
    return __wasm_canon_nan_f64(fmin(a, b));
}

double __wasm_f64_max_deterministic(double a, double b) {
    return __wasm_canon_nan_f64(fmax(a, b));
}

/* ============================================================================
 * RELAXED SIMD - SCALAR FALLBACK
 * ============================================================================
 * QBE has no SIMD support, so we implement v128 operations with scalar code.
 * All v128 values are passed by reference (pointer to 16-byte aligned memory).
 */

typedef union {
    int8_t   i8[16];
    uint8_t  u8[16];
    int16_t  i16[8];
    uint16_t u16[8];
    int32_t  i32[4];
    uint32_t u32[4];
    int64_t  i64[2];
    uint64_t u64[2];
    float    f32[4];
    double   f64[2];
} v128_t;

/* ---- Lane Selection and Swizzle ---- */

void __wasm_i8x16_relaxed_swizzle(v128_t *result, v128_t *a, v128_t *s) {
    for (int i = 0; i < 16; i++) {
        int idx = s->u8[i];
        /* Relaxed: undefined for idx >= 16, we just mask */
        result->i8[i] = a->i8[idx & 15];
    }
}

void __wasm_i8x16_relaxed_laneselect(v128_t *result, v128_t *a, v128_t *b, v128_t *m) {
    for (int i = 0; i < 16; i++) {
        result->i8[i] = (m->i8[i] & 0x80) ? b->i8[i] : a->i8[i];
    }
}

void __wasm_i16x8_relaxed_laneselect(v128_t *result, v128_t *a, v128_t *b, v128_t *m) {
    for (int i = 0; i < 8; i++) {
        result->i16[i] = (m->i16[i] < 0) ? b->i16[i] : a->i16[i];
    }
}

void __wasm_i32x4_relaxed_laneselect(v128_t *result, v128_t *a, v128_t *b, v128_t *m) {
    for (int i = 0; i < 4; i++) {
        result->i32[i] = (m->i32[i] < 0) ? b->i32[i] : a->i32[i];
    }
}

void __wasm_i64x2_relaxed_laneselect(v128_t *result, v128_t *a, v128_t *b, v128_t *m) {
    for (int i = 0; i < 2; i++) {
        result->i64[i] = (m->i64[i] < 0) ? b->i64[i] : a->i64[i];
    }
}

/* ---- Relaxed Min/Max ---- */

void __wasm_f32x4_relaxed_min(v128_t *result, v128_t *a, v128_t *b) {
    for (int i = 0; i < 4; i++) {
        /* Relaxed NaN behavior - just use fminf */
        result->f32[i] = fminf(a->f32[i], b->f32[i]);
    }
}

void __wasm_f32x4_relaxed_max(v128_t *result, v128_t *a, v128_t *b) {
    for (int i = 0; i < 4; i++) {
        result->f32[i] = fmaxf(a->f32[i], b->f32[i]);
    }
}

void __wasm_f64x2_relaxed_min(v128_t *result, v128_t *a, v128_t *b) {
    for (int i = 0; i < 2; i++) {
        result->f64[i] = fmin(a->f64[i], b->f64[i]);
    }
}

void __wasm_f64x2_relaxed_max(v128_t *result, v128_t *a, v128_t *b) {
    for (int i = 0; i < 2; i++) {
        result->f64[i] = fmax(a->f64[i], b->f64[i]);
    }
}

/* ---- Fused Multiply-Add ---- */

void __wasm_f32x4_relaxed_madd(v128_t *result, v128_t *a, v128_t *b, v128_t *c) {
    for (int i = 0; i < 4; i++) {
#ifdef FP_FAST_FMAF
        result->f32[i] = fmaf(a->f32[i], b->f32[i], c->f32[i]);
#else
        result->f32[i] = a->f32[i] * b->f32[i] + c->f32[i];
#endif
    }
}

void __wasm_f32x4_relaxed_nmadd(v128_t *result, v128_t *a, v128_t *b, v128_t *c) {
    for (int i = 0; i < 4; i++) {
#ifdef FP_FAST_FMAF
        result->f32[i] = fmaf(-a->f32[i], b->f32[i], c->f32[i]);
#else
        result->f32[i] = -(a->f32[i] * b->f32[i]) + c->f32[i];
#endif
    }
}

void __wasm_f64x2_relaxed_madd(v128_t *result, v128_t *a, v128_t *b, v128_t *c) {
    for (int i = 0; i < 2; i++) {
#ifdef FP_FAST_FMA
        result->f64[i] = fma(a->f64[i], b->f64[i], c->f64[i]);
#else
        result->f64[i] = a->f64[i] * b->f64[i] + c->f64[i];
#endif
    }
}

void __wasm_f64x2_relaxed_nmadd(v128_t *result, v128_t *a, v128_t *b, v128_t *c) {
    for (int i = 0; i < 2; i++) {
#ifdef FP_FAST_FMA
        result->f64[i] = fma(-a->f64[i], b->f64[i], c->f64[i]);
#else
        result->f64[i] = -(a->f64[i] * b->f64[i]) + c->f64[i];
#endif
    }
}

/* ---- Relaxed Truncations ---- */

void __wasm_i32x4_relaxed_trunc_f32x4_s(v128_t *result, v128_t *a) {
    for (int i = 0; i < 4; i++) {
        /* Relaxed: behavior on overflow/NaN is implementation-defined */
        float val = a->f32[i];
        if (isnan(val)) {
            result->i32[i] = 0;
        } else if (val >= 2147483648.0f) {
            result->i32[i] = 2147483647;
        } else if (val < -2147483648.0f) {
            result->i32[i] = -2147483648;
        } else {
            result->i32[i] = (int32_t)val;
        }
    }
}

void __wasm_i32x4_relaxed_trunc_f32x4_u(v128_t *result, v128_t *a) {
    for (int i = 0; i < 4; i++) {
        float val = a->f32[i];
        if (isnan(val) || val < 0.0f) {
            result->u32[i] = 0;
        } else if (val >= 4294967296.0f) {
            result->u32[i] = 4294967295U;
        } else {
            result->u32[i] = (uint32_t)val;
        }
    }
}

void __wasm_i32x4_relaxed_trunc_f64x2_s_zero(v128_t *result, v128_t *a) {
    for (int i = 0; i < 2; i++) {
        double val = a->f64[i];
        if (isnan(val)) {
            result->i32[i] = 0;
        } else if (val >= 2147483648.0) {
            result->i32[i] = 2147483647;
        } else if (val < -2147483648.0) {
            result->i32[i] = -2147483648;
        } else {
            result->i32[i] = (int32_t)val;
        }
    }
    result->i32[2] = 0;
    result->i32[3] = 0;
}

void __wasm_i32x4_relaxed_trunc_f64x2_u_zero(v128_t *result, v128_t *a) {
    for (int i = 0; i < 2; i++) {
        double val = a->f64[i];
        if (isnan(val) || val < 0.0) {
            result->u32[i] = 0;
        } else if (val >= 4294967296.0) {
            result->u32[i] = 4294967295U;
        } else {
            result->u32[i] = (uint32_t)val;
        }
    }
    result->u32[2] = 0;
    result->u32[3] = 0;
}

/* ---- Dot Products ---- */

void __wasm_i16x8_relaxed_q15mulr_s(v128_t *result, v128_t *a, v128_t *b) {
    for (int i = 0; i < 8; i++) {
        /* Q15 saturating multiply with rounding */
        int32_t product = (int32_t)a->i16[i] * (int32_t)b->i16[i];
        int32_t rounded = (product + 0x4000) >> 15;
        /* Saturate to int16 */
        if (rounded > 32767) rounded = 32767;
        if (rounded < -32768) rounded = -32768;
        result->i16[i] = (int16_t)rounded;
    }
}

void __wasm_i16x8_relaxed_dot_i8x16_i7x16_s(v128_t *result, v128_t *a, v128_t *b) {
    /* Dot product of pairs: i8 x i7 (7-bit treated as signed or unsigned) -> i16 */
    for (int i = 0; i < 8; i++) {
        int32_t sum = (int32_t)a->i8[2*i] * (int32_t)b->i8[2*i] +
                      (int32_t)a->i8[2*i+1] * (int32_t)b->i8[2*i+1];
        /* Saturate to int16 */
        if (sum > 32767) sum = 32767;
        if (sum < -32768) sum = -32768;
        result->i16[i] = (int16_t)sum;
    }
}

void __wasm_i32x4_relaxed_dot_i8x16_i7x16_add_s(v128_t *result, v128_t *a, v128_t *b, v128_t *c) {
    /* Dot product with accumulate: 4 groups of 4 i8xi7 -> i32, add to c */
    for (int i = 0; i < 4; i++) {
        int32_t sum = 0;
        for (int j = 0; j < 4; j++) {
            sum += (int32_t)a->i8[4*i+j] * (int32_t)b->i8[4*i+j];
        }
        result->i32[i] = sum + c->i32[i];
    }
}

/* ---- Basic v128 Operations (for completeness) ---- */

void __wasm_v128_load(v128_t *result, void *addr) {
    memcpy(result, addr, 16);
}

void __wasm_v128_store(void *addr, v128_t *value) {
    memcpy(addr, value, 16);
}

void __wasm_v128_const(v128_t *result, uint64_t low, uint64_t high) {
    result->u64[0] = low;
    result->u64[1] = high;
}

/* ---- WASI Function Aliases (without __wasi_ prefix) ---- */
/* WASM imports use short names like "proc_exit", not "__wasi_proc_exit" */

void proc_exit(int32_t code) {
    __wasi_proc_exit(code);
}

__wasi_errno_t args_sizes_get(uint32_t *argc_out, uint32_t *argv_buf_size_out) {
    return __wasi_args_sizes_get(argc_out, argv_buf_size_out);
}

__wasi_errno_t args_get(uint32_t argv_ptr, uint32_t argv_buf_ptr) {
    return __wasi_args_get(argv_ptr, argv_buf_ptr);
}

__wasi_errno_t environ_sizes_get(uint32_t *count_out, uint32_t *buf_size_out) {
    return __wasi_environ_sizes_get(count_out, buf_size_out);
}

__wasi_errno_t environ_get(uint32_t environ_ptr, uint32_t environ_buf_ptr) {
    return __wasi_environ_get(environ_ptr, environ_buf_ptr);
}

__wasi_errno_t fd_close(int32_t fd) {
    return __wasi_fd_close(fd);
}

__wasi_errno_t fd_write(int32_t fd, uint32_t iovs_ptr, uint32_t iovs_len, uint32_t nwritten_ptr) {
    return __wasi_fd_write(fd, iovs_ptr, iovs_len, nwritten_ptr);
}

__wasi_errno_t fd_read(int32_t fd, uint32_t iovs_ptr, uint32_t iovs_len, uint32_t nread_ptr) {
    return __wasi_fd_read(fd, iovs_ptr, iovs_len, nread_ptr);
}

__wasi_errno_t fd_seek(int32_t fd, int64_t offset, uint8_t whence, uint32_t newoffset_ptr) {
    return __wasi_fd_seek(fd, offset, whence, newoffset_ptr);
}

__wasi_errno_t fd_tell(int32_t fd, uint32_t offset_ptr) {
    return __wasi_fd_tell(fd, offset_ptr);
}

__wasi_errno_t fd_sync(int32_t fd) {
    return __wasi_fd_sync(fd);
}

__wasi_errno_t fd_fdstat_get(int32_t fd, uint32_t stat_ptr) {
    return __wasi_fd_fdstat_get(fd, stat_ptr);
}

__wasi_errno_t fd_prestat_get(int32_t fd, uint32_t prestat_ptr) {
    return __wasi_fd_prestat_get(fd, prestat_ptr);
}

__wasi_errno_t fd_prestat_dir_name(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    return __wasi_fd_prestat_dir_name(fd, path_ptr, path_len);
}

__wasi_errno_t path_open(
    int32_t fd,
    uint32_t dirflags,
    uint32_t path_ptr,
    uint32_t path_len,
    uint32_t oflags,
    uint64_t fs_rights_base,
    uint64_t fs_rights_inheriting,
    uint16_t fdflags,
    uint32_t opened_fd_ptr
) {
    return __wasi_path_open(fd, dirflags, path_ptr, path_len, oflags,
                            fs_rights_base, fs_rights_inheriting, fdflags, opened_fd_ptr);
}

__wasi_errno_t path_create_directory(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    return __wasi_path_create_directory(fd, path_ptr, path_len);
}

__wasi_errno_t path_unlink_file(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    return __wasi_path_unlink_file(fd, path_ptr, path_len);
}

__wasi_errno_t path_remove_directory(int32_t fd, uint32_t path_ptr, uint32_t path_len) {
    return __wasi_path_remove_directory(fd, path_ptr, path_len);
}

__wasi_errno_t path_rename(
    int32_t fd, uint32_t old_path_ptr, uint32_t old_path_len,
    int32_t new_fd, uint32_t new_path_ptr, uint32_t new_path_len
) {
    return __wasi_path_rename(fd, old_path_ptr, old_path_len, new_fd, new_path_ptr, new_path_len);
}

__wasi_errno_t path_filestat_get(
    int32_t fd,
    uint32_t flags,
    uint32_t path_ptr,
    uint32_t path_len,
    uint32_t filestat_ptr
) {
    return __wasi_path_filestat_get(fd, flags, path_ptr, path_len, filestat_ptr);
}

__wasi_errno_t clock_res_get(uint32_t clock_id, uint32_t resolution_ptr) {
    return __wasi_clock_res_get(clock_id, resolution_ptr);
}

__wasi_errno_t clock_time_get(uint32_t clock_id, uint64_t precision, uint32_t time_ptr) {
    return __wasi_clock_time_get(clock_id, precision, time_ptr);
}

__wasi_errno_t random_get(uint32_t buf_ptr, uint32_t buf_len) {
    return __wasi_random_get(buf_ptr, buf_len);
}

/* sched_yield conflicts with system header - skip alias */

__wasi_errno_t poll_oneoff(uint32_t in_ptr, uint32_t out_ptr, uint32_t nsubscriptions, uint32_t nevents_ptr) {
    return __wasi_poll_oneoff(in_ptr, out_ptr, nsubscriptions, nevents_ptr);
}
