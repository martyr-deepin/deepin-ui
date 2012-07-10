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

from contextlib import contextmanager 
from threading import Lock
import Queue as Q
import gtk
import os
import threading as td
import time

class MissionThreadPool(td.Thread):
    '''Mission thread pool'''
    
    FINISH_SIGNAL = "Finish"
	
    def __init__(self, 
                 concurrent_thread_num=5, # max concurrent thread number
                 clean_delay=0,           # clean delay (milliseconds)
                 clean_callback=None,     # clean callback
                 exit_when_finish=False   # exit thread pool when all missions finish
                 ):    
        '''Init thread pool.'''
        # Init thread.
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit 
        
        # Init arguments.
        self.concurrent_thread_num = concurrent_thread_num
        self.clean_delay = clean_delay
        self.clean_callback = clean_callback
        self.clean_time = time.time()
        self.exit_when_finish = exit_when_finish
        
        # Init list.
        self.active_mission_list = []
        self.wait_mission_list = []
        self.mission_result_list = []
        
        # Init lock.
        self.thread_sync_lock = Lock()
        self.mission_lock = Q.Queue()

    def run(self):
        '''Run.'''
        self.loop()
        
    def loop(self):
        '''Loop.'''
        result = self.mission_lock.get()
        if result == self.FINISH_SIGNAL:
            print ">>> Finish missions."
            if self.exit_when_finish:
                print ">>> Exit thread pool %s" % (self)
            else:
                print ">>> Wait new missions."
                self.loop()
        else:
            self.start_missions(result)
            self.loop()
            
    def add_missions(self, missions):
        '''Add missions.'''
        self.mission_lock.put(missions)
        
    def start_missions(self, missions):
        '''Add missions.'''
        for (index, mission) in enumerate(missions):
            # Add to wait list if active mission number reach max value.
            if len(self.active_mission_list) >= self.concurrent_thread_num:
                self.wait_mission_list += missions[index::]
                break
            # Otherwise start new mission.
            else:
                self.start_mission(mission)
                
    def start_mission(self, mission):
        '''Start mission.'''
        self.active_mission_list.append(mission)
        mission.finish_mission = self.finish_mission
        mission.start()
                
    def wake_up_wait_missions(self):
        '''Wake up waiting missions.'''
        for mission in self.wait_mission_list:
            # Just break loop when active mission is bigger than max value.
            if len(self.active_mission_list) >= self.concurrent_thread_num:
                break
            # Otherwise add mission from wait list.
            else:
                # Remove from wait list.
                if mission in self.wait_mission_list:
                    self.wait_mission_list.remove(mission)
                
                # Start new mission.
                self.start_mission(mission)
                
    @contextmanager
    def sync(self):
        '''Sync.'''
        self.thread_sync_lock.acquire()
        try:  
            yield  
        except Exception, e:  
            print 'sync error %s' % e  
        else:  
            self.thread_sync_lock.release()
        
    def finish_mission(self, mission):
        '''Finish mission.'''
        with self.sync():
            # Remove mission from active mission list.
            if mission in self.active_mission_list:
                self.mission_result_list.append(mission.get_mission_result())
                self.active_mission_list.remove(mission)
                
            # Wake up wait missions.
            self.wake_up_wait_missions()
            
            # Do clean work.
            if self.clean_delay > 0 and self.clean_callback != None and len(self.mission_result_list) > 0:
                # Get current time.
                current_time = time.time()
                
                # Do clean work no mission will start or time reach delay.
                if (len(self.active_mission_list) == 0 and len(self.wait_mission_list) == 0) or (current_time - self.clean_time) * 1000 > self.clean_delay:
                    self.clean_mission(current_time)
                    
            # Exit thread when download finish.
            if (len(self.active_mission_list) == 0 and len(self.wait_mission_list) == 0):
                self.mission_lock.put(self.FINISH_SIGNAL)
                    
    def clean_mission(self, current_time):
        '''Clean missions.'''
        # Do clean work.
        self.clean_callback(self.mission_result_list)
                    
        # Clean mission result list.
        self.mission_result_list = []                
                    
        # Record new clean time.
        self.clean_time = current_time
                    
class MissionThread(td.Thread):
    '''Mission thread.'''
	
    def __init__(self):
        '''Mission thread.'''
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit 
        
    def run(self):
        '''Run.'''
        self.start_mission()
        self.finish_mission(self)
        
    def start_mission(self):
        '''Start mission.'''
        print "Write your code here."

    def get_mission_result(self):
        '''Get mission result, if you don't want handle result, just return None.'''
        return None
        
class TestMissionThread(MissionThread):
    '''Test mission thread.'''
	
    def __init__(self, artist):
        '''Init test mission thread.'''
        MissionThread.__init__(self)
        self.artist = artist
        
    def start_mission(self):
        '''Start misssion.'''
        print "*** Start download cover for %s" % (self.artist)
        time.sleep(5)
        print "*** Finish download cover for %s" % (self.artist)
        
    def get_mission_result(self):
        '''Get misssion retsult.'''
        return os.path.join("/home/cover", self.artist)
    
def clean_cover(filepath):
    '''Clean cover.'''
    print "#### Update covers %s" % (filepath)    
        
if __name__ == "__main__":
    gtk.gdk.threads_init()
        
    artists_one = ["John Lennon", "Aqua", "Beatles", "Bob Dylan", "BSB", "Anastacia", "Coldplay",
                   "James Blunt", "James Morrison", "Jason Mraz"]
    artists_two = ["Daniel Powter", "Dixie Chicks", "Egil Olsen", "Elton John", "Elvis Presley"]
    
    missions_one = []
    for artist in artists_one:
        missions_one.append(TestMissionThread(artist))

    missions_two = []
    for artist in artists_two:
        missions_two.append(TestMissionThread(artist))
        
    pool = MissionThreadPool(5, 1000, clean_cover)
    pool.start()
    pool.add_missions(missions_one)
    pool.add_missions(missions_two)

    gtk.main()
