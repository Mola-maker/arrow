### Describe the bug, including details regarding any error messages, version, and platform.

`StringArray.from_buffers()` and `LargeStringArray.from_buffers()` reject valid 64-bit array counters with `OverflowError: value too large to convert to int`. Their `length`, `null_count` and `offset` arguments are declared as C `int`, although the underlying Arrow `ArrayData` counters are `int64_t` and `Array.from_buffers()` accepts the same buffers.

Minimal example isolating an offset above INT32_MAX (64-bit POSIX; the mapping reserves address space without materializing billions of strings):

```python
import mmap
import struct
import pyarrow as pa

offset = 2**31
mapping = mmap.mmap(-1, (offset + 2) * 8,
                    flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
struct.pack_into("<q", mapping, (offset + 1) * 8, 1)
offsets = pa.py_buffer(mapping)
data = pa.py_buffer(b"x")

array = pa.Array.from_buffers(pa.large_string(), 1, [None, offsets, data],
                             null_count=0, offset=offset)
assert array[0].as_py() == "x"  # valid, expected

pa.LargeStringArray.from_buffers(1, offsets, data,
                                null_count=0, offset=offset)
# OverflowError: value too large to convert to int
```

The same mismatch occurs for `StringArray`, and for valid arrays with lengths or null counts above INT32_MAX. Verified on PyArrow 26.0.0, Ubuntu/Python 3.12.14 and native Arch/Python 3.14.8. Rebuilding the original Python binding from current upstream source reproduces all six factory/counter cases. Generic controls can read the actual final values. Peak process RSS in these sparse-buffer checks is about 57–79 MiB.

Widening all three counters to `int64_t` in both helpers makes the specialized factories accept the same valid arrays. Normal string/binary buffer round-trips, six new regressions, and the array test module pass in both environments. There is no buffer-layout change.

Existing issue/PR searches found #49717 (buffer safety documentation) and historical #1772; neither addresses these counter widths. This report, reproduction and candidate patch were prepared with Codex and independently AI-reviewed; no human review is claimed.

### Component(s)

Python
