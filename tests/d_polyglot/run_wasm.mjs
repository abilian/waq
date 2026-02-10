#!/usr/bin/env node
/**
 * Node.js WASM/WASI runner for polyglot tests.
 *
 * Usage:
 *   node run_wasm.mjs <wasm_file> --mode pure --func <func_name>
 *   node run_wasm.mjs <wasm_file> --mode wasi
 */

import { readFileSync } from 'fs';
import { WASI } from 'wasi';
import { argv, exit } from 'process';

function parseArgs(args) {
    const result = {
        wasmPath: null,
        mode: 'pure',
        func: 'main',
    };

    let i = 2; // Skip node and script name
    while (i < args.length) {
        const arg = args[i];
        if (arg === '--mode') {
            result.mode = args[++i];
        } else if (arg === '--func') {
            result.func = args[++i];
        } else if (!arg.startsWith('-')) {
            result.wasmPath = arg;
        }
        i++;
    }

    return result;
}

async function runPureWasm(wasmPath, funcName) {
    const wasmBuffer = readFileSync(wasmPath);
    const wasmModule = await WebAssembly.compile(wasmBuffer);

    // Analyze imports to determine what we need to provide
    const imports = WebAssembly.Module.imports(wasmModule);
    const importObject = {};

    for (const imp of imports) {
        if (!importObject[imp.module]) {
            importObject[imp.module] = {};
        }
        if (imp.kind === 'memory') {
            importObject[imp.module][imp.name] = new WebAssembly.Memory({ initial: 1, maximum: 10 });
        } else if (imp.kind === 'table') {
            importObject[imp.module][imp.name] = new WebAssembly.Table({ initial: 0, element: 'anyfunc' });
        } else if (imp.kind === 'global') {
            importObject[imp.module][imp.name] = new WebAssembly.Global({ value: 'i32', mutable: true }, 0);
        } else if (imp.kind === 'function') {
            importObject[imp.module][imp.name] = () => {};
        }
    }

    const instance = await WebAssembly.instantiate(wasmModule, importObject);

    const func = instance.exports[funcName];
    if (typeof func !== 'function') {
        console.error(`Export '${funcName}' is not a function`);
        exit(1);
    }

    const result = func();

    // Exit with the return value (mod 256 for exit code compatibility)
    if (typeof result === 'number') {
        exit(result & 0xff);
    } else {
        exit(0);
    }
}

async function runWasiWasm(wasmPath) {
    const wasi = new WASI({
        version: 'preview1',
        args: [wasmPath],
        env: {},
        preopens: {},
    });

    const wasmBuffer = readFileSync(wasmPath);
    const wasmModule = await WebAssembly.compile(wasmBuffer);
    const instance = await WebAssembly.instantiate(wasmModule, wasi.getImportObject());

    try {
        const exitCode = wasi.start(instance);
        exit(exitCode);
    } catch (err) {
        // WASI programs may throw on exit
        if (err.code !== undefined) {
            exit(err.code);
        }
        throw err;
    }
}

async function main() {
    const args = parseArgs(argv);

    if (!args.wasmPath) {
        console.error('Usage: node run_wasm.mjs <wasm_file> --mode <pure|wasi> [--func <name>]');
        exit(1);
    }

    try {
        if (args.mode === 'pure') {
            await runPureWasm(args.wasmPath, args.func);
        } else if (args.mode === 'wasi') {
            await runWasiWasm(args.wasmPath);
        } else {
            console.error(`Unknown mode: ${args.mode}`);
            exit(1);
        }
    } catch (err) {
        console.error(`Error: ${err.message}`);
        exit(1);
    }
}

main();
