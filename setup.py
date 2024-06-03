from setuptools import setup, Extension

setup(
    name="procset",
    version="1.0",
    ext_modules=[
        Extension(
            name="procset",
            sources=["src/procsetmodule.c"],
            extra_compile_args=["-g", "-Wall", "-Wextra", "-Werror", "-std=c99"],
        )
    ],
)
