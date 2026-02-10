// Pure WASM: Compute factorial(6) = 720, return 720 % 256 = 208

fn factorial(n: i32) i32 {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

export fn main() i32 {
    return @mod(factorial(6), 256); // 720 % 256 = 208
}
