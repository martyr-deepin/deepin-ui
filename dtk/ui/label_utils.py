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

import tooltip as tooltip

__all__ = ["show_label_tooltip"]

def show_label_tooltip(label):
    '''
    Make label show tooltip.

    @param label: The label widget to display it's content as tooltip.
    '''
    label.update_size_hook = set_label_tooltip_hook

def set_label_tooltip_hook(label, label_width, expect_label_width):
    if expect_label_width < label_width:
        tooltip.disable(label, False)
        tooltip.text(label, label.text)
    else:
        tooltip.disable(label, True)
