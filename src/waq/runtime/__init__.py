"""Runtime library support for WASM execution."""

from __future__ import annotations

# Runtime function declarations that need to be linked
RUNTIME_FUNCTIONS = [
    # Integer intrinsics
    "__wasm_i32_clz",
    "__wasm_i32_ctz",
    "__wasm_i32_popcnt",
    "__wasm_i64_clz",
    "__wasm_i64_ctz",
    "__wasm_i64_popcnt",
    # Float intrinsics
    "__wasm_f32_abs",
    "__wasm_f32_ceil",
    "__wasm_f32_floor",
    "__wasm_f32_trunc",
    "__wasm_f32_nearest",
    "__wasm_f32_sqrt",
    "__wasm_f32_min",
    "__wasm_f32_max",
    "__wasm_f32_copysign",
    "__wasm_f64_abs",
    "__wasm_f64_ceil",
    "__wasm_f64_floor",
    "__wasm_f64_trunc",
    "__wasm_f64_nearest",
    "__wasm_f64_sqrt",
    "__wasm_f64_min",
    "__wasm_f64_max",
    "__wasm_f64_copysign",
    # Traps
    "__wasm_trap_unreachable",
    "__wasm_trap_div_by_zero",
    "__wasm_trap_integer_overflow",
    "__wasm_trap_invalid_conversion",
    "__wasm_trap_out_of_bounds",
    # Memory
    "__wasm_memory_grow",
    "__wasm_memory_size",
]

__all__ = ["RUNTIME_FUNCTIONS"]
