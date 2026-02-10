// Pure WASM: Compute gcd(48, 18) = 6
// Tests: loops, conditionals, modulo

static int gcd(int a, int b) {
    while (b != 0) {
        int tmp = a % b;
        a = b;
        b = tmp;
    }
    return a;
}

__attribute__((export_name("main")))
int main(void) {
    // gcd(48, 18) = 6
    // Also test with larger numbers: gcd(252, 105) = 21
    // Return sum: 6 + 21 = 27
    return gcd(48, 18) + gcd(252, 105);
}
