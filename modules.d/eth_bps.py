
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


# FIXME:
# initialize module at the end...
# is there a better way?
# should we use the imp way?
#
# FIXME:
# get_eths() should be more flexible
# and not have the first octet hardcoded...

time_max = 120
descriptors = list()


def run():
    metrics = []
    eth_stats_Collector()
    for d in descriptors:
        metrics.append((d['name'], d['value'], d['type'], d['units']))
        d['value'] = None
    return metrics


def eth_stats_Collector():

    f = open('/proc/net/dev', 'r')

    for line in f:
        for d in descriptors:
            if line.split(':')[0].strip() == d['dev']:
                fields = line.split(':')[1].split()

                if d['eth_counter'] == 0:
                    delta = 0
                    if d['op'] == 'in':
                        d['eth_counter'] = int(fields[0])
                    elif d['op'] == 'out':
                        d['eth_counter'] = int(fields[8])
                else:
                    if d['op'] == 'in':
                        delta = float(fields[0]) - d['eth_counter']
                        d['eth_counter'] = int(fields[0])
                    elif d['op'] == 'out':
                        delta = float(fields[8]) - d['eth_counter']
                        d['eth_counter'] = int(fields[8])

                bps = (delta / time_max) * 8
                d['value'] = bps
    f.close()
            

def Init_Metric (metric_name, type, units, dev, op):
    '''Create a metric definition dictionary object for a device.'''
    
    d = {'name': metric_name,
        'value_type': type,
         'value': None,
        'units': units,
         'dev': dev,
         'eth_counter': 0,
         'op': op}
    return d


def get_eths():

    f = open('/proc/net/arp', 'r')

    eths = {}
    fields = []

    # gather unique eth interfaces
    
    for line in f:
        fields = line.split()
        
        if re.match('^eth', fields[5]) == None:
            continue

        if fields[5] in eths.keys():
            continue

        eths[fields[5]] = fields[0]

    f.close()
    external_eth = ''
    internal_eth = ''

    for k, v in eths.iteritems():
        if re.match('^10', v) != None:
            internal_eth = k
            continue

        if re.match('^64', v) != None:
            external_eth = k

    return (external_eth, internal_eth)



def metric_init():
    global descriptors

    # determine which ethernet interfaces
    # are internal and which are external
    (ext_eth, int_eth) = get_eths()

    descriptors.append(Init_Metric('ext-eth-in','float', 'bps', ext_eth, 'in'))
    descriptors.append(Init_Metric('ext-eth-out','float', 'bps', ext_eth, 'out'))
    descriptors.append(Init_Metric('int-eth-in','float', 'bps', int_eth, 'in'))
    descriptors.append(Init_Metric('int-eth-out','float', 'bps', int_eth, 'out'))



metric_init()

