;; Test local variables
(module
  (func $main (export "wasm_main") (result i32)
    (local $a i32)
    (local $b i32)
    (local.set $a (i32.const 10))
    (local.set $b (i32.const 20))
    (i32.add (local.get $a) (local.get $b))
  )
)
