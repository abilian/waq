// Pure WASM: Compute fibonacci(20) = 6765, return 6765 % 256 = 109
// Tests: loops, local variables

fn fibonacci(n: i32) i32 {
    if (n <= 1) return n;

    var a: i32 = 0;
    var b: i32 = 1;
    var i: i32 = 2;

    while (i <= n) : (i += 1) {
        const tmp = a + b;
        a = b;
        b = tmp;
    }
    return b;
}

export fn main() i32 {
    return @mod(fibonacci(20), 256); // 6765 % 256 = 109
}
