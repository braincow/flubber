#!/usr/bin/env python
# -*- coding: utf-8 -*-

# name
APP='flubber'

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
    description='Flubber is a GTK+ 3 frontend for Watson timetracker',
    packages=[APP],
    author='Antti Peltonen',
    author_email='antti.peltonen@iki.fi',
    license='MIT',
    long_description=readme,
    install_requires=parse_requirements('requirements.txt'),
    tests_require=parse_requirements('requirements-dev.txt'),
    entry_points={
        'console_scripts': [
            'flubber = flubber.__main__:gui',
        ]
    },
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Operating System :: POSIX",
        "Intended Audience :: Customer Service",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Other Audience"
    ],
    keywords='flubber watson gtk time-tracking time tracking',
)
