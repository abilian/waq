// Pure WASM: Count primes up to 100 = 25
// Tests: nested loops, conditionals

#![no_std]

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}

fn is_prime(n: i32) -> bool {
    if n < 2 {
        return false;
    }
    if n == 2 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }

    let mut i = 3;
    while i * i <= n {
        if n % i == 0 {
            return false;
        }
        i += 2;
    }
    true
}

fn count_primes(limit: i32) -> i32 {
    let mut count = 0;
    for n in 2..=limit {
        if is_prime(n) {
            count += 1;
        }
    }
    count
}

#[no_mangle]
pub extern "C" fn main() -> i32 {
    count_primes(100) // 25 primes up to 100
}
