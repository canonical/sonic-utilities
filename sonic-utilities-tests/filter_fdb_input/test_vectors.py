"""
    Filter FDB entries test vector
"""
filterFdbEntriesTestVector = [
    {
        "arp":[
        ],
        "fdb": [
        ],
        "config_db": {
        },
        "expected_fdb": [
        ],
    },
    {
        "arp":[
            {
                "NEIGH_TABLE:Vlan1000:192.168.0.10": {
                    "neigh": "72:06:00:01:00:08",
                    "family": "IPv4"
                },
                "OP": "SET"
            },
            {
                "NEIGH_TABLE:Vlan1:25.103.178.129": {
                    "neigh": "50:2f:a8:cb:76:7c",
                    "family": "IPv4"
                },
                "OP": "SET"
            },
        ],
        "fdb": [
            {
                "FDB_TABLE:Vlan1000:72-06-00-01-01-16": {
                    "type": "dynamic",
                    "port": "Ethernet22"
                },
                "OP": "SET"
            },
        ],
        "config_db": {"VLAN": {
            "Vlan1000": {}
        }},
        "expected_fdb": [
        ],
    },
    {
        "arp":[
            {
                "NEIGH_TABLE:Vlan1000:192.168.0.10": {
                    "neigh": "72:06:00:01:01:16",
                    "family": "IPv4"
                },
                "OP": "SET"
            },
            {
                "NEIGH_TABLE:Vlan1:25.103.178.129": {
                    "neigh": "72:06:00:01:01:16",
                    "family": "IPv4"
                },
                "OP": "SET"
            },
        ],
        "fdb": [
            {
                "FDB_TABLE:Vlan1000:72-06-00-01-01-16": {
                    "type": "dynamic",
                    "port": "Ethernet22"
                },
                "OP": "SET"
            },
        ],
        "config_db": {"VLAN": {
            "Vlan1000": {}
        }},
        "expected_fdb": [
            {
                "FDB_TABLE:Vlan1000:72-06-00-01-01-16": {
                    "type": "dynamic",
                    "port": "Ethernet22"
                },
                "OP": "SET"
            },
        ],
    },
    {
        "arp":[
            {
                "NEIGH_TABLE:Vlan1000:192.168.0.10": {
                    "neigh": "72:06:00:01:01:16",
                    "family": "IPv4"
                },
                "OP": "SET"
            },
        ],
        "fdb": [
            {
                "FDB_TABLE:Vlan1000:72-06-00-01-01-16": {
                    "type": "dynamic",
                    "port": "Ethernet22"
                },
                "OP": "SET"
            },
        ],
        "config_db": {"VLAN": {
            "Vlan1": {}
        }},
        "expected_fdb": [
        ],
    },
    {
        "arp":[
            {
                "NEIGH_TABLE:Vlan1000:192.168.0.10": {
                    "neigh": "72:06:00:01:01:16",
                    "family": "IPv4"
                },
                "OP": "SET"
            },
            {
                "NEIGH_TABLE:Vlan1:25.103.178.129": {
                    "neigh": "50:2f:a8:cb:76:7c",
                    "family": "IPv4"
                },
                "OP": "SET"
            },
        ],
        "fdb": [
            {
                "FDB_TABLE:Vlan1:50-2f-a8-cb-76-7c": {
                    "type": "dynamic",
                    "port": "Ethernet22"
                },
                "OP": "SET"
            },
        ],
        "config_db": {"VLAN": {
            "Vlan1": {}
        }},
        "expected_fdb": [
            {
                "FDB_TABLE:Vlan1:50-2f-a8-cb-76-7c": {
                    "type": "dynamic",
                    "port": "Ethernet22"
                },
                "OP": "SET"
            },
        ],
    },
    {
        "arp": "sonic-utilities-tests/filter_fdb_input/arp.json",
        "fdb": "sonic-utilities-tests/filter_fdb_input/fdb.json",
        "config_db": "sonic-utilities-tests/filter_fdb_input/config_db.json",
        "expected_fdb": "sonic-utilities-tests/filter_fdb_input/expected_fdb.json"
    },
    {
        "arp": "sonic-utilities-tests/filter_fdb_input/arp.json",
        "fdb": "sonic-utilities-tests/filter_fdb_input/fdb.json",
        "config_db": {"VLAN": {
            "Vlan1": {}
        }},
        "expected_fdb": [
        ],
    },
    {
        "arp": "sonic-utilities-tests/filter_fdb_input/arp.json",
        "fdb": "sonic-utilities-tests/filter_fdb_input/fdb.json",
        "config_db": {
        },
        "expected_fdb": [
        ],
    },
]
