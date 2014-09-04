#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Hou Shaohui
#
# Author:     Hou Shaohui <houshao55@gmail.com>
# Maintainer: Hou Shaohui <houshao55@gmail.com>
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

import logging
import re

levelno = logging.INFO

def set_level_no(n):
    global levelno
    levelno = ( 100 - (n * 10) )

class FilterLogger(logging.Logger):
    class Filter(logging.Filter):
        def filter(self, record):
            pass_record = True

            if FilterLogger.module is not None:
                pass_record = record.name == self.module

            if FilterLogger.level != logging.NOTSET and pass_record:
                pass_record = record.levelno == self.level

            return pass_record

    module = None
    level = logging.NOTSET

    def __init__(self, name):
        logging.Logger.__init__(self, name)

        log_filter = self.Filter(name)
        log_filter.module = FilterLogger.module
        log_filter.level = FilterLogger.level
        self.addFilter(log_filter)

# FilterLogger.module = ""
# FilterLogger.level = ""
logging.setLoggerClass(FilterLogger)

levelno = logging.DEBUG
logging.addLevelName(100, "DEPRECATED")
# console_format = '%(asctime)s %(levelname)-8s %(name)-30s %(message)s'
console_format = '%(levelname)-8s %(name)-30s %(message)s'
logging.basicConfig(level=levelno, format=console_format, datafmt="%H:%M:%S")

def objaddr(obj):
    string = object.__repr__(obj)
    m = re.search("at (0x\w+)",string)
    if m: return  m.group(1)[2:]

    return "       "

class Logger(object):

    def set_log_name(self, name):
        self.__logname = name

    def get_log_name(self):
        if hasattr(self,"__logname") and self.__logname :
            return self.__logname
        else:
            return "%s.%s"%(self.__module__,self.__class__.__name__)

    def log_debug(self, msg, *args, **kwargs):
        # msg = "%s %s"%(objaddr(self),msg)
        mylogger = logging.getLogger(self.get_log_name())
        mylogger.debug(msg, *args, **kwargs)

    def log_info(self, msg, *args, **kwargs):
        # msg = "%s  %s"%(objaddr(self),msg)
        mylogger = logging.getLogger(self.get_log_name())
        mylogger.info(msg, *args, **kwargs)

    def log_warn(self, msg, *args, **kwargs):
        # msg = "%s  %s"%(objaddr(self),msg)
        mylogger = logging.getLogger(self.get_log_name())
        mylogger.warn(msg, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        # msg = "%s  %s"%(objaddr(self),msg)
        mylogger = logging.getLogger(self.get_log_name())
        mylogger.error(msg, *args, **kwargs)

    def log_critical(self, msg, *args, **kwargs):
        # msg = "%s  %s"%(objaddr(self),msg)
        mylogger = logging.getLogger(self.get_log_name())
        mylogger.critical(msg, *args, **kwargs)

    def log_exception(self, msg, *args, **kwargs):
        # msg = "%s  %s"%(objaddr(self),msg)
        mylogger = logging.getLogger(self.get_log_name())
        mylogger.exception(msg, *args, **kwargs)

    def log_deprecated(self, msg, *args, **kwargs):
        # msg = "%s  %s"%(objaddr(self),msg)
        mylogger = logging.getLogger(self.get_log_name())
        mylogger.log(100,msg, *args, **kwargs)

def new_logger(name):
    l = Logger()
    l.set_log_name(name)

    return l
