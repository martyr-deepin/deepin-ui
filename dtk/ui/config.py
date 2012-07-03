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

from ConfigParser import RawConfigParser as ConfigParser
from collections import OrderedDict
import gobject    

class Config(gobject.GObject):
    __gsignals__ = {
        "config-changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                            (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING))
        }
    
    def __init__(self, config_file, default_config=None):
        gobject.GObject.__init__(self)
        self.config_parser = ConfigParser()
        self.remove_option = self.config_parser.remove_option
        self.has_option = self.config_parser.has_option
        self.add_section = self.config_parser.add_section
        self.getboolean = self.config_parser.getboolean
        self.getint = self.config_parser.getint
        self.getfloat = self.config_parser.getfloat
        self.options = self.config_parser.options
        self.config_file = config_file
        self.default_config = default_config
        
        # Load default configure.
        self.load_default()
                
    def load_default(self):            
        # Convert config when config is list format.
        if isinstance(self.default_config, list):
            self.default_config = self.convert_from_list(self.default_config)
            
        if self.default_config:
            for section, items in self.default_config.iteritems():
                self.add_section(section)
                for key, value in items.iteritems():
                    self.config_parser.set(section, key, value)
                
    def load(self):            
        ''' Load config items from the file. '''
        self.config_parser.read(self.config_file)
    
    def get(self, section, option, default=None):
        ''' specified the section for read the option value. '''
        try:
            return self.config_parser.get(section, option)
        except Exception, e:
            print "config.get error: %s" % (e)
            return default
            
    def set(self, section, option, value):  
        if not self.config_parser.has_section(section):
            print "Section \"%s\" not exist. create..." % (section)
            self.add_section(section)
            
        self.config_parser.set(section, option, value)
        self.emit("config-changed", section, option, value)
        
    def write(self, given_filepath=None):    
        ''' write configure to file. '''
        if given_filepath:
            f = file(given_filepath, "w")
        else:
            f = file(self.config_file, "w")
        self.config_parser.write(f)
        f.close()
        
    def get_default(self):    
        return self.default_config
    
    def set_default(self, default_config):
        self.default_config = default_config
        self.load_default()
        
    def convert_from_list(self, config_list):
        '''Convert to dict from list format.'''
        config_dict = OrderedDict()
        for (section, option_list) in config_list:
            option_dict = OrderedDict()
            for (option, value) in option_list:
                option_dict[option] = value
            config_dict[section] = option_dict
        
        return config_dict    
        
gobject.type_register(Config)
