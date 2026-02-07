;; Test global variables
(module
  (global $counter (mut i32) (i32.const 0))
  
  (func $increment (result i32)
    (global.set $counter (i32.add (global.get $counter) (i32.const 1)))
    (global.get $counter)
  )
  
  (func $main (export "wasm_main") (result i32)
    (drop (call $increment))  ;; counter = 1
    (drop (call $increment))  ;; counter = 2
    (drop (call $increment))  ;; counter = 3
    (call $increment)         ;; counter = 4, return 4
  )
)
