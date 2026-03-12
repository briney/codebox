# COMPILED.md

Supplementary guidelines for C++ and Rust development. These languages are used sparingly in this environment, typically for performance-critical inner loops, CUDA kernels, numerical algorithms, or Python extensions.

---

## C++

### Language Standard & Style

- **C++17** minimum. C++20 if the project/toolchain supports it.
- Use modern features: `std::optional`, `std::variant`, `std::string_view`, structured bindings, `if constexpr`, `std::filesystem`.
- `auto` for complex iterator types and template deductions. Spell out the type when it aids readability (especially numeric types).
- `constexpr` wherever possible for compile-time computation.
- Avoid raw pointers for ownership. Use `std::unique_ptr` (default) or `std::shared_ptr` (only when shared ownership is genuinely needed).
- No raw `new`/`delete`. RAII for all resource management.
- Prefer references over pointers for non-nullable, non-owning access.
- Use `const` aggressively: `const` references, `const` member functions, `const` variables.

### Error Handling

- Use exceptions for truly exceptional conditions. Use `std::expected` (C++23) or return codes / `std::optional` for expected failure paths.
- If the project disables exceptions (common in CUDA-heavy code): use error codes with a consistent pattern. Document which functions can fail and how.
- Never catch `(...)` silently. At minimum, log the error.

### Memory & Performance

- Prefer stack allocation over heap allocation. Use `std::array` over `std::vector` when size is known at compile time.
- Avoid unnecessary copies: pass large objects by `const&`. Use move semantics (`std::move`) when transferring ownership.
- `std::span` (C++20) for non-owning views of contiguous data. Falls back to a pointer + size pair in C++17.
- Profile before optimizing. Use `perf`, Valgrind/Callgrind, or compiler sanitizers (`-fsanitize=address,undefined`).
- For SIMD: prefer compiler auto-vectorization with appropriate flags first. Drop to intrinsics only when measured performance warrants it.

### CUDA (when applicable)

- Separate host and device code clearly. Use `.cu` extension for files with kernels.
- Always check CUDA API return codes. Use a macro/wrapper:
  ```cpp
  #define CUDA_CHECK(call) do { \
      cudaError_t err = call; \
      if (err != cudaSuccess) { /* handle error */ } \
  } while(0)
  ```
- Prefer managed memory (`cudaMallocManaged`) for prototyping. Use explicit `cudaMemcpy` for production performance-critical paths.
- Document grid/block dimensions and shared memory usage.
- Use CUDA streams for concurrent kernel execution and overlap of compute/transfer.

### Python Bindings (pybind11)

- **pybind11** is the default for C++ → Python bindings.
- Keep the binding layer thin: one `bindings.cpp` file that wraps the C++ API. Don't put logic in the binding code.
- Use NumPy array bindings (`py::array_t<double>`) for bulk data transfer. Avoid copying — use `py::array::c_style | py::array::forcecast` for zero-copy where possible.
- Expose only what Python needs. Don't bind internal implementation classes.
- Add docstrings to bound functions: `py::arg("name")` and `.doc()`.
- Build with `scikit-build-core` or `meson-python` via `pyproject.toml`. Avoid raw `setup.py` + CMake hacks.
- Test the bindings from Python (pytest), not from C++ — the Python interface is what matters.

### Build System

- **CMake** (3.20+). Use modern CMake: targets and properties, not global variables.
- `target_link_libraries` with visibility (`PUBLIC`, `PRIVATE`, `INTERFACE`).
- Don't use `GLOB` for source files — list them explicitly.
- Use `FetchContent` or `find_package` for dependencies. No vendored copies unless strictly necessary.
- Presets (`CMakePresets.json`) for common configurations (Debug, Release, CUDA-enabled).
- For Python extensions: prefer `scikit-build-core` to drive CMake from `pyproject.toml`.

### Formatting & Linting

- **clang-format** with the project's `.clang-format` file. If none exists, use LLVM style with these overrides:
  ```yaml
  BasedOnStyle: LLVM
  ColumnLimit: 100
  IndentWidth: 4
  ```
- **clang-tidy** for static analysis. Enable `modernize-*`, `bugprone-*`, `performance-*` checks.
- Compiler warnings: `-Wall -Wextra -Wpedantic`. Treat warnings as errors in CI (`-Werror`).

### Testing

- **Google Test** (gtest) + **Google Benchmark** for microbenchmarks.
- Test at the API boundary, not internal functions. Mirror the Python test strategy: does the function produce correct results for known inputs?
- For numerical code: use approximate comparisons with documented tolerances.

---

## Rust

### Language & Style

