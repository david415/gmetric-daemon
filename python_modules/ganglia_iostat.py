#!/usr/bin/env python

# Copyright 2009 Tailrank, Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
#
# author: David Stainton
#

import os
import sys
import re

from libcmd import read_cmd

descriptors = list()
iostat_disk = {}


def Find_Metric (name):
    '''Find the metric definition data given the metric name.
   The metric name should always be unique.'''
    for d in descriptors:
        if d['name'] == name:
            return d
    pass



def iostat_Handler(name):

    d = Find_Metric(name)
    if not d:
        return 0

    dev = d['dev']

    f = open('/proc/diskstats', 'r')
    for line in f:
        line = line.strip()

        myregex = "\d+\s+\d+\s+%s\s+([^ ]+)\s+[^ ]+\s+[^ ]+\s+[^ ]+\s+([^ ]+)\s+" % (dev)
        m = re.search(myregex, line)

        if m != None:            
            f.close()
            read_counter = int(m.group(1))
            write_counter = int(m.group(2))


            if iostat_disk[dev]['wps'] == None:
                
                if iostat_disk[dev]['write_counter'] == 0:
                    delta = 0
                else:
                    delta = write_counter - iostat_disk[dev]['write_counter']
                    
                wps = delta / d['time_max']
                iostat_disk[dev]['write_counter'] = write_counter
                #print "%s / %s = %s" % (delta, d['time_max'], wps)
                #print "new write_counter = %s" % write_counter
            else:
                wps = iostat_disk[dev]['wps']
                iostat_disk[dev]['wps'] = None


            if iostat_disk[dev]['rps'] == None:

                if iostat_disk[dev]['read_counter'] == 0:
                    delta = 0
                else:
                    delta = read_counter - iostat_disk[dev]['read_counter']

                rps = delta / d['time_max']
                iostat_disk[dev]['read_counter'] = read_counter
                #print "%s / %s = %s" % (delta, d['time_max'], rps)
                #print "new read_counter = %s" % read_counter
            else:
                rps = iostat_disk[dev]['rps']
                iostat_disk[dev]['rps'] = None

            ###print "io_type = %s" % d['io_type']

            if d['io_type'] == 'wps':
                iostat_disk[dev]['rps'] = rps
                return wps
            elif d['io_type'] == 'rps':
                iostat_disk[dev]['wps'] = wps
                return rps

            return 0

    f.close()
    return 0


def get_symlink_dest(link):
    cmd = "ls -l %s" % link
    out = read_cmd(cmd)
    sep = '->'
    out = out.split(sep)
    return out[1].strip()
    

def Init_Metric (fs_name, name, tmax, type, units, slope, fmt, desc, handler, dev):

    '''Create a metric definition dictionary object for a device.'''

    metric_name = fs_name + '-' + name
    
    d = {'name': metric_name,
        'call_back': handler,
        'time_max': tmax,
        'value_type': type,
        'units': units,
        'slope': slope,
        'format': fmt,
        'description': desc,
        'groups': 'disk',
        'dev': dev,
         'write_counter':0,
         'io_type': name}

    return d



def get_lvm_dev():

    output = read_cmd('pvdisplay')

    m = re.search('\s+PV Name\s+([^\s]+)\s+', output)
    if m != None:
        dev = m.group(1)
        return dev.split('/')[2]
            
    return None


def get_root_dev():

    f = open('/proc/mounts', 'r')
    for line in f:
        m = re.match('^\/dev\/([^\s]+)\s+/\s+', line)
        if m != None:
            return m.group(1).strip()

    return None


def metric_init(params):
    global descriptors
    global iostat_disk

    found_d2 = False
    dev = None

    f = open('/proc/mounts', 'r')
    d2dev = ''
    for line in f:
        tuple = line.split()
        if tuple[1] == '/d2':
            found_d2 = True
            if re.search('vg0',tuple[0]) != None:
                dev = get_lvm_dev()
            else:
                dev = tuple[0]

    if found_d2 == True:

        descriptors.append(Init_Metric('mysql_fs', 'wps', int(120), 
                                   'float', 'N', 'both', '%.3f', 
                                   'writes per second', iostat_Handler, dev))

        descriptors.append(Init_Metric('mysql_fs', 'rps', int(120), 
                                   'float', 'N', 'both', '%.3f', 
                                   'reads per second', iostat_Handler, dev))

        iostat_disk[dev] = {}
        iostat_disk[dev]['wps'] = None
        iostat_disk[dev]['rps'] = None
        iostat_disk[dev]['read_counter'] = 0
        iostat_disk[dev]['write_counter'] = 0
        
    dev = get_root_dev()
    if dev != None:

        descriptors.append(Init_Metric('root_fs', 'wps', int(120), 
                                   'float', 'N', 'both', '%.3f', 
                                   'writes per second', iostat_Handler, dev))

        descriptors.append(Init_Metric('root_fs', 'rps', int(120), 
                                   'float', 'N', 'both', '%.3f', 
                                   'reads per second', iostat_Handler, dev))
    
        iostat_disk[dev] = {}
        iostat_disk[dev]['wps'] = None
        iostat_disk[dev]['rps'] = None
        iostat_disk[dev]['read_counter'] = 0
        iostat_disk[dev]['write_counter'] = 0


    return descriptors


def metric_cleanup():
    '''Clean up the metric module.'''
    pass



#This code is for debugging and unit testing    
if __name__ == '__main__':
    metric_init(None)
    for d in descriptors:
        v = d['call_back'](d['name'])
        print 'value for %s is %f' % (d['name'],  v)


