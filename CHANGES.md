# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [VERSION] - DATE

### Changed

### Fixed

### Documentation


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

