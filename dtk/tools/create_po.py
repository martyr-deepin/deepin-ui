#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import os
import glob
from ConfigParser import RawConfigParser as ConfigParser

def remove_directory(path):
    """equivalent to command `rm -rf path`"""
    if os.path.exists(path):
        for i in os.listdir(path):
            full_path = os.path.join(path, i)
            if os.path.isdir(full_path):
                remove_directory(full_path)
            else:
                os.remove(full_path)
        os.rmdir(path)        
        
def create_directory(directory, remove_first=False):
    '''Create directory.'''
    if remove_first and os.path.exists(directory):
        remove_directory(directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
        
if __name__ == "__main__":
    # Read config options.
    config_parser = ConfigParser()
    config_parser.read("locale_config.ini")
    project_name = config_parser.get("locale", "project_name")
    source_dir = os.path.abspath(config_parser.get("locale", "source_dir"))
    locale_dir = os.path.abspath(config_parser.get("locale", "locale_dir"))
    langs = eval(config_parser.get("locale", "langs"))
    create_directory(locale_dir)
    
    # Get input arguments.
    source_files = glob.glob(os.path.join(source_dir, "*.py"))
    pot_filepath = os.path.join(locale_dir, project_name + ".pot")
    
    # Generate pot file.
    subprocess.call(
        "xgettext -k_ -o %s %s" % (pot_filepath, ' '.join(source_files)),
        shell=True)
    
    # Generate po files.
    for lang in langs:
        subprocess.call(
            "msginit --no-translator -l %s.UTF-8 -i %s -o %s" % (lang, pot_filepath, os.path.join(locale_dir, "%s.po" % (lang))),
            shell=True
            )
        
