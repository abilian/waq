(module
  ;; Function that returns two values: (a+b, a*b)
  (func $add_and_mul (param $a i32) (param $b i32) (result i32 i32)
    (i32.add (local.get $a) (local.get $b))
    (i32.mul (local.get $a) (local.get $b))
  )

  ;; Function that calls add_and_mul and returns sum of both results
  (func (export "wasm_main") (result i32)
    (local $sum i32)
    (local $product i32)
    ;; Call add_and_mul(3, 4) -> returns (7, 12)
    (call $add_and_mul (i32.const 3) (i32.const 4))
    (local.set $product)  ;; second result (12)
    (local.set $sum)      ;; first result (7)
    ;; Return sum + product = 7 + 12 = 19
    (i32.add (local.get $sum) (local.get $product))
  )
)
