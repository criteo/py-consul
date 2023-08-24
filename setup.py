import glob
import os
import re
import sys

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.test import test as TestCommand

with open("consul/__init__.py", encoding="utf-8") as f:
    metadata = dict(re.findall('__([a-z]+)__ = "([^"]+)"', f.read()))


def _read_reqs(relpath: str):
    fullpath = os.path.join(os.path.dirname(__file__), relpath)
    with open(fullpath, encoding="utf-8") as f:
        return [s.strip() for s in f.readlines() if (s.strip() and not s.startswith("#"))]


description = "Python client for Consul (http://www.consul.io/)"


py_modules = [os.path.splitext(x)[0] for x in glob.glob("consul/*.py")]


class Install(install):
    def run(self):
        install.run(self)


class PyTest(TestCommand):
    # pylint: disable=attribute-defined-outside-init
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest  # pylint: disable=import-outside-toplevel

        errno = pytest.main(self.test_args)
        sys.exit(errno)


with open("README.rst", encoding="utf-8") as f1, open("CHANGELOG.rst", encoding="utf-8") as f2:
    long_description = f"{f1.read()}\n\n{f2.read()}"

setup(
    name="py-consul",
    version=metadata["version"],
    author="Criteo",
    author_email="github@criteo.com",
    url="https://github.com/criteo-forks/py-consul",
    license="MIT",
    description=description,
    long_description=long_description,
    py_modules=py_modules,
    install_requires=_read_reqs("requirements.txt"),
    extras_require={
        "tornado": ["tornado"],
        "asyncio": ["aiohttp"],
        "twisted": ["twisted", "treq"],
    },
    data_files=[(".", ["requirements.txt", "tests-requirements.txt"])],
    tests_require=_read_reqs("tests-requirements.txt"),
    cmdclass={"test": PyTest, "install": Install},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
