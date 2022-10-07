#!env python3

from setuptools import setup, find_packages

setup(
    name="msdocs_to_dash",
    version="0.0.1",
    description="",
    url="https://github.com/sreinhardt/msdocs_to_dash",
    author="Spenser Reinhardt",
    author_email="none@none.none",
    packages=find_packages(exclude=["test", "extra"]),
    include_package_data=True,
    install_requires=[ "requests", "selenium", "bs4"]
)