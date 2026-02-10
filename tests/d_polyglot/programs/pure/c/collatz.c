// Pure WASM: Compute Collatz sequence length for n=27 = 111 steps
// Tests: loops, conditionals, division

static int collatz_length(int start) {
    long long n = start; // Use 64-bit to avoid overflow
    int steps = 0;

    while (n != 1) {
        if (n % 2 == 0) {
            n /= 2;
        } else {
            n = 3 * n + 1;
        }
        steps++;
    }
    return steps;
}

__attribute__((export_name("main")))
int main(void) {
    // n=27 has 111 steps (longest for n < 100)
    return collatz_length(27) % 256; // 111
}
