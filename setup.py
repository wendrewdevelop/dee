from setuptools import setup, find_packages

setup(
    name="dee",
    version="0.1.12",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dee=src.main:main",           
        ],
    },
)
