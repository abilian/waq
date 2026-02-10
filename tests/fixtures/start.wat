(module
  ;; Global counter, mutable
  (global $counter (mut i32) (i32.const 0))

  ;; Start function - increments counter
  (func $init
    (global.set $counter (i32.add (global.get $counter) (i32.const 10)))
  )

  ;; Declare start function
  (start $init)

  ;; Export function that returns the counter value
  ;; If start worked, this should return 10
  (func (export "wasm_main") (result i32)
    (global.get $counter)
  )
)
