from setuptools import setup, find_packages

PACKAGE = "fastapi-sqlalchemy"
VERSION = "0.1.1"

setup(
    name=PACKAGE,
    version=VERSION,
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "email-validator",
        "fastapi",
        "passlib",
        "python-dateutil",
        "python-multipart",
        "pyjwt",
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
