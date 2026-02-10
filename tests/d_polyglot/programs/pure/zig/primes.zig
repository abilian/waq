// Pure WASM: Count primes up to 100 = 25
// Tests: nested loops, conditionals

fn is_prime(n: i32) bool {
    if (n < 2) return false;
    if (n == 2) return true;
    if (@mod(n, 2) == 0) return false;

    var i: i32 = 3;
    while (i * i <= n) : (i += 2) {
        if (@mod(n, i) == 0) return false;
    }
    return true;
}

fn count_primes(limit: i32) i32 {
    var count: i32 = 0;
    var n: i32 = 2;
    while (n <= limit) : (n += 1) {
        if (is_prime(n)) count += 1;
    }
    return count;
}

export fn main() i32 {
    return count_primes(100); // 25 primes up to 100
}
