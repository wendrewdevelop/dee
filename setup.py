import re
from setuptools import setup, find_packages


with open("version.py") as f:
    version = re.search(r'__version__ = ["\'](.+)["\']', f.read()).group(1)

setup(
    name="dee",
    version="0.1.14",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "dee=src.main:main",           
        ],
    },
)

#dev dev dev
# dev dev dev