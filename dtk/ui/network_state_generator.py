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

import re

enum_regex = re.compile(r'typedef enum(?:\s+[a-zA-Z]+)?\s*\{(.*?)\}', re.DOTALL)
comment_regex = re.compile(r'/\*.*?\*/', re.DOTALL)
# Header include package `network-manager-dev`.
headers = ['/usr/include/NetworkManager/NetworkManager.h',
           '/usr/include/NetworkManager/NetworkManagerVPN.h']
if __name__ == "__main__":
    state_string = "# Constants below are generated with network_state_generator.py. Do not edit manually.\n\n"
    for h in headers:
        for enum in enum_regex.findall(open(h).read()):
            enum = comment_regex.sub('', enum)
            last = -1
            for key in enum.split(','):
                if not key.strip():
                    continue
                if '=' in key:
                    key, val = key.split('=')
                    val = eval(val)
                else:
                    val = last + 1
                key = key.strip()
                # print('%s = %d' % (key, val))
                state_string += "%s = %d\n" % (key, val)
                last = val
    
    state_file = open("./network_state.py", "w")
    state_file.write(state_string)
    state_file.close()

    