- Latest stable Rust. Update toolchain regularly.
- `cargo fmt` on every save. `cargo clippy` with warnings as errors: `#![deny(clippy::all)]`.
- Prefer `clippy::pedantic` for library code. Selectively `#[allow(...)]` with justification comments.
- Use the type system: `enum` over stringly-typed alternatives. Newtypes for domain-specific wrappers (e.g., `struct SequenceLength(usize)`).
- Prefer `impl Trait` in argument position for simple generics. Use explicit type parameters when the generic appears multiple times or in return position.

### Error Handling

- **Library code**: define error types with `thiserror`. Each public module should have its own `Error` enum.
  ```rust
  #[derive(Debug, thiserror::Error)]
  pub enum ParseError {
      #[error("invalid FASTA header at line {line}")]
      InvalidHeader { line: usize },
      #[error("unexpected character '{ch}' in sequence")]
      InvalidCharacter { ch: char },
  }
  ```
- **Application / script code**: use `anyhow` for convenience. `anyhow::Context` for adding context to errors.
- Never `unwrap()` in library code. `expect("reason")` is acceptable in application code only when the invariant is genuinely guaranteed and documented.
- Use `?` operator for propagation. Keep error chains intact.

### Memory & Performance

- Default to stack allocation. Use `Box` only when you need heap allocation or trait objects.
- Prefer `&str` over `String` in function arguments. Accept `impl AsRef<str>` when flexibility is needed.
- Use iterators and zero-copy parsing wherever possible. `&[u8]` for binary data.
- Avoid `clone()` unless necessary. If cloning frequently, reconsider the ownership model.
- For numerical/scientific work: `ndarray` for multi-dimensional arrays, `rayon` for data parallelism.
- Profile with `cargo flamegraph` or `perf`. Benchmark with `criterion`.

### Python Bindings (PyO3)

- **PyO3 + maturin** for Rust → Python extensions.
- Build with `maturin develop` during development, `maturin build --release` for distribution.
- Use `numpy` feature of PyO3 for NumPy array interop. Avoid unnecessary data copies across the FFI boundary.
- Expose a clean Python API: Pythonic naming (`snake_case`), proper docstrings, type stub generation.
- Structure:
  ```
  my-extension/
  ├── Cargo.toml
  ├── pyproject.toml        # maturin build config
  ├── src/
  │   ├── lib.rs            # PyO3 module definition
  │   └── core.rs           # Pure Rust logic (no PyO3 deps)
  └── python/
      └── my_extension/
          ├── __init__.py
          └── py.typed       # PEP 561 marker
  ```
- Keep pure Rust logic separate from PyO3 bindings. The `core.rs` (or `core/` module) should be testable without Python.
- Test from Python side (pytest) for integration. Test pure Rust logic with `#[cfg(test)]` modules.

### Unsafe Code

- Minimize `unsafe`. Isolate it in small, well-documented functions.
- Every `unsafe` block requires a `// SAFETY:` comment explaining why the invariants are upheld:
  ```rust
  // SAFETY: `ptr` is guaranteed non-null and aligned by the allocator,
  // and we have exclusive access via the mutable borrow on `self`.
  unsafe { *ptr = value; }
  ```
- Prefer safe abstractions: `std::sync`, `crossbeam`, `parking_lot` over raw atomics/mutexes.
- Run `miri` (`cargo +nightly miri test`) on unsafe code when feasible.

### Project Structure

```
project-name/
├── Cargo.toml
├── src/
│   ├── lib.rs              # Public API
│   ├── main.rs             # Binary entry point (if applicable)
│   └── module/
│       ├── mod.rs
│       └── submodule.rs
├── tests/                  # Integration tests
├── benches/                # Criterion benchmarks
└── examples/               # Usage examples
```

### Dependencies

- Vet dependencies before adding. Prefer well-maintained, widely-used crates.
- Pin versions in `Cargo.lock` (committed for binaries and extensions, not for libraries).
- `cargo audit` in CI for vulnerability scanning.
- Keep the dependency tree lean — transitive dependencies matter for compile time and security surface.

---

## Cross-Language Integration Patterns

When C++ or Rust code exists to accelerate a Python workflow, follow these patterns:

### API Design

- Design the Python interface first, then implement the native code to match.
- The native code should do one thing well: a hot inner loop, a parsing/serialization step, a numerical kernel. Don't reimplement orchestration logic that Python handles fine.
- Accept and return NumPy arrays / Python primitives at the boundary. Don't force Python callers to work with foreign types.

### Build & Distribution

- All native extensions build via `pyproject.toml`. The Python package manager (`pip`, `uv`) should be the only build command a user runs.
- CI builds wheels for common platforms (Linux x86_64, macOS arm64 at minimum).
- Provide a pure-Python fallback when feasible (slower but functional), guarded by an import check.

### Testing

- Primary tests live in Python (pytest). They test the public API that users actually call.
- Native-side unit tests (gtest / `#[test]`) cover internal logic and edge cases that are awkward to test through Python.
- Benchmark both the Python interface overhead and the raw native performance.
