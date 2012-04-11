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

from PIL import Image

def get_dominant_color(image_path):
    '''Get dominant color of image.'''
    # Get image.
    image = Image.open(image_path).convert('RGBA')
    
    # Init.
    color_count = 0
    r_all = 0
    g_all = 0
    b_all = 0
    
    # Scan image.
    for count, (r, g, b, a) in image.getcolors(image.size[0] * image.size[1]):
        # Skip transparent pixel.
        if a == 0:
            continue

        # Add color information.
        r_all += r
        g_all += g
        b_all += b
        
        # Update counter.
        color_count += 1
        
    return (r_all / color_count, g_all / color_count, b_all / color_count)    

if __name__ == '__main__':
    print '#%02x%02x%02x' % get_dominant_color("/home/andy/deepin-ui/dtk/theme/default/image/background9.jpg")
