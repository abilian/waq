// Pure WASM: Compute gcd(48, 18) = 6
// Tests: loops, conditionals, modulo

fn gcd(a_in: i32, b_in: i32) i32 {
    var a = a_in;
    var b = b_in;

    while (b != 0) {
        const tmp = @mod(a, b);
        a = b;
        b = tmp;
    }
    return a;
}

export fn main() i32 {
    // gcd(48, 18) = 6
    // Also test with larger numbers: gcd(252, 105) = 21
    // Return sum: 6 + 21 = 27
    return gcd(48, 18) + gcd(252, 105);
}
