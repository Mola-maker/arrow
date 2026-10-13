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
parser.add_argument('--reuse-cython', action='store_true')
args = parser.parse_args()
repo = args.repo.resolve()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
pyarrow.create_library_symlinks()
Options.warning_errors = True
Options.c_line_in_traceback = False
source = str(repo / 'python/pyarrow/lib.pyx')
if args.reuse_cython:
    generated = list((output / 'cython').rglob('lib.cpp'))
    assert len(generated) == 1, generated
    source = str(generated[0])
extension = Extension(
    'pyarrow.lib',
    [source],
    language='c++',
    include_dirs=[pyarrow.get_include(), numpy.get_include()],
    library_dirs=pyarrow.get_library_dirs(),
    libraries=['arrow_python', 'arrow'],
    runtime_library_dirs=['$ORIGIN'],
    extra_compile_args=['-std=c++20', '-O1', '-g0'],
)
if args.reuse_cython:
    extensions = [extension]
else:
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
sys.argv = ['build_arrow_lib.py', 'build_ext', '--build-lib',
            str(output / 'lib'), '--build-temp', str(output / 'temp'), '--force']
setup(name='arrow-lib-local-validation', version='0.0.0', ext_modules=extensions)
