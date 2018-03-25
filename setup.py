#!/usr/bin/env python
# -*- coding: utf-8 -*-

# name
APP='app'

from os.path import join

from setuptools import setup

with open('README.md') as f:
    readme = f.read()

# read package meta-data from version.py
pkg = {}
mod = join(APP, 'version.py')
exec(compile(open(mod).read(), mod, 'exec'), {}, pkg)

def parse_requirements(requirements, ignore=('setuptools',)):
    """Read dependencies from requirements file (with version numbers if any)

    Note: this implementation does not support requirements files with extra
    requirements
    """
    with open(requirements) as f:
        packages = set()
        for line in f:
            line = line.strip()
            if line.startswith(('#', '-r', '--')):
                continue
            if '#egg=' in line:
                line = line.split('#egg=')[1]
            pkg = line.strip()
            if pkg not in ignore:
                packages.add(pkg)
        return tuple(packages)

setup(
    name=APP,
    version=pkg['version'],
    description='Description of this application!',
    packages=[APP],
    author='Your Name Here',
    author_email='your.email@address.here',
    license='MIT',
    long_description=readme,
    install_requires=parse_requirements('requirements.txt'),
    tests_require=parse_requirements('requirements-dev.txt'),
    entry_points={
        'console_scripts': [
            'app = app.__main__:app',
        ]
    },
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License"
    ],
    keywords='fuu bar',
)
