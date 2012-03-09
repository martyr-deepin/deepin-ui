#! /usr/bin/env python

from distutils.core import setup

setup(name='deepin-ui-toolkit',
      version='0.0.1',
      description='UI toolkit for Linux Deepin.',
      long_description ="""UI toolkit for Linux Deepin.""",
      author='Linux Deepin Team',
      author_email='wangyong@linuxdeepin.com',
      license='GPL-3',
      url="https://github.com/manateelazycat/deepin-ui-toolkit",
      download_url="git://github.com/manateelazycat/deepin-ui-toolkit.git",
      platforms = ['Linux'],
      packages = ['dtk'], 
      package_data = {'dtk': ['theme/*']},
      )
