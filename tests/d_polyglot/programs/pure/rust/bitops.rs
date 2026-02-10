// Pure WASM: Test bit operations
// Tests: and, or, xor, shifts, popcount

#![no_std]

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

fn popcount(mut x: u32) -> i32 {
    let mut count: i32 = 0;
    while x != 0 {
        count += (x & 1) as i32;
        x >>= 1;
    }
    count
}

#[no_mangle]
pub extern "C" fn main() -> i32 {
    let a: u32 = 0b11001010; // 202
    let b: u32 = 0b10101100; // 172

    // AND: 0b10001000 = 136
    let and_result = a & b;

    // OR: 0b11101110 = 238
    let or_result = a | b;

    // XOR: 0b01100110 = 102
    let xor_result = a ^ b;

    // Right shift: 202 >> 3 = 25
    let rshift = a >> 3;

    // Popcount of 0b11001010 = 4
    let pop = popcount(a);

    // Return a checksum that fits in exit code
    // (136 + 238 + 102 + 25 + 4) % 256 = 505 % 256 = 249
    ((and_result as i32) + (or_result as i32) + (xor_result as i32) +
     (rshift as i32) + pop) % 256
}
