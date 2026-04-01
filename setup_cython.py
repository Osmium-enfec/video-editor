from setuptools import setup
from Cython.Build import cythonize
import glob

py_files = [f for f in glob.glob("ffedit/core/*.py") + glob.glob("ffedit/ffmpeg/*.py") if not f.endswith("__init__.py")]

if not py_files:
    print("No files found to cythonize.")
else:
    setup(
        name="cythonize_project",
        ext_modules=cythonize(py_files, compiler_directives={"language_level": "3"}),
    )
