// Pure WASM: Compute gcd(48, 18) = 6
// Tests: loops, conditionals, modulo

#![no_std]

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

fn gcd(mut a: i32, mut b: i32) -> i32 {
    while b != 0 {
        let tmp = a % b;
        a = b;
        b = tmp;
    }
    a
}

#[no_mangle]
pub extern "C" fn main() -> i32 {
    // gcd(48, 18) = 6
    // Also test with larger numbers: gcd(252, 105) = 21
    // Return sum: 6 + 21 = 27
    gcd(48, 18) + gcd(252, 105)
}
