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

__author__ = "David Stainton"
__copyright__ = "Copyright 2009 Tailrank, Inc."
__license__ = "Apache License"

import os
import sys
import re
import time
from subprocess import *

pdns_state = {}
pdns_state['cache-hits'] = 0
pdns_state['cache-misses'] = 0

time_max = 60

def run():
    metric = ('pdns_cache_hit_ratio', str(get_pdns_cache_ratio()), 'float', 'ratio')
    singleton = metric,
    return singleton

def read_cmd(cmd,input=None,cwd=None):
    """Run the given command and read its output"""

    pipe = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE,stdin=PIPE,cwd=cwd)

    out=''
    err=''

    while True:

        (_out,_err) = pipe.communicate( input )

        out += _out
        err += _err

        ret = pipe.poll()
        
        if ret != None:
            return out

        if returncode == 0:
            return out
        elif returncode >= 0:
            if sys.stderr != None:
                sys.stderr.write(err)
                raise Exception( "%s exited with %s" % (cmd, returncode) )


def get_pdns_stat(name):
    cmd = "/usr/bin/sudo /usr/bin/rec_control get " + name
    out = read_cmd(cmd)
    #print "out %s" % out
    return int(out.strip())


def get_pdns_cache_ratio():

    global pdns_state

    hits = get_pdns_stat('cache-hits')
    misses = get_pdns_stat('cache-misses')
    
    if pdns_state['cache-hits'] == 0 and pdns_state['cache-misses'] == 0:
        pdns_state['cache-hits'] = hits
        pdns_state['cache-misses'] = misses
        return 0

    hits_delta = hits - pdns_state['cache-hits']
    misses_delta = misses - pdns_state['cache-misses']

    pdns_state['cache-hits'] = hits
    pdns_state['cache-misses'] = misses

    cache_total = hits_delta + misses_delta
    hits_ratio = float()

    if cache_total > 0:
        hits_ratio = float(hits_delta) / float(cache_total)
    else:
        hits_ratio = 0

    return hits_ratio * 100



#This code is for debugging and unit testing    
if __name__ == '__main__':
    print(run())
    time.sleep(30)
    print(run())


