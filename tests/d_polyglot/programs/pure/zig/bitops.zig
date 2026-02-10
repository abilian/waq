// Pure WASM: Test bit operations
// Tests: and, or, xor, shifts, popcount

fn popcount(x: u32) i32 {
    var n = x;
    var count: i32 = 0;
    while (n != 0) {
        count += @as(i32, @intCast(n & 1));
        n >>= 1;
    }
    return count;
}

export fn main() i32 {
    const a: u32 = 0b11001010; // 202
    const b: u32 = 0b10101100; // 172

    // AND: 0b10001000 = 136
    const and_result = a & b;

    // OR: 0b11101110 = 238
    const or_result = a | b;

    // XOR: 0b01100110 = 102
    const xor_result = a ^ b;

    // Right shift: 202 >> 3 = 25
    const rshift = a >> 3;

    // Popcount of 0b11001010 = 4
    const pop = popcount(a);

    // Return a checksum that fits in exit code
    // (136 + 238 + 102 + 25 + 4) % 256 = 505 % 256 = 249
    return @mod(@as(i32, @intCast(and_result)) +
                @as(i32, @intCast(or_result)) +
                @as(i32, @intCast(xor_result)) +
                @as(i32, @intCast(rshift)) +
                pop, 256);
}
