import argparse
import json
from pathlib import Path
import resource
import signal
import subprocess
import sys

import pyarrow as pa

SETUP = """
import resource
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
import pyarrow as pa
import pyarrow.parquet as pq
sink = pa.BufferOutputStream()
pq.write_table(pa.table({'value': [1, 2, 3]}), sink)
metadata = pq.read_metadata(pa.BufferReader(sink.getvalue()))
objects = {
    'file': metadata,
    'row_group': metadata.row_group(0),
    'column_chunk': metadata.row_group(0).column(0),
    'statistics': metadata.row_group(0).column(0).statistics,
    'schema': metadata.schema,
    'column_schema': metadata.schema.column(0),
}
obj = objects[{kind!r}]
try:
    result = {operation}
except TypeError:
    print('TypeError')
else:
    print(repr(result))
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    print(f'PyArrow {pa.__version__}; Python {sys.version.split()[0]}', flush=True)
    print('Real in-memory Parquet write/read; one process per comparison', flush=True)
    results = []
    for kind in ('file', 'row_group', 'column_chunk', 'statistics', 'schema', 'column_schema'):
        row = {'object': kind}
        for label, operation in (('== None', 'obj == None'), ('.equals(None)', 'obj.equals(None)')):
            code = SETUP.replace('{kind!r}', repr(kind)).replace('{operation}', operation)
            proc = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=15)
            outcome = proc.stdout.strip()
            if proc.returncode < 0:
                outcome = signal.Signals(-proc.returncode).name
            elif proc.returncode:
                outcome = f'exit {proc.returncode}: {proc.stderr.strip()}'
            row[label] = {'exit_code': proc.returncode, 'result': outcome}
        results.append(row)
        print(f"{kind:14s}  == None: {row['== None']['result']:10s}  .equals(None): {row['.equals(None)']['result']}", flush=True)
    args.output.write_text(json.dumps({'pyarrow': pa.__version__, 'python': sys.version, 'cpp_build_info': pa.cpp_build_info._asdict(), 'results': results}, indent=2))
    crashes = sum(case['exit_code'] < 0 for row in results for key, case in row.items() if key != 'object')
    print(f'Native crashes: {crashes}', flush=True)


if __name__ == '__main__':
    main()
