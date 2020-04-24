import glob
import json
import os
import pytest
import shutil
import subprocess
import sys

from collections import defaultdict

"""
    Filter FDB entries test vector
"""
filterFdbEntriesTestVector = [
    {
        "arp":[
        ],
        "fdb": [
        ],
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
        "arp": "sonic-utilities-tests/filter_fdb_input/arp.json",
        "fdb": "sonic-utilities-tests/filter_fdb_input/fdb.json",
        "expected_fdb": "sonic-utilities-tests/filter_fdb_input/expected_fdb.json"
    },
]

class TestFilterFdbEntries(object):
    """
        Test Filter FDb entries
    """
    ARP_FILENAME = "/tmp/arp.json"
    FDB_FILENAME = "/tmp/fdb.json"
    EXPECTED_FDB_FILENAME = "/tmp/expected_fdb.json"

    def __setUp(self, testData):
        """
            Sets up test data

            Builds arp.json and fdb.json input files to /tmp and also build expected fdb entries files int /tmp

            Args:
                testData(dist): Current test vector data

            Returns:
                None
        """
        def create_file_or_raise(data, filename):
            """
                Create test data files

                If the data is string, it will be dump to a json filename.
                If data is a file, it will be coppied to filename

                Args:
                    data(str|list): source of test data
                    filename(str): filename for test data

                Returns:
                    None

                Raises:
                    Exception if data type is not supported
            """
            if isinstance(data, list):
                with open(filename, 'w') as fp:
                    json.dump(data, fp, indent=2, separators=(',', ': '))
            elif isinstance(data, str):
                shutil.copyfile(data, filename)
            else:
                raise Exception("Unknown test data type: {0}".format(type(test_data)))

        create_file_or_raise(testData["arp"], self.ARP_FILENAME)
        create_file_or_raise(testData["fdb"], self.FDB_FILENAME)
        create_file_or_raise(testData["expected_fdb"], self.EXPECTED_FDB_FILENAME)

    def __tearDown(self):
        """
            Tear down current test case setup

            Args:
                None

            Returns:
                None
        """
        os.remove(self.ARP_FILENAME)
        os.remove(self.EXPECTED_FDB_FILENAME)
        fdbFiles = glob.glob(self.FDB_FILENAME + '*')
        for file in fdbFiles:
            os.remove(file)

    def __runCommand(self, cmds):
        """
            Runs command 'cmds' on host

            Args:
                cmds(list): command to be run on localhost

            Returns:
                stdout(str): stdout gathered during command execution
                stderr(str): stderr gathered during command execution
                returncode(int): command exit code
        """
        process = subprocess.Popen(
            cmds,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        return stdout, stderr, process.returncode

    def __getFdbEntriesMap(self, filename):
        """
            Generate map for FDB entries

            FDB entry map is using the FDB_TABLE:... as a key for the FDB entry.

            Args:
                filename(str): FDB entry file name

            Returns:
                fdbMap(defaultdict) map of FDB entries using MAC as key.
        """
        with open(filename, 'r') as fp:
            fdbEntries = json.load(fp)

        fdbMap = defaultdict()
        for fdb in fdbEntries:
            for key, config in fdb.items():
                if "FDB_TABLE" in key:
                    fdbMap[key] = fdb

        return fdbMap

    def __verifyOutput(self):
        """
            Verifies FDB entries match expected FDB entries

            Args:
                None

            Retruns:
                isEqual(bool): True if FDB entries match, False otherwise
        """
        fdbMap = self.__getFdbEntriesMap(self.FDB_FILENAME)
        with open(self.EXPECTED_FDB_FILENAME, 'r') as fp:
            expectedFdbEntries = json.load(fp)

        isEqual = len(fdbMap) == len(expectedFdbEntries)
        if isEqual:
            for expectedFdbEntry in expectedFdbEntries:
                fdbEntry = {}
                for key, config in expectedFdbEntry.items():
                    if "FDB_TABLE" in key:
                        fdbEntry = fdbMap[key]

                isEqual = len(fdbEntry) == len(expectedFdbEntry)
                for key, config in expectedFdbEntry.items():
                    isEqual = isEqual and fdbEntry[key] == config

                if not isEqual:
                    break

        return isEqual

    @pytest.mark.parametrize("testData", filterFdbEntriesTestVector)
    def testFilterFdbEntries(self, testData):
        """
            Test Filter FDB entries script

            Args:
                testData(dict): Map containing ARP entries, FDB entries, and expected FDB entries
        """
        try:
            self.__setUp(testData)
    
            stdout, stderr, rc = self.__runCommand([
                "scripts/filter_fdb_entries.py",
                "-a",
                self.ARP_FILENAME,
                "-f",
                self.FDB_FILENAME,
            ])
            assert rc == 0, "CFilter_fbd_entries.py failed with '{0}'".format(stderr)
            assert self.__verifyOutput(), "Test failed for test data: {0}".format(testData)
        finally:
            self.__tearDown()
