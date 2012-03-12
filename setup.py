#! /usr/bin/env python

from distutils.core import setup, Extension
from setuptools import find_packages
import os

def list_files(target_dir, install_dir):
    '''List files for option `data_files`.'''
    results = []
    for root, dirs, files in os.walk(target_dir):
        for filepath in files:
            data_dir = os.path.dirname(os.path.join(root, filepath))
            data_file = os.path.join(root, filepath)
            results.append((data_dir, [data_file]))
            print results
    return results                

mod = Extension('dtk.ui.cairo_blur',
                include_dirs = ['/usr/include/cairo',
                                '/usr/include/pixman-1',
                                '/usr/include/freetype2',
                                '/usr/include/libpng12',
                                '/usr/include/glib-2.0',
                                '/usr/lib/x86_64-linux-gnu/glib-2.0/include'],
                libraries = ['cairo', 'pthread', 'glib-2.0'],
                sources = ['dtk/ui/cairo_blur.c'])

setup(name='dtk',
      version='0.1',
      description='UI toolkit for Linux Deepin.',
      long_description ="""UI toolkit for Linux Deepin.""",
      author='Linux Deepin Team',
      author_email='wangyong@linuxdeepin.com',
      license='GPL-3',
      url="https://github.com/manateelazycat/deepin-ui-toolkit",
      download_url="git://github.com/manateelazycat/deepin-ui-toolkit.git",
      platforms = ['Linux'],
      packages = ['dtk', 'dtk.ui'],
      data_files = list_files("dtk/theme","dtk/theme"),
      ext_modules = [mod]
      )

