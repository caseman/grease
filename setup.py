#############################################################################
#
# Copyright (c) 2010 by Casey Duncan and contributors
# All Rights Reserved.
#
# This software is subject to the provisions of the MIT License
# A copy of the license should accompany this distribution.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
#############################################################################

from ez_setup import use_setuptools
use_setuptools()

import os
import sys
import shutil
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.txt')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires=['pyglet']
tests_require = install_requires + ['Sphinx', 'docutils', 'nose', 'coverage']

# Copy the blasteroids example scripts to the tutorial dir
# Ideally they would just live there, but inflexibility in
# distutils wrt packaging data makes this necessary
for i in range(1, 4):
    shutil.copyfile(
        os.path.join(here, 'examples', 'blasteroids%s.py' % i),
        os.path.join(here, 'doc', 'tutorial', 'blasteroids%s.py' % i))

setup(
    name='grease',
    version='0.3', # *** REMEMBER TO UPDATE __init__.py ***
    description='The highly extensible game engine framework for Python',
    long_description=README + '\n\n' +  CHANGES,
    keywords='game engine pyglet grease',
    author='Casey Duncan',
    author_email='casey.duncan@gmail.com',
    # url='',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.6',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
    ],

    package_dir={'grease': 'grease', 
                 'grease.controller': 'grease/controller',
                 'grease.component': 'grease/component',
                 'grease.renderer': 'grease/renderer',
                 'grease.test': 'grease/test',
                 'grease.examples': 'examples'},
    package_data={'grease.examples': ['font/*', 'sfx/*']},
    packages=find_packages(),
    install_requires = install_requires,
    tests_require = tests_require,
    test_suite="nose.collector",
    zip_safe=False,
)

try:
    import numpy
except ImportError:
    print """
WARNING:
    numpy is required by grease, but it is not installed. 
    Unfortunately it cannot be installed automatically by setuptools.

    You can download and install it yourself from:
    https://sourceforge.net/projects/numpy/files/
"""
