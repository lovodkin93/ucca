#!/usr/bin/env python

import sys

import os
import re
from glob import glob
from setuptools import setup, find_packages

from ucca.__version__ import VERSION

try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]
os.chdir(os.path.dirname(os.path.abspath(this_file)))

extras_require = {}
install_requires = []
for requirements_file in glob("requirements.*txt"):
    suffix = re.match(r"[^.]*\.(.*)\.?txt", requirements_file).group(1).rstrip(".")
    with open(requirements_file) as f:
        (extras_require.setdefault(suffix, []) if suffix else install_requires).extend(f.read().splitlines())

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(name="UCCA",
      version=VERSION,
      install_requires=install_requires,
      extras_require=extras_require,
      description="Universal Conceptual Cognitive Annotation",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Daniel Hershcovich",
      author_email="danielh@cs.huji.ac.il",
      url="https://github.com/huji-nlp/ucca",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Science/Research",
          "Programming Language :: Python :: 3.6",
          "Topic :: Text Processing :: Linguistic",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
      ],
      packages=find_packages(),
      )
