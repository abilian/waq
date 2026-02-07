;; Simple test: return constant 42
(module
  (func $main (export "wasm_main") (result i32)
    i32.const 42
  )
)
