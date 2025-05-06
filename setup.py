from setuptools import setup, find_packages

setup(
    name="dee",
    version="0.1.11",
    packages=find_packages(where="src"),    # encontra só dentro de src/
    package_dir={"": "src"},                # define que src/ é a raiz dos pacotes
    install_requires=[
        "click",
        "django",
        "djangorestframework",
        "jinja2",
        "paramiko",
        "psycopg2-binary",
        "pygments",
        "python-decouple",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "dee=cli.commands:cli",           
        ],
    },
)
