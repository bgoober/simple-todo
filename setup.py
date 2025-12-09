"""Setup script for Simple Todo."""

from setuptools import setup, find_packages

setup(
    name="simple-todo",
    version="1.0.0",
    description="A minimal to-do list application",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "simple-todo=simple_todo.main:main",
        ],
    },
)

