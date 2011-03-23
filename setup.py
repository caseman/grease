#!/usr/bin/env python

# $Id$

import os
import sys
import shutil
from distutils.core import setup, Extension

srcdir = os.path.dirname(__file__)

def read(fname):
    return open(os.path.join(srcdir, fname)).read()

# Copy the blasteroids example scripts to the tutorial dir
# Ideally they would just live there, but inflexibility in
# distutils wrt packaging data makes this necessary
for i in range(1, 4):
	shutil.copyfile(
		os.path.join(srcdir, 'examples', 'blasteroids%s.py' % i),
		os.path.join(srcdir, 'doc', 'tutorial', 'blasteroids%s.py' % i))

setup(
	name='grease',
    version='0.3', # *** REMEMBER TO UPDATE __init__.py ***
	description='Grease: A component-based game engine and rapid development framework',
	long_description=read('README.txt'),
	author='Casey Duncan',
	author_email='casey.duncan@gmail.com',
	url='http://pygamesf.org/~casey/grease/doc/',
	license='MIT',
    classifiers = [
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
				 'grease.test': 'test',
	             'grease.examples': 'examples'},
	package_data={'grease.examples': ['font/*', 'sfx/*']},
    packages=['grease', 
	          'grease.controller', 
	          'grease.component', 
			  'grease.renderer', 
			  'grease.test',
			  'grease.examples'],
)
