import glob
import os
import re

from setuptools import find_packages, setup
from setuptools.command.install import install

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


with open("README.md", encoding="utf-8") as f1, open("CHANGELOG.md", encoding="utf-8") as f2:
    long_description = f"{f1.read()}\n\n{f2.read()}"

setup(
    name="py-consul",
    version=metadata["version"],
    author="Criteo",
    author_email="github@criteo.com",
    url="https://github.com/criteo-forks/py-consul",
    license="MIT",
    description=description,
    description_content_type="text/markdown",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=py_modules,
    install_requires=_read_reqs("requirements.txt"),
    extras_require={
        "asyncio": ["aiohttp"],
    },
    data_files=[(".", ["requirements.txt", "tests-requirements.txt"])],
    packages=find_packages(exclude=["tests*"]),
    tests_require=_read_reqs("tests-requirements.txt"),
    cmdclass={"install": Install},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
