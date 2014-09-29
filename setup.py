#! /usr/bin/env python

import os
from setuptools import setup, find_packages

def list_datafiles(pkg, dirs, exts):
    subdirs = []
    for dir in dirs:
        subdirs += [ d.lstrip(pkg).lstrip('/') for d, _, _ in os.walk(pkg+'/'+dir) ]
    files = [ (d+'/'+e) for d in subdirs for e in exts ]
    return files

setup(name='dtk',
    version="1.0.3",
    description='UI toolkit for Linux Deepin.',
    long_description ="""UI toolkit for Linux Deepin.""",
    author='Linux Deepin Team',
    author_email='wangyong@linuxdeepin.com',
    license='GPL-3',
    url="https://github.com/linuxdeepin/deepin-ui",
    download_url="git://github.com/linuxdeepin/deepin-ui.git",
    platforms = ['Linux'],
    packages = find_packages(),
    include_package_data = True,
    package_data = {
        '': list_datafiles('dtk', ['theme', 'skin'], ['*.png', '*.jpg', '*.txt', '*.ini'])
    }
)
