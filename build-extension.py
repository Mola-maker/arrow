import argparse
from pathlib import Path
import sys

from Cython.Build import cythonize
from Cython.Compiler import Options
import numpy
import pyarrow
from setuptools import Extension, setup

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
repo = args.repo.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
pyarrow.create_library_symlinks()
Options.warning_errors = True
Options.c_line_in_traceback = False
extension = Extension(
    'pyarrow._parquet',
    [str(repo / 'python/pyarrow/_parquet.pyx')],
    language='c++',
    include_dirs=[pyarrow.get_include(), numpy.get_include()],
    library_dirs=pyarrow.get_library_dirs(),
    libraries=['arrow_python', 'parquet', 'arrow'],
    runtime_library_dirs=['$ORIGIN'],
    extra_compile_args=['-std=c++20', '-O2'],
)
extensions = cythonize(
    [extension],
    include_path=[str(repo / 'python')],
    build_dir=str(output / 'cython'),
    compiler_directives={
        'language_level': 3,
        'embedsignature': True,
        'freethreading_compatible': True,
    },
    force=True,
)
sys.argv = ['build_arrow_parquet.py', 'build_ext', '--build-lib', str(output / 'lib'), '--build-temp', str(output / 'temp'), '--force']
setup(name='arrow-parquet-local-validation', version='0.0.0', ext_modules=extensions)
