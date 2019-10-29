#!/usr/bin/env python
""" JSON based configlet update

A tool to update CONFIG-DB with JSON diffs that can update/delete redis-DB.

All elements in the list are processed in the same order as it is present.
Within an entry in the list, the tables are handled in any order.
Within a table, the keys are handled in any order.



A sample for delete a field TABLE1|KEY1|Key2:field1
[
    {
        "TABLE1": {
            "Key1": {
                "Key2": {
                    "Field1": "Val1"
                }
            }
        }
    }
],

A sample for update 
[
    {
        "TABLE1": {
            "Key1": {
                "Key2": {
                    "Field1": "Val1",
                    "Field2": "Val2",
                    "Field3": "Val3"
                },
                "Key2_1": {
                    "Field2_1": "Val1",
                    "Field2_2": "Val2",
                    "Field2_3": "Val3"
                }
            }
        }
    },
    {
        "TABLE1": {
            "Key1": {
                "Key2": {
                    "Field4": "Val2"
                }
            }
        }
    }
]

A sample for delete entire TABLE2:
[
    {
        "TABLE2": {
        }
    }
]

A sample for update:
[
    {
        "TABLE2": {
            "Key22_1": {
                "Key22_2": {
                    "Field22_2": "Val22_2"
                }
            }
        }
    }
]


"""

from __future__ import print_function
import sys
import os.path
import argparse
import json
import time
from collections import OrderedDict
from natsort import natsorted
from swsssdk import ConfigDBConnector

test_only = False

connected = False

db = ConfigDBConnector()

def init():
    global connected

    if connected == False:
        db.connect(False)
        connected = True

def db_update(t, k, lst):
    init()
    db.mod_entry(t, k, lst)

def db_filtered_upd(t, k, lst):
    init()
    data = db.get_entry(t, k)
    for i in lst.keys():
        data.pop(i)
    db.set_entry(t, k, data)


def db_delete_deep(t, k):
    if not k:
        db.delete_table(t)
    else:
        db.mod_entry(t, k, None)

def db_delete(t, k, lst):
    init()
    if lst:
        db_filtered_upd(t, k, lst)
    else:
        db_delete_deep(t, k)

def do_update(t, k, lst):
    if test_only == False:
        db_update(t, k, lst)
    else:
        print ("TEST update")
        print ("table: " + t)
        print ("key: " + str(k))
        print (lst)
        print ("---------------------")

def do_delete(t, k, lst):
    if test_only == False:
        db_delete(t, k, lst)
    else:
        print ("TEST delete")
        print ("table: " + t)
        print ("key: " + str(k))
        print (lst)
        print ("---------------------")


def do_operate(op_upd, t, k, lst):
    if lst:
        if type(lst[lst.keys()[0]]) == dict:
            for i in lst:
                do_operate(op_upd, t, k+(i,), lst[i])
            return

    if op_upd:
        do_update(t, k, lst)
    else:
        do_delete(t, k, lst)


def process_entry(op_upd, data):
    for t in data.keys():
        do_operate(op_upd, t, (), data[t])

def main():
    global test_only

    parser=argparse.ArgumentParser(description="Manage configlets for CUD (Update & Delete")
    parser.add_argument("-j", "--json", help="json file that contains configlet", action='append')
    parser.add_argument("-t", "--test", help="Test only", action='store_true', default=False)
    parser.add_argument("-p", "--parse", help="Parse JSON only", action='store_true', default=False)
    parser.add_argument("-u", "--update", help="Apply the JSON as update", action='store_true', default=False)
    parser.add_argument("-d", "--delete", help="Apply the JSON as delete", action='store_true', default=False)

    args = parser.parse_args()

    test_only = args.test
    parse_only = args.parse
    do_update = args.update
    do_delete = args.delete

    do_act = test_only | parse_only | do_update | do_delete
    if not do_act:
        print ("Expect an action update/delete or for debug parse/test\n")
        parser.print_help()
        exit(-1)

    for json_file in args.json:
        with open(json_file, 'r') as stream:
            data = json.load(stream)
            if parse_only == False:
                for i in data:
                    process_entry (do_update, i)
                    # Artificial sleep to give a pause between two entries
                    # so as to ensure that all internal daemons have digested the 
                    # previous update, before the next one arrives.
                    #
                    time.sleep(3)
            else:
                print("Parsed:")
                print(data)


if __name__ == "__main__":
    main()

