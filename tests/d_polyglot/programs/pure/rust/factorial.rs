// Pure WASM: Compute factorial(6) = 720, return 720 % 256 = 208

#![no_std]

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

fn factorial(n: i32) -> i32 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}

#[no_mangle]
pub extern "C" fn main() -> i32 {
    factorial(6) % 256  // 720 % 256 = 208
}
