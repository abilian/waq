;; Test memory: store and load
(module
  (memory 1)
  
  (func $main (export "wasm_main") (result i32)
    ;; Store 42 at address 0
    (i32.store (i32.const 0) (i32.const 42))
    ;; Store 58 at address 4
    (i32.store (i32.const 4) (i32.const 58))
    ;; Load both and add them (42 + 58 = 100)
    (i32.add
      (i32.load (i32.const 0))
      (i32.load (i32.const 4))
    )
  )
)
