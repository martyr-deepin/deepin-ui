#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Deepin, Inc.
#               2011 Hou Shaohui
#
# Author:     Hou Shaohui <houshao55@gmail.com>
# Maintainer: Hou ShaoHui <houshao55@gmail.com>
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

from deepin_utils.config import Config as DConfig

class Config(DConfig):
    '''
    Config module to read *.ini file.
    '''

    def __init__(self,
                 config_file,
                 default_config=None):
        '''
        Init config module.

        @param config_file: Config filepath.
        @param default_config: Default config value use when config file is empty.
        '''
        print "Please import deepin_utils.config instead dtk.ui.config, this module will remove in next version."
        DConfig.__init__(self, config_file, default_config)
