(module
  ;; Import a function from "env" module
  (import "env" "add_numbers" (func $add_numbers (param i32 i32) (result i32)))

  ;; Use the imported function
  (func (export "test_import") (result i32)
    (call $add_numbers (i32.const 30) (i32.const 12))
  )
)
