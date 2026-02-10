// Pure WASM: Compute fibonacci(20) = 6765, return 6765 % 256 = 109
// Tests: loops, local variables

__attribute__((export_name("main")))
int main(void) {
    int n = 20;
    if (n <= 1) return n;

    int a = 0;
    int b = 1;

    for (int i = 2; i <= n; i++) {
        int tmp = a + b;
        a = b;
        b = tmp;
    }
    return b % 256; // 6765 % 256 = 109
}
