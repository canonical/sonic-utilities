import os
import traceback
from unittest import mock
from mock import patch

from click.testing import CliRunner
from jsonpatch import JsonPatchConflict

import config.main as config
import config.validated_config_db_connector as validated_config_db_connector
from utilities_common.db import Db
import utilities_common.bgp_util as bgp_util

class TestConfigVRRP(object):
    _old_run_bgp_command = None
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        cls._old_run_bgp_command = bgp_util.run_bgp_command
        bgp_util.run_bgp_command = mock.MagicMock(
            return_value=cls.mock_run_bgp_command())
        print("SETUP")

    ''' Tests for VRRPv4 and VRRPv6  '''

    def mock_run_bgp_command():
        return ""
    
    def test_add_del_vrrp_instance_without_vip(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp add Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["add"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["add"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["add"], ["Ethernet2", "7"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_add_del_vrrp6_instance_without_vip(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 100::64/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "100::64/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '100::64/64') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp6 add Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["add"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["add"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["add"], ["Ethernet2", "7"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int vrrp6 remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP6')

        # config int ip remove Ethernet64 100::64/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "100::64/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '100::64/64') not in db.cfgdb.get_table('INTERFACE')

    def test_add_del_vrrp_instance(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["add"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["add"], ["Ethernet2", "7"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int vrrp ip add Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24']

        # config int vrrp ip add Ethernet64 8 10.10.10.16/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.16/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24', '10.10.10.16/24']

        # config int vrrp ip remove Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["remove"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.16/24']

        # config int vrrp ip remove Ethernet64 8 10.10.10.16/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["remove"], ["Ethernet64", "8", "10.10.10.16/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['']

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet2", "7"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int vrrp remove Ethernet63 9
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet63", "9"], obj=obj)
        print(result.exit_code, result.output)
        assert "Ethernet63 dose not configured the vrrp instance 9" in result.output
        assert result.exit_code == 0

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_add_del_vrrp6_instance(self):
        runner = CliRunner()
        db = Db()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 100::1/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "100::1/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '100::1/64') in db.cfgdb.get_table('INTERFACE')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["add"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["add"], ["Ethernet2", "7"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int vrrp6 ipv6 add Ethernet64 8 100::8/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["add"], ["Ethernet64", "8", "100::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['100::8/64']

        # config int vrrp6 ipv6 add Ethernet64 8 100::16/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["add"], ["Ethernet64", "8", "100::16/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['100::8/64', '100::16/64']

        # config int vrrp6 ipv6 remove Ethernet64 8 100::8/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["remove"], ["Ethernet64", "8", "100::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['100::16/64']

        # config int vrrp6 ipv6 remove Ethernet64 8 100::16/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["remove"], ["Ethernet64", "8", "100::16/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['']

        # config int vrrp6 remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP6')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet2", "7"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int vrrp remove Ethernet63 9
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet63", "9"], obj=obj)
        print(result.exit_code, result.output)
        assert "Ethernet63 dose not configured the vrrp instance 9" in result.output
        assert result.exit_code == 0

        # config int ip remove Ethernet64 100::1/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "100::1/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '100::1/64') not in db.cfgdb.get_table('INTERFACE')

    def test_add_del_vrrp_instance_track_intf(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int ip add Ethernet5 10.10.10.5/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet5", "10.10.10.5/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet5', '10.10.10.5/24') in db.cfgdb.get_table('INTERFACE')

        # config int ip add Ethernet6 10.10.10.6/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet6", "10.10.10.6/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet6', '10.10.10.6/24') in db.cfgdb.get_table('INTERFACE')

        # config int ip add Ethernet7 10.10.10.7/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet7", "10.10.10.7/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet7', '10.10.10.7/24') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp ip add Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["add"], ["Ethernet-64", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["add"], ["Ethernet2", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet-5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'track_interface' is not valid." in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet2", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config interface vrrp track_interface add Ethernet64 8 Ethernet5 20
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet5') in db.cfgdb.get_table('VRRP_TRACK')
        assert db.cfgdb.get_table('VRRP_TRACK')['Ethernet64', '8', 'Ethernet5']['priority_increment'] == '20'

        # config interface vrrp track_interface add Ethernet64 8 Ethernet6 30
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet6", "30"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet6') in db.cfgdb.get_table('VRRP_TRACK')
        assert db.cfgdb.get_table('VRRP_TRACK')['Ethernet64', '8', 'Ethernet6']['priority_increment'] == '30'

        # config interface vrrp track_interface add Ethernet64 8 Ethernet7 80
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet7", "80"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        # config interface vrrp track_interface remove Ethernet64 8 Ethernet6
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet6"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet6') not in db.cfgdb.get_table('VRRP_TRACK')

        # config interface vrrp track_interface remove Ethernet64 8 Ethernet5
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet5"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet5') not in db.cfgdb.get_table('VRRP_TRACK')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["remove"], ["Ethernet-64", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["remove"], ["Ethernet2", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet-5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'track_interface' is not valid." in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet2", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # config int ip remove Ethernet7 10.10.10.7/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet7", "10.10.10.7/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet7', '10.10.10.7/24') not in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet6 10.10.10.6/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet6", "10.10.10.6/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet6', '10.10.10.6/24') not in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet5 10.10.10.5/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet5", "10.10.10.5/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet5', '10.10.10.5/24') not in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_add_del_vrrp6_instance_track_intf(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 100::64/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "100::64/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '100::64/64') in db.cfgdb.get_table('INTERFACE')

        # config int ip add Ethernet5 100::5/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet5", "100::5/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet5', '100::5/64') in db.cfgdb.get_table('INTERFACE')

        # config int ip add Ethernet6 100::6/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet6", "100::6/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet6', '100::6/64') in db.cfgdb.get_table('INTERFACE')

        # config int ip add Ethernet7 100::7/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet7", "100::7/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet7', '100::7/64') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp6 ipv6 add Ethernet64 8 100::1/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["add"], ["Ethernet64", "8", "100::1/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['100::1/64']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["add"], ["Ethernet-64", "8", "Ethernet", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["add"], ["Ethernet2", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet-5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'track_interface' is not valid." in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet2", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config interface vrrp6 track_interface add Ethernet64 8 Ethernet5 20
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet5') in db.cfgdb.get_table('VRRP6_TRACK')
        assert db.cfgdb.get_table('VRRP6_TRACK')['Ethernet64', '8', 'Ethernet5']['priority_increment'] == '20'

        # config interface vrrp6 track_interface add Ethernet64 8 Ethernet6 30
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet6", "30"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet6') in db.cfgdb.get_table('VRRP6_TRACK')
        assert db.cfgdb.get_table('VRRP6_TRACK')['Ethernet64', '8', 'Ethernet6']['priority_increment'] == '30'

        # config interface vrrp6 track_interface add Ethernet64 8 Ethernet7 80
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["add"], ["Ethernet64", "8", "Ethernet7", "80"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        # config interface vrrp6 track_interface remove Ethernet64 8 Ethernet6
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet6"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet6') not in db.cfgdb.get_table('VRRP6_TRACK')

        # config interface vrrp6 track_interface remove Ethernet64 8 Ethernet5
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet5"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8', 'Ethernet5') not in db.cfgdb.get_table('VRRP6_TRACK')

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["remove"], ["Ethernet-64", "8", "Ethernet", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["remove"], ["Ethernet2", "8", "Ethernet5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet-5", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "'track_interface' is not valid." in result.output
        assert result.exit_code == 0

        # check track_interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["track_interface"].commands["remove"], ["Ethernet64", "8", "Ethernet2", "20"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # config int vrrp6 remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP6')

        # config int ip remove Ethernet7 100::7/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet7", "100::7/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet7', '100::7/64') not in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet6 100::6/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet6", "100::6/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet6', '100::6/64') not in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet5 100::5/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet5", "100::5/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet5', '100::5/64') not in db.cfgdb.get_table('INTERFACE')

        # config int ip remove Ethernet64 100::64/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "100::64/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '100::64/64') not in db.cfgdb.get_table('INTERFACE')

    def test_enable_disable_vrrp_instance_preempt(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp ip add Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["pre_empt"], ["Ethernet-64", "8", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["pre_empt"], ["Ethernet2", "8", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["pre_empt"], ["Ethernet64", "9", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert "vrrp instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp vrrp pre_empt Ethernet64 8 disabled
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["pre_empt"], ["Ethernet64", "8", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['preempt'] == 'disabled'

        # config interface vrrp vrrp pre_empt Ethernet64 8 enabled
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["pre_empt"], ["Ethernet64", "8", "enabled"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['preempt'] == 'enabled'

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_enable_disable_vrrp6_instance_preempt(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10::8/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10::8/64') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp6 ipv6 add Ethernet64 8 10::1/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["add"], ["Ethernet64", "8", "10::1/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['10::1/64']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["pre_empt"], ["Ethernet-64", "8", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["pre_empt"], ["Ethernet2", "8", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp6 instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["pre_empt"], ["Ethernet64", "9", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert "Vrrpv6 instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp6 pre_empt Ethernet64 8 disabled
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["pre_empt"], ["Ethernet64", "8", "disabled"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['preempt'] == 'disabled'

        # config interface vrrp vrrp pre_empt Ethernet64 8 enabled
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["pre_empt"], ["Ethernet64", "8", "enabled"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['preempt'] == 'enabled'

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP6')

        # config int ip remove Ethernet64 10::8/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10::8/64') not in db.cfgdb.get_table('INTERFACE')

    def test_config_vrrp_instance_adv_interval(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp ip add Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["adv_interval"], ["Ethernet-64", "8", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["adv_interval"], ["Ethernet2", "8", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["adv_interval"], ["Ethernet64", "9", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert "vrrp instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp vrrp adv_interval Ethernet64 8 2000
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["adv_interval"], ["Ethernet64", "8", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['adv_interval'] == '2000'

        # config interface vrrp vrrp adv_interval Ethernet64 8 5
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["adv_interval"], ["Ethernet64", "8", "5"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_config_vrrp6_instance_adv_interval(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10::8/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10::8/64') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp6 ipv6 add Ethernet64 8 10::1/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["add"], ["Ethernet64", "8", "10::1/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['10::1/64']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["adv_interval"], ["Ethernet-64", "8", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["adv_interval"], ["Ethernet2", "8", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["adv_interval"], ["Ethernet64", "9", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert "Vrrpv6 instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp6 adv_interval Ethernet64 8 2000
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["adv_interval"], ["Ethernet64", "8", "2000"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['adv_interval'] == '2000'

        # config interface vrrp6 adv_interval Ethernet64 8 5
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["adv_interval"], ["Ethernet64", "8", "5"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        # config int vrrp6 remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP6')

        # config int ip remove Ethernet64 10::8/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10::8/64') not in db.cfgdb.get_table('INTERFACE')

    def test_config_vrrp_instance_priority(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp ip add Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["priority"], ["Ethernet-64", "8", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["priority"], ["Ethernet2", "8", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["priority"], ["Ethernet64", "9", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert "vrrp instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp priority Ethernet64 8 150
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["priority"], ["Ethernet64", "8", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['priority'] == '150'

        # config interface vrrp priority Ethernet64 8 256
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["priority"], ["Ethernet64", "8", "256"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_config_vrrp6_instance_priority(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10::8/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10::8/64') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp6 ipv6 add Ethernet64 8 10::1/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["add"], ["Ethernet64", "8", "10::1/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['10::1/64']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["priority"], ["Ethernet-64", "8", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["priority"], ["Ethernet2", "8", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["priority"], ["Ethernet64", "9", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert "Vrrpv6 instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp6 priority Ethernet64 8 150
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["priority"], ["Ethernet64", "8", "150"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['priority'] == '150'

        # config interface vrrp priority Ethernet64 8 256
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["priority"], ["Ethernet64", "8", "256"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        # config int vrrp6 remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP6')

        # config int ip remove Ethernet64 10::8/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10::8/64') not in db.cfgdb.get_table('INTERFACE')

    def test_config_vrrp_instance_version(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp ip add Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["version"], ["Ethernet-64", "8", "3"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["version"], ["Ethernet2", "8", "3"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["version"], ["Ethernet64", "9", "3"], obj=obj)
        print(result.exit_code, result.output)
        assert "vrrp instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp version Ethernet64 8 3
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["version"], ["Ethernet64", "8", "3"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['version'] == '3'

        # config interface vrrp version Ethernet64 8 1
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["version"], ["Ethernet64", "8", "1"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_config_vrrp_instance_shutdown_and_startup(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10.10.10.1/24') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp ip add Ethernet64 8 10.10.10.8/24
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["ip"].commands["add"], ["Ethernet64", "8", "10.10.10.8/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['vip'] == ['10.10.10.8/24']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["shutdown"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["shutdown"], ["Ethernet2", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["shutdown"], ["Ethernet64", "9"], obj=obj)
        print(result.exit_code, result.output)
        assert "vrrp instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp shutdown Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["shutdown"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['admin_status'] == 'down'

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["startup"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["startup"], ["Ethernet2", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["startup"], ["Ethernet64", "9"], obj=obj)
        print(result.exit_code, result.output)
        assert "vrrp instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp startup Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["startup"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP')
        assert db.cfgdb.get_table('VRRP')['Ethernet64', '8']['admin_status'] == 'up'

        # config int vrrp remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP')

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')

    def test_config_vrrp6_instance_shutdown_and_startup(self):
        db = Db()
        runner = CliRunner()
        obj = {'config_db':db.cfgdb}

        # config int ip add Ethernet64 10::8/64
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["add"], ["Ethernet64", "10::8/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '10::8/64') in db.cfgdb.get_table('INTERFACE')

        # config int vrrp6 ipv6 add Ethernet64 8 10::1/64
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["ipv6"].commands["add"], ["Ethernet64", "8", "10::1/64"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['vip'] == ['10::1/64']

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["shutdown"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["shutdown"], ["Ethernet2", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["shutdown"], ["Ethernet64", "9"], obj=obj)
        print(result.exit_code, result.output)
        assert "Vrrpv6 instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp shutdown Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["shutdown"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['admin_status'] == 'down'

        # check interface_name is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["startup"], ["Ethernet-64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "'interface_name' is not valid" in result.output
        assert result.exit_code == 0

        # check interface is Router interface
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["startup"], ["Ethernet2", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert "Router Interface 'Ethernet2' not found" in result.output
        assert result.exit_code == 0

        # check the vrrp6 instance is valid
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["startup"], ["Ethernet64", "9"], obj=obj)
        print(result.exit_code, result.output)
        assert "Vrrpv6 instance 9 not found on interface Ethernet64" in result.output
        assert result.exit_code == 0

        # config interface vrrp6 startup Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["startup"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') in db.cfgdb.get_table('VRRP6')
        assert db.cfgdb.get_table('VRRP6')['Ethernet64', '8']['admin_status'] == 'up'

        # config int vrrp6 remove Ethernet64 8
        result = runner.invoke(config.config.commands["interface"].commands["vrrp6"].commands["remove"], ["Ethernet64", "8"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code == 0
        assert ('Ethernet64', '8') not in db.cfgdb.get_table('VRRP6')

        # config int ip remove Ethernet64 10.10.10.1/24
        result = runner.invoke(config.config.commands["interface"].commands["ip"].commands["remove"], ["Ethernet64", "10.10.10.1/24"], obj=obj)
        print(result.exit_code, result.output)
        assert result.exit_code != 0
        assert ('Ethernet64', '10.10.10.1/24') not in db.cfgdb.get_table('INTERFACE')
