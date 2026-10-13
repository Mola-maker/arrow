# Arrow string buffer factory counter validation

Issue: [apache/arrow#53519](https://github.com/apache/arrow/issues/53519). Fix commit: `d702b7df76ade0d6f5523920470509a82d9caa7d`, based on `875cd2ed9b2be520f7af74f9b4badd2b70b28f39`.

`StringArray.from_buffers` and `LargeStringArray.from_buffers` used C `int` for length, null_count and offset, rejecting valid counters above INT32_MAX. The generic `Array.from_buffers` already accepts the same buffers using 64-bit Arrow ArrayData counters. The fix uses `int64_t` for all three arguments in both helpers. String offset-buffer layouts remain 32-bit and 64-bit respectively.

## Actual runtime verification

| Environment | Original source binding | Fixed source binding | Focused tests | Array module |
| --- | --- | --- | --- | --- |
| Ubuntu, Python 3.12.14, GCC 15.2 | 6 specialized OverflowErrors; 6 valid generic controls | 6 valid specialized arrays, correct final values | 8 passed | 332 passed, 40 skipped |
| Arch/Omarchy, Python 3.14.8, GCC 16.2.1 | 6 specialized OverflowErrors; 6 valid generic controls | 6 valid specialized arrays, correct final values | 8 passed | 332 passed, 40 skipped |

Both original and candidate `pyarrow.lib` bindings were compiled from upstream source using Cython 3.3.0 against the official PyArrow 26.0.0 C++ SDK. The entire C++ SDK was not rebuilt. All 29 packaged pxd ABI descriptions matched the source in both environments. The Python subtree is byte-identical between the baseline build's `9b34c4a` and the updated PR base `875cd2e`; the intervening main update adds unrelated Parquet encoding support.

The new regressions exercise both factories and each large counter with genuine sparse, zero-filled private anonymous mappings. The final offset points to an actual `x` byte; the nullable case has a real zero-filled bitmap and returns None. The generic controls validate successfully and read the final value. These are valid Arrow buffers, with no mocked constructors or forged buffer lengths. Virtual mappings reserve about 8–16 GiB while the measured Arrow process RSS remains about 57–79 MiB. Tests use the existing `large_memory` group and run explicitly with `PYARROW_TEST_LARGE_MEMORY=1`; normal array-module runs retain the default skips.

The graphical validation uses the official disposable Omarchy edge image `omarchy-edge-2026.10.12.442.qcow2` (SHA256 `7ed0bd351861bce80c43434a9fb48fe6058dc12dbdb0bde2b14e59d7fe9d4110`), QEMU/KVM and 2 CPUs. The guest advertises 24 GiB RAM to provide enough commit allowance for the sparse mappings; its memory policy was unchanged. Runtime installation is confined to the guest user's virtual environment. `dependency-install.log`, `pip-bootstrap.log`, `dependencies-python.json` and `dependencies-system.txt` record installation from official PyPI and the exact native versions. The independent Ubuntu environment used the host's configured PyPI mirror; `host-dependency-install.log` records this.

`before.png` and `after.png` are unedited native outputs of `omarchy capture screenshot fullscreen save`. The displayed terminal program reruns `reproduce.py` against the actually loaded source-built binding and prints the real results and binding SHA256. It is not a rendered imitation. Initial setup notifications from the disposable Omarchy image appear in the screenshots.

## Evidence files

- `before.json` / `after.json`: native source-built results.
- `host-before.json` / `host-after.json`: independent Ubuntu source-built results.
- `native-red-tests.log`: all six new regressions fail against original native source.
- `native-focused-tests.log` / `host-focused-tests.log`: all eight focused checks pass.
- `native-array-suite.log` / `host-array-suite.log`: complete array-module runs and explicit skip counts.
- `build-*.log` / `host-build-*.log`: compilation logs.
- `source-sdk.json` / `host-source-sdk.json`: exact ABI-description comparison.
- `reproduce.py`, `build-binding.py`, `display-native.py`: reproduction, source build and screenshot display programs.
- `duplicate-final.json`: final search returns only safety-documentation issue #49717 and historical generic-factory PR #1772; neither fixes counter widths. Additional from_buffers/offset PR searches found only unrelated closed work.
- `review.txt`: independent Codex review, including valid mmap layouts/lifetime and platform-safe optional imports. No human review is claimed.

Only two source files change in the PR. No runtime dependency is added. Git diff whitespace checks pass. No credentials, temporary SSH keys or VM overlays are published here.
