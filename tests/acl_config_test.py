import pytest

import config.main as config
import show.main as show

from click.testing import CliRunner
from config.main import expand_vlan_ports, parse_acl_table_info
from utilities_common.db import Db

class TestConfigAcl(object):
    def test_expand_vlan(self):
        assert set(expand_vlan_ports("Vlan1000")) == {"Ethernet4", "Ethernet8", "Ethernet12", "Ethernet16"}

    def test_expand_lag(self):
        assert set(expand_vlan_ports("PortChannel1001")) == {"PortChannel1001"}

    def test_expand_physical_interface(self):
        assert set(expand_vlan_ports("Ethernet4")) == {"Ethernet4"}

    def test_expand_empty_vlan(self):
        with pytest.raises(ValueError):
            expand_vlan_ports("Vlan3000")

    def test_parse_table_with_vlan_expansion(self):
        table_info = parse_acl_table_info("TEST", "L3", None, "Vlan1000", "egress")
        assert table_info["type"] == "L3"
        assert table_info["policy_desc"] == "TEST"
        assert table_info["stage"] == "egress"
        assert set(table_info["ports"]) == {"Ethernet4", "Ethernet8", "Ethernet12", "Ethernet16"}

    def test_parse_table_with_vlan_and_duplicates(self):
        table_info = parse_acl_table_info("TEST", "L3", None, "Ethernet4,Vlan1000", "egress")
        assert table_info["type"] == "L3"
        assert table_info["policy_desc"] == "TEST"
        assert table_info["stage"] == "egress"

        # Since Ethernet4 is a member of Vlan1000 we should not include it twice in the output
        port_set = set(table_info["ports"])
        assert len(port_set) == 4
        assert set(port_set) == {"Ethernet4", "Ethernet8", "Ethernet12", "Ethernet16"}

    def test_parse_table_with_empty_vlan(self):
        with pytest.raises(ValueError):
            parse_acl_table_info("TEST", "L3", None, "Ethernet4,Vlan3000", "egress")

    def test_parse_table_with_invalid_ports(self):
        with pytest.raises(ValueError):
            parse_acl_table_info("TEST", "L3", None, "Ethernet200", "egress")

    def test_parse_table_with_empty_ports(self):
        with pytest.raises(ValueError):
            parse_acl_table_info("TEST", "L3", None, "", "egress")

    def test_acl_add_table_nonexistent_port(self):
        runner = CliRunner()

        result = runner.invoke(
            config.config.commands["acl"].commands["add"].commands["table"],
            ["TEST", "L3", "-p", "Ethernet200"])

        assert result.exit_code != 0
        assert "Cannot bind ACL to specified port Ethernet200" in result.output

    def test_acl_add_table_empty_string_port_list(self):
        runner = CliRunner()

        result = runner.invoke(
            config.config.commands["acl"].commands["add"].commands["table"],
            ["TEST", "L3", "-p", ""])

        assert result.exit_code != 0
        assert "Cannot bind empty list of ports" in result.output

    def test_acl_add_table_empty_vlan(self):
        runner = CliRunner()

        result = runner.invoke(
            config.config.commands["acl"].commands["add"].commands["table"],
            ["TEST", "L3", "-p", "Vlan3000"])

        assert result.exit_code != 0
        assert "Cannot bind empty VLAN Vlan3000" in result.output

    def test_acl_show_runningconfiguration(self):
        runner = CliRunner()
        db = Db()
        table_info = parse_acl_table_info("TEST", "L3", None, "Ethernet20", "ingress")
        db.cfgdb.set_entry("ACL_TABLE", "TEST", table_info)
        result = runner.invoke(show.cli.commands["runningconfiguration"].commands["acl"], [], obj=db)
        print(result.exit_code)
        print(result.output)
        #assert result.exit_code == 0
        #assert "TEST" in result.output
