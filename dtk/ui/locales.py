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

# To test other language, use below method:
#       env LANG=zh_CN LANGUAGE=zh_CN foo.py
#
# WARNING: relative directory `locale` just for test.
# Please copy *.mo files in directory `/usr/share/locale`
# and JUST read *.mo files from `/usr/share/locale`
#
# Read *.mo files from relative directory will make translation string
# can't work, at least i test it can't work in Debian-base system.

from deepin_utils.file import get_parent_dir
import gettext
import os

domain_name = "deepin-ui"

LOCALE_DIR = os.path.join(get_parent_dir(__file__, 2), "locale", "mo")
if not os.path.exists(LOCALE_DIR):
    LOCALE_DIR="/usr/share/locale"

_ = None
try:
    _ = gettext.translation(domain_name, LOCALE_DIR).gettext
except Exception, e:
    _ = lambda i : i

def get_locale_code(domain_name, locale_dir):
    try:
        return gettext.find(domain_name, locale_dir).split(locale_dir)[1].split('/')[1]
    except:
        return "en_US"

LANGUAGE = get_locale_code(domain_name, LOCALE_DIR)
