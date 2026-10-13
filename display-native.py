from contextlib import redirect_stdout
import hashlib
import io
from pathlib import Path
import platform
import runpy
import sys

import pyarrow

phase = sys.argv[1]
assert phase in ('before', 'after')
root = Path('/home/omarchy/arrow-string-validation')
with redirect_stdout(io.StringIO()):
    namespace = runpy.run_path(str(root/'repro_arrow_string_buffer_counters.py'))
report = namespace['report']
expected = 'OverflowError' if phase == 'before' else 'valid'
assert all(c['generic_factory'] == 'valid' and c['specialized_factory'] == expected
           for c in report['cases'])
print(f'APACHE ARROW - NATIVE SOURCE VALIDATION: {phase.upper()}')
print(f'Python {report["python"]} | PyArrow {report["pyarrow"]} | {platform.machine()}')
print('Real private mmap buffers; actual final values read by Arrow.')
print()
print(f'{"Factory":<19} {"Counter":<11} {"Value":<12} {"Generic":<9} Specialized')
print('-' * 76)
for case in report['cases']:
    value = case[case['counter']]
    print(f'{case["factory"]:<19} {case["counter"]:<11} {value:<12} '
          f'{case["generic_factory"]:<9} {case["specialized_factory"]}')
print()
valid = sum(c['specialized_factory'] == 'valid' for c in report['cases'])
print(f'Generic controls: 6/6 valid | Specialized factories: {valid}/6 valid')
print(f'Peak process RSS: {report["peak_rss_kib"] / 1024:.1f} MiB')
print('Native source-built pyarrow.lib SHA256:')
print(hashlib.sha256(Path(pyarrow.lib.__file__).read_bytes()).hexdigest())
print()
input('Press Enter to close this validation terminal. ')
