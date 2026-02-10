(module
  ;; Function with a block that returns multiple values
  (func (export "wasm_main") (result i32)
    (local $sum i32)
    (local $product i32)

    ;; Block type: returns (i32, i32)
    (block (result i32 i32)
      (i32.const 5)
      (i32.const 7)
    )
    ;; Stack now has: [5, 7]
    (local.set $product)  ;; 7
    (local.set $sum)      ;; 5

    ;; Return sum + product = 5 + 7 = 12
    (i32.add (local.get $sum) (local.get $product))
  )
)
