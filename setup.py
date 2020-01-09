from setuptools import setup, find_packages

PACKAGE = "fastapi-sqlalchemy"
VERSION = "0.6.0"

setup(
    name=PACKAGE,
    version=VERSION,
    author="Matthew Laue",
    author_email="matt@zuar.com",
    url="https://github.com/zuarbase/fastapi-sqlalchemy",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "email-validator",
        "fastapi>=0.42.0",
        "passlib",
        "python-dateutil",
        "python-multipart",
        "pyjwt",
        "sqlalchemy",
        "sqlalchemy-filters",
        "tzlocal",
        "itsdangerous",
    ],
    extras_require={
        "dev": [
            "coverage",
            "pylint",
            "pytest",
            "pytest-env",
            "pytest-dotenv",
            "pytest-mock",
            "requests",
            "flake8",
            "flake8-quotes",
        ],
        "prod": [
            "uvicorn",
            "gunicorn",
        ]
    }
)
