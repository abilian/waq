;; Test loop: sum 1 to 10 = 55
(module
  (func $main (export "wasm_main") (result i32)
    (local $i i32)
    (local $sum i32)
    (local.set $i (i32.const 1))
    (local.set $sum (i32.const 0))
    
    (block $break
      (loop $continue
        ;; sum += i
        (local.set $sum (i32.add (local.get $sum) (local.get $i)))
        ;; i++
        (local.set $i (i32.add (local.get $i) (i32.const 1)))
        ;; if i > 10, break
        (br_if $break (i32.gt_s (local.get $i) (i32.const 10)))
        ;; continue loop
        (br $continue)
      )
    )
    (local.get $sum)
  )
)
