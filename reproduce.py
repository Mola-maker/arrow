import gc
import json
import mmap
import resource
import struct
import sys

import pyarrow as pa


def run_case(factory, dtype, width, counter):
    boundary = 1 << 31
    length = boundary + 1 if counter == "length" else 1
    offset = boundary if counter == "offset" else 0
    null_count = boundary if counter == "null_count" else 0
    if counter == "null_count":
        length = boundary

    offsets_size = (length + offset + 1) * width
    offset_map = mmap.mmap(-1, offsets_size,
                           flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
    fmt = "<i" if width == 4 else "<q"
    struct.pack_into(fmt, offset_map, offsets_size - width, 1)
    offsets = pa.py_buffer(offset_map)
    bitmap_map = None
    bitmap = None
    if null_count:
        bitmap_map = mmap.mmap(-1, (length + 7) // 8,
                               flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
        bitmap = pa.py_buffer(bitmap_map)
    data = pa.py_buffer(b"x")

    generic = pa.Array.from_buffers(dtype, length, [bitmap, offsets, data],
                                    null_count=null_count, offset=offset)
    generic.validate()
    last = generic[-1].as_py()
    assert last == (None if null_count else "x")
    result = {
        "factory": factory.__name__, "counter": counter,
        "length": length, "offset": offset, "null_count": null_count,
        "mapped_offsets_bytes": offsets_size,
        "generic_factory": "valid", "generic_last_value": last,
    }
    try:
        specialized = factory.from_buffers(length, offsets, data,
                                           null_bitmap=bitmap,
                                           null_count=null_count, offset=offset)
        specialized.validate()
        assert len(specialized) == len(generic)
        assert specialized.offset == generic.offset
        assert specialized.null_count == generic.null_count
        assert specialized[-1].as_py() == last
        result["specialized_factory"] = "valid"
        del specialized
    except Exception as exc:
        result["specialized_factory"] = type(exc).__name__
        result["error"] = str(exc)

    del generic, offsets, bitmap, data
    gc.collect()
    offset_map.close()
    if bitmap_map is not None:
        bitmap_map.close()
    return result


results = [run_case(factory, dtype, width, counter)
           for factory, dtype, width in [(pa.StringArray, pa.string(), 4),
                                          (pa.LargeStringArray, pa.large_string(), 8)]
           for counter in ["length", "offset", "null_count"]]
report = {"python": sys.version.split()[0], "pyarrow": pa.__version__,
          "cases": results,
          "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
print(json.dumps(report, indent=2))
