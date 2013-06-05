#! /usr/bin/env python

from setuptools import setup
import os

def list_files(target_dir, install_dir):
    '''List files for option `data_files`.'''
    results = []
    for root, dirs, files in os.walk(target_dir):
        for filepath in files:
            data_dir = os.path.dirname(os.path.join(root, filepath))
            data_file = os.path.join(root, filepath)
            results.append((data_dir, [data_file]))
            # print results
    return results                

setup(name='dtk',
      version='0.1',
      description='UI toolkit for Linux Deepin.',
      long_description ="""UI toolkit for Linux Deepin.""",
      author='Linux Deepin Team',
      author_email='wangyong@linuxdeepin.com',
      license='GPL-3',
      url="https://github.com/linuxdeepin/deepin-ui",
      download_url="git://github.com/linuxdeepin/deepin-ui.git",
      platforms = ['Linux'],
      packages = ['dtk', 'dtk.ui'],
      data_files = list_files("dtk/theme","dtk/theme") + list_files("dtk/locale", "dtk/locale") + list_files("dtk/skin", "dtk/skin"),
      )

