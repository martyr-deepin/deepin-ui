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

import sys
import subprocess
import os

if __name__ == "__main__":
    # Get input arguments.
    input_dir, output_dir = sys.argv[1], sys.argv[2]
    
    # Init theme color.
    theme_colors = {
        "dark_grey" : "#333333",
        "red" : "#FF0000",
        "orange" : "#FF6C00",
        "gold" : "#FFC600",
        "yellow" : "#FCFF00",
        "green_yellow" : "#C0FF00",
        "chartreuse" : "#00FF60",
        "cyan" : "#00FDFF",
        "dodger_blue" : "#00A8FF",
        "blue" : "#0006FF",
        "dark_purple" : "#8400FF",
        "purple" : "#BA00FF",
        "deep_pink" : "#FF00B4"}

    # Create theme directories.
    for (key, value) in theme_colors.items():
        subprocess.Popen("cp -r %s %s/%s" % (input_dir, output_dir, key), shell=True).wait()
        
        for root, dirs, files in os.walk("%s/%s" % (output_dir, key)):
            for filename in files:
                for extension in [".png", ".jpeg", ".jpg", ".ico"]:
                    if filename.endswith(extension):
                        print "convert %s -fill %s -colorize 50%% %s" % (
                                os.path.join(root, filename),
                                value,
                                os.path.join(root, filename)
                                )
                        
                        image_file = os.path.join(root, filename)
                        subprocess.call(["convert", image_file, "-fill", value, "-colorize", "50%", image_file])
                        break
