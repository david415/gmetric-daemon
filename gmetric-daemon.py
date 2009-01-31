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

import re
import os
import sys
import time


gmetric_path = '/opt/ganglia/bin/gmetric'

pid_list = []

def ganglia_report_value(metric_name, value, type, units):
   gangliaMetric = gmetric_path + " --name=" + metric_name + " --value=" + str(value) + " --type=" + type + " --units=" + units
   #print(gangliaMetric)
   res = os.system(gangliaMetric)


# one proc per module
# each proc handles it's own collector scheduling
# based on how long the previous collection took
def forkModule(time_max, run):

   newpid = os.fork()

   if newpid == 0:

      while True:
         start_t = time.time()

         metrics = run()

         end_t = time.time()
         duration = end_t - start_t

         for name,value,type,units in metrics:
            ganglia_report_value(name, value)


      # have i got this right?
      # maybe we should always sleep the same amount of time.

         if duration > time_max:
            sleep_t = time_max % duration
         else:
            sleep_t = time_max - duration

         time.sleep(sleep_t)

   # else parent proc returns
   else:
      pid_list.append(newpid)
      return


# spawns a thread per module to execute the run() function

def run_modules(module_dir):

   modules = os.listdir(module_dir)

   sys.path.append(module_dir)

   for module_name in modules:

      if re.match('^\.', module_name) != None:
         continue
      if re.match('^#', module_name) != None:
         continue

      module_name = module_name.split('.')[0]
      print "importing %s" % module_name
      module = __import__(module_name)
      print module
      forkModule(module.time_max, module.run)


def main():
   module_dir = "modules.d"
   run_modules(module_dir)

   # must wait for children to die
   for pid in pid_list:
      os.waitpid(pid,0)


if __name__ == "__main__":
   main()

