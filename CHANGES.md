# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026/02/10

### Added

**WASM 3.0 Support:**
- Memory64: 64-bit memory addressing for large address spaces
- Multiple memories: support for multiple memory instances per module
- Tail calls: `return_call`, `return_call_indirect`, `return_call_ref`
  - Self-recursive tail calls optimized to loops
  - Other tail calls compiled as call + return
- Exception handling: `try`, `catch`, `throw`, `rethrow`, `delegate`, `catch_all`
  - Runtime support via setjmp/longjmp
- Typed function references: `call_ref`, `return_call_ref`
- Garbage collection:
  - Struct types: `struct.new`, `struct.new_default`, `struct.get`, `struct.get_s`, `struct.get_u`, `struct.set`
  - Array types: `array.new`, `array.new_default`, `array.new_fixed`, `array.get`, `array.get_s`, `array.get_u`, `array.set`, `array.len`
  - Reference operations: `ref.test`, `ref.cast`, `ref.i31`, `i31.get_s`, `i31.get_u`
  - Arena allocator runtime for GC objects
- Relaxed SIMD: scalar fallback implementation for all relaxed SIMD operations
- Deterministic profile: canonical NaN support (`0x7FC00000` for f32, `0x7FF8000000000000` for f64)

**WASI Preview 1 Support:**
- File descriptors: `fd_read`, `fd_write`, `fd_close`, `fd_seek`, `fd_tell`, `fd_sync`, `fd_fdstat_get`, `fd_fdstat_set_flags`, `fd_prestat_get`, `fd_prestat_dir_name`
- Filesystem: `path_open`, `path_create_directory`, `path_remove_directory`, `path_unlink_file`, `path_rename`, `path_readlink`, `path_filestat_get`
- Args/Environment: `args_get`, `args_sizes_get`, `environ_get`, `environ_sizes_get`
- Clock: `clock_time_get`, `clock_res_get`
- Process: `proc_exit`, `proc_raise`, `sched_yield`
- Random: `random_get`

**Testing:**
- Test coverage improved to 87% (355 tests)
- Added tests for multi-value calls, tail calls, GC extended operations
- Registered pytest markers (unit, integration, e2e)

### Fixed

- Fixed opcode routing for `return_call_ref` (0x15) to control instruction compiler
- Fixed type narrowing for `FuncType` when accessing module types
- Fixed `Store` instruction type argument (use string `"l"` instead of `BaseType.LONG`)
- Fixed None checks for control frame labels in exception handling
- Fixed None checks for phi node labels in if/else with results


## [0.1.1] - 2026/02/07

### Added

- New `--emit asm` option to output assembly code
- New `--emit obj` option to output object files
- New `--emit exe` option to output standalone executables
- New `--entry` flag to specify entry function for executables (default: `wasm_main`)
- New `--no-print` flag for void entry functions or when output should be suppressed
- C runtime library (`src/waq/runtime/waq_runtime.c`) with:
  - Integer intrinsics (clz, ctz, popcnt for i32/i64)
  - Float intrinsics (abs, ceil, floor, trunc, nearest, sqrt, min, max, copysign for f32/f64)
  - Trap handlers (unreachable, div-by-zero, integer overflow, invalid conversion, out-of-bounds)
  - Memory operations (grow, size)


## [0.1.0] - 2026/02/07

Initial release.

