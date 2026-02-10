// Pure WASM: Compute Collatz sequence length for n=27 = 111 steps
// Tests: loops, conditionals, division

#![no_std]

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

fn collatz_length(start: i32) -> i32 {
    let mut n: i64 = start as i64; // Use i64 to avoid overflow
    let mut steps: i32 = 0;

    while n != 1 {
        if n % 2 == 0 {
            n /= 2;
        } else {
            n = 3 * n + 1;
        }
        steps += 1;
    }
    steps
}

#[no_mangle]
pub extern "C" fn main() -> i32 {
    // n=27 has 111 steps (longest for n < 100)
    collatz_length(27) % 256 // 111
}
