from setuptools import setup

PACKAGE = "fastapi-sqlalchemy"
VERSION = "0.1.0"

setup(
    name=PACKAGE,
    version=VERSION,
    packages=["fastapi_sqlalchemy"],
    install_requires=[
        "fastapi",
        "python-dateutil",
        "sqlalchemy",
        "sqlalchemy-filters",
        "tzlocal"
    ],
    extras_require={
        "dev": [
            "coverage",
            "pylint",
            "pytest",
            "pytest-env",
            "pytest-dotenv",
            "requests",
            "flake8",
            "flake8-quotes"
        ]
    }
)