import glob
import sys
import re
import os

from setuptools.command.test import test as TestCommand
from setuptools.command.install import install
from setuptools import setup


metadata = dict(
    re.findall("__([a-z]+)__ = '([^']+)'", open('consul/__init__.py').read()))


requirements = [
    x.strip() for x
    in open('requirements.txt').readlines() if not x.startswith('#')]


description = "Python client for Consul (http://www.consul.io/)"


py_modules = [os.path.splitext(x)[0] for x in glob.glob('consul/*.py')]


class Install(install):
    def run(self):
        install.run(self)


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='py-consul',
    version=metadata['version'],
    author='NetworkLB Team',
    author_email='network-lb@criteo.com',
    url='https://github.com/criteo-forks/py-consul',
    license='MIT',
    description=description,
    long_description="%s\n\n%s" % (
        open('README.rst').read(),
        open('CHANGELOG.rst').read()
    ),
    py_modules=py_modules,
    install_requires=requirements,
    extras_require={
        'tornado': ['tornado'],
        'asyncio': ['aiohttp'],
        'twisted': ['twisted', 'treq'],
    },
    tests_require=['pytest', 'pytest-twisted'],
    cmdclass={'test': PyTest,
              'install': Install},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
