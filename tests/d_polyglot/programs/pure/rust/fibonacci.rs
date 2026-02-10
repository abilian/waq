// Pure WASM: Compute fibonacci(20) = 6765, return 6765 % 256 = 109
// Tests: loops, local variables

#![no_std]

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

fn fibonacci(n: i32) -> i32 {
    if n <= 1 {
        return n;
    }

    let mut a = 0i32;
    let mut b = 1i32;

    for _ in 2..=n {
        let tmp = a + b;
        a = b;
        b = tmp;
    }
    b
}

#[no_mangle]
pub extern "C" fn main() -> i32 {
    fibonacci(20) % 256 // 6765 % 256 = 109
}
