// Pure WASM: Test bit operations
// Tests: and, or, xor, shifts, popcount

static int popcount(unsigned int x) {
    int count = 0;
    while (x != 0) {
        count += x & 1;
        x >>= 1;
    }
    return count;
}

__attribute__((export_name("main")))
int main(void) {
    unsigned int a = 0xCA; // 0b11001010 = 202
    unsigned int b = 0xAC; // 0b10101100 = 172

    // AND: 0b10001000 = 136
    int and_result = a & b;

    // OR: 0b11101110 = 238
    int or_result = a | b;

    // XOR: 0b01100110 = 102
    int xor_result = a ^ b;

    // Right shift: 202 >> 3 = 25
    int rshift = a >> 3;

    // Popcount of 0b11001010 = 4
    int pop = popcount(a);

    // Return a checksum that fits in exit code
    // (136 + 238 + 102 + 25 + 4) % 256 = 505 % 256 = 249
    return (and_result + or_result + xor_result + rshift + pop) % 256;
}
