// Pure WASM: Compute Collatz sequence length for n=27 = 112 steps
// Tests: loops, conditionals, division

fn collatz_length(start: i32) i32 {
    var n: i64 = start; // Use i64 to avoid overflow
    var steps: i32 = 0;

    while (n != 1) {
        if (@mod(n, 2) == 0) {
            n = @divTrunc(n, 2);
        } else {
            n = 3 * n + 1;
        }
        steps += 1;
    }
    return steps;
}

export fn main() i32 {
    // n=27 has 111 steps (longest for n < 100)
    // Return modulo 256 to fit in exit code
    return @mod(collatz_length(27), 256); // 111
}
