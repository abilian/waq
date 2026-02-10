// Pure WASM: Compute factorial(6) = 720, return 720 % 256 = 208

static int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

__attribute__((export_name("main")))
int main(void) {
    return factorial(6) % 256;  // 720 % 256 = 208
}
