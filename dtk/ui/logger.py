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
classfilter = []

def set_level_no(n):
    global levelno
    levelno = ( 100 - (n * 10) )
    
def set_filter(filter_list):    
    global classfilter
    classfilter = filter_list

class MyFilter(logging.Filter):
    def __init__(self, name=""): 
        pass
    
    def filter(self, record):
        if record.levelno >= levelno: 
            return True
        
        for filter in classfilter:
            if record.name.startswith(filter): 
                return True
            
        return False

logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)
logging.addLevelName(100,"DEPRECATED")

# formatter = logging.Formatter('%(levelname)-8s %(name)-30s %(message)s')
formatter = logging.Formatter('%(levelname)-8s %(message)s')

handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.addFilter(MyFilter())
logger.addHandler(handler)

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
    
