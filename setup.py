from distutils.core import setup, Extension

setup(
    name="procset",
    version="1.0",
    ext_modules=[Extension("procset", ["src/procsetmodule.c"])],
)