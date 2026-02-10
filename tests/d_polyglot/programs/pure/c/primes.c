// Pure WASM: Count primes up to 100 = 25
// Tests: nested loops, conditionals

static int is_prime(int n) {
    if (n < 2) return 0;
    if (n == 2) return 1;
    if (n % 2 == 0) return 0;

    for (int i = 3; i * i <= n; i += 2) {
        if (n % i == 0) return 0;
    }
    return 1;
}

static int count_primes(int limit) {
    int count = 0;
    for (int n = 2; n <= limit; n++) {
        if (is_prime(n)) count++;
    }
    return count;
}

__attribute__((export_name("main")))
int main(void) {
    return count_primes(100); // 25 primes up to 100
}
