# network statistics utility functions #

import json
from collections import namedtuple

STATUS_NA = 'N/A'
PORT_RATE = 40

rates_key_list = [ 'RX_BPS', 'RX_PPS', 'RX_UTIL', 'TX_BPS', 'TX_PPS', 'TX_UTIL' ]
ratestat_fields = ("rx_bps",  "rx_pps", "rx_util", "tx_bps", "tx_pps", "tx_util")
RateStats = namedtuple("RateStats", ratestat_fields)

COUNTERS_PORT_NAME_MAP = "COUNTERS_PORT_NAME_MAP"
COUNTERS_RIF_NAME_MAP = "COUNTERS_RIF_NAME_MAP"
RATES_TABLE_PREFIX = "RATES:"

def ns_diff(newstr, oldstr):
    """
        Calculate the diff.
    """
    if newstr == STATUS_NA or oldstr == STATUS_NA:
        return STATUS_NA
    else:
        new, old = int(newstr), int(oldstr)
        return '{:,}'.format(max(0, new - old))

def ns_brate(newstr, oldstr, delta):
    """
        Calculate the byte rate.
    """
    if newstr == STATUS_NA or oldstr == STATUS_NA:
        return STATUS_NA
    else:
        rate = int(ns_diff(newstr, oldstr).replace(',',''))/delta
        if rate > 1024*1024*10:
            rate = "{:.2f}".format(rate/1024/1024.0)+' MB'
        elif rate > 1024*10:
            rate = "{:.2f}".format(rate/1024.0)+' KB'
        else:
            rate = "{:.2f}".format(rate)+' B'
        return rate+'/s'

def ns_prate(newstr, oldstr, delta):
    """
        Calculate the packet rate.
    """
    if newstr == STATUS_NA or oldstr == STATUS_NA:
        return STATUS_NA
    else:
        rate = int(ns_diff(newstr, oldstr).replace(',',''))/delta
        return "{:.2f}".format(rate)+'/s'

def ns_util(newstr, oldstr, delta, port_rate=PORT_RATE):
    """
        Calculate the util.
    """
    if newstr == STATUS_NA or oldstr == STATUS_NA:
        return STATUS_NA
    else:
        rate = int(ns_diff(newstr, oldstr).replace(',',''))/delta
        util = rate/(port_rate*1024*1024*1024/8.0)*100
        return "{:.2f}%".format(util)

def format_brate(rate):
    """
    Show the byte rate.
    """
    if rate == STATUS_NA:
        return STATUS_NA
    else:
        rate = float(rate)
        if rate > 1024*1024*10:
            rate = "{:.2f}".format(rate/1024/1024.0)+' MB'
        elif rate > 1024*10:
            rate = "{:.2f}".format(rate/1024.0)+' KB'
        else:
            rate = "{:.2f}".format(rate)+' B'
        return rate+'/s'

def format_prate(rate):
    """
    Show the packet rate.
    """
    if rate == STATUS_NA:
        return STATUS_NA
    else:
        return "{:.2f}".format(float(rate))+'/s'

def format_util(brate, port_rate=PORT_RATE):
    """
    Calculate the util.
    """
    if brate == STATUS_NA:
        return STATUS_NA
    else:
        util = brate/(float(port_rate)*1024*1024*1024/8.0)*100
        return "{:.2f}%".format(util)

def table_as_json(table, header):
    """
        Print table as json format.
    """
    output = {}

    # Build a dictionary where the if_name is the key and the value is
    # a dictionary that holds MTU, TX_DRP, etc
    for line in table:
        if_name = line[0]
        output[if_name] = {header[i]: line[i] for i in range(1, len(header))}
    
    return json.dumps(output, indent=4, sort_keys=True)
