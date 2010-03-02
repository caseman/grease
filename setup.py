#!/usr/bin/env python

# $Id$

import os
import sys
from distutils.core import setup, Extension

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
	name='grease',
    version='0.1', # *** REMEMBER TO UPDATE __init__.py ***
	description='Grease: A component-based game engine and rapid development framework',
	long_description=read('README.txt'),
	author='Casey Duncan',
	author_email='casey.duncan@gmail.com',
	#url='http://code.google.com/p/py-grease/',
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
