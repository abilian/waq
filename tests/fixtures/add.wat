;; Test addition: 10 + 32 = 42
(module
  (func $main (export "wasm_main") (result i32)
    i32.const 10
    i32.const 32
    i32.add
  )
)
