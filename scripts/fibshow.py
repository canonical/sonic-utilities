#!/usr/bin/env python3

"""
    Script to show dataplane/FIB entries

    usage: fibshow [-ip IPADDR] v
    optional arguments:
        -ip IPADDR, --ipaddr IPADDR
                        dataplane/FIB entry for a specific address

    Example of the output:
    admin@str~$fibshow -4
    No.    Address             nexthop                                  ifname
    -----  ------------------  ---------------------------------------  -----------------------------------------------------------
    1      192.181.8.0/25      10.0.0.57,10.0.0.59,10.0.0.61,10.0.0.63  PortChannel101,PortChannel102,PortChannel103,PortChannel104
    2      192.184.56.0/25     10.0.0.57,10.0.0.59,10.0.0.61,10.0.0.63  PortChannel101,PortChannel102,PortChannel103,PortChannel104
    ...
    Total number of entries 19

    admin@str:~$ sudo fibshow -6 -ip 20c0:b560:0:80::
    No.     Address              nexthop                              ifname
    -----  -------------------  -----------------------------------  -----------------------------------------------------------
    1      20c0:b560:0:80::/64  fc00::72,fc00::76,fc00::7a,fc00::7e  PortChannel101,PortChannel102,PortChannel103,PortChannel104
    Total number of entries 1
"""
import argparse
import json
import sys
import subprocess
import re
import ipaddress

from natsort import natsorted
from swsssdk import port_util
from swsscommon.swsscommon import SonicV2Connector
from tabulate import tabulate


"""
   Base class for v4 and v6 FIB entries.
"""


class FibBase(object):

    HEADER = ["No.", "Address", "nexthop", "ifname"]

    def __init__(self):
        super(FibBase, self).__init__()
        self.db = SonicV2Connector(host="127.0.0.1")
        self.fetch_fib_data()

    def fetch_fib_data(self):
        """
            Fetch FIB entries from APPL_DB
        """
        self.db.connect(self.db.APPL_DB)
        self.fib_entry_list = []

        fib_str = self.db.keys(self.db.APPL_DB, "ROUTE_TABLE:*")
        if not fib_str:
            return

        for s in fib_str:
            fib_entry = s
            fib = fib_entry.split(":", 1)[-1]
            if not fib:
                continue

            ent = self.db.get_all(self.db.APPL_DB, s)
            if not ent:
                continue

            self.fib_entry_list.append((fib,) + (ent["nexthop"],) + (ent["ifname"],) )
        self.fib_entry_list.sort(key=lambda x: x[0])
        return

    def display(self, version, address):
        """
            Display FIB entries from APPL_DB
        """
        output = []
        fdb_index = 1
        for fib in self.fib_entry_list:
            ip = ipaddress.ip_address(fib[0].split("/")[0])
            if address is not None:
                if fib[0] == address:
                    if ip.version == 4 and version == "-4":
                        output.append([fdb_index, fib[0], fib[1], fib[2]])
                        fdb_index += 1
                    elif ip.version == 6 and version == "-6":
                        output.append([fdb_index, fib[0], fib[1], fib[2]])
                        fdb_index += 1
                    break
                else:
                    continue
            else:
                if ip.version == 4 and version == "-4":
                    output.append([fdb_index, fib[0], fib[1], fib[2]])
                    fdb_index += 1
                elif ip.version == 6 and version == "-6":
                    output.append([fdb_index, fib[0], fib[1], fib[2]])
                    fdb_index += 1
        print(tabulate(output, self.HEADER))
        print("Total number of entries {0}".format(len(output)))

def main():

    parser = argparse.ArgumentParser(description='Show dataplane/FIB entries',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-ip', '--ipaddr', type=str,
                        help='dataplane/FIB route for a specific address', default=None)
    parser.add_argument('v', help='IP Version -4 or -6')

    args = parser.parse_args()

    try:
        fib = FibBase()
        fib.display(args.v, args.ipaddr)
    except Exception as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
