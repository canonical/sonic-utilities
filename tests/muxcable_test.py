import os
import sys
import traceback

import mock_tables.dbconnector
from click.testing import CliRunner
from unittest import mock
from utilities_common.db import Db

sys.modules['sonic_platform_base'] = mock.Mock()
sys.modules['sonic_platform_base.sonic_sfp'] = mock.Mock()
sys.modules['sonic_platform_base.sonic_sfp.sfputilhelper'] = mock.Mock()
sys.modules['sonic_y_cable'] = mock.Mock()
sys.modules['y_cable'] = mock.Mock()
sys.modules['sonic_y_cable.y_cable'] = mock.Mock()
sys.modules['platform_sfputil'] = mock.Mock()
sys.modules['platform_sfputil_helper'] = mock.Mock()
sys.modules['utilities_common.platform_sfputil_helper'] = mock.Mock()
#sys.modules['os'] = mock.Mock()
#sys.modules['os.geteuid'] = mock.Mock()
#sys.modules['platform_sfputil'] = mock.Mock()
import config.main as config
import show.main as show


tabular_data_status_output_expected = """\
PORT        STATUS    HEALTH
----------  --------  --------
Ethernet0   active    HEALTHY
Ethernet4   standby   HEALTHY
Ethernet8   standby   HEALTHY
Ethernet12  unknown   HEALTHY
Ethernet32  active    HEALTHY
"""

json_data_status_output_expected = """\
{
    "MUX_CABLE": {
        "Ethernet0": {
            "STATUS": "active",
            "HEALTH": "HEALTHY"
        },
        "Ethernet4": {
            "STATUS": "standby",
            "HEALTH": "HEALTHY"
        },
        "Ethernet8": {
            "STATUS": "standby",
            "HEALTH": "HEALTHY"
        },
        "Ethernet12": {
            "STATUS": "unknown",
            "HEALTH": "HEALTHY"
        },
        "Ethernet32": {
            "STATUS": "active",
            "HEALTH": "HEALTHY"
        }
    }
}
"""


tabular_data_config_output_expected = """\
SWITCH_NAME    PEER_TOR
-------------  ----------
sonic-switch   10.2.2.2
port        state    ipv4      ipv6
----------  -------  --------  --------
Ethernet0   active   10.2.1.1  e800::46
Ethernet4   auto     10.3.1.1  e801::46
Ethernet8   active   10.4.1.1  e802::46
Ethernet12  active   10.4.1.1  e802::46
Ethernet32  auto     10.1.1.1  fc00::75
"""

json_data_status_config_output_expected = """\
{
    "MUX_CABLE": {
        "PEER_TOR": "10.2.2.2",
        "PORTS": {
            "Ethernet0": {
                "STATE": "active",
                "SERVER": {
                    "IPv4": "10.2.1.1",
                    "IPv6": "e800::46"
                }
            },
            "Ethernet4": {
                "STATE": "auto",
                "SERVER": {
                    "IPv4": "10.3.1.1",
                    "IPv6": "e801::46"
                }
            },
            "Ethernet8": {
                "STATE": "active",
                "SERVER": {
                    "IPv4": "10.4.1.1",
                    "IPv6": "e802::46"
                }
            },
            "Ethernet12": {
                "STATE": "active",
                "SERVER": {
                    "IPv4": "10.4.1.1",
                    "IPv6": "e802::46"
                }
            },
            "Ethernet32": {
                "STATE": "auto",
                "SERVER": {
                    "IPv4": "10.1.1.1",
                    "IPv6": "fc00::75"
                }
            }
        }
    }
}
"""

json_port_data_status_config_output_expected = """\
{
    "MUX_CABLE": {
        "PEER_TOR": "10.2.2.2",
        "PORTS": {
            "Ethernet32": {
                "STATE": "auto",
                "SERVER": {
                    "IPv4": "10.1.1.1",
                    "IPv6": "fc00::75"
                }
            }
        }
    }
}
"""

json_data_config_output_auto_expected = """\
{
    "Ethernet32": "OK",
    "Ethernet0": "OK",
    "Ethernet4": "OK",
    "Ethernet8": "OK",
    "Ethernet12": "OK"
}
"""

json_data_config_output_active_expected = """\
{
    "Ethernet32": "OK",
    "Ethernet0": "OK",
    "Ethernet4": "INPROGRESS",
    "Ethernet8": "OK",
    "Ethernet12": "OK"
}
"""


class TestMuxcable(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")

    def test_muxcable_status(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands["muxcable"].commands["status"], obj=db)

        assert result.exit_code == 102
        assert result.output == tabular_data_status_output_expected

    def test_muxcable_status_json(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["status"], ["--json"], obj=db)

        assert result.exit_code == 102
        assert result.output == json_data_status_output_expected

    def test_muxcable_status_config(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["config"], obj=db)

        assert result.exit_code == 101
        assert result.output == tabular_data_config_output_expected

    def test_muxcable_status_config_json(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["config"], ["--json"], obj=db)

        assert result.exit_code == 101
        assert result.output == json_data_status_config_output_expected

    def test_muxcable_config_json_with_incorrect_port(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["config"], ["Ethernet33", "--json"], obj=db)

        assert result.exit_code == 1

    def test_muxcable_status_json_with_correct_port(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(show.cli.commands["muxcable"].commands["status"], ["Ethernet0", "--json"], obj=db)

        assert result.exit_code == 102

    def test_muxcable_status_json_port_incorrect_index(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 1
            result = runner.invoke(show.cli.commands["muxcable"].commands["status"], ["Ethernet0", "--json"], obj=db)

        assert result.exit_code == 1

    def test_muxcable_status_with_patch(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"], obj=db)

    def test_muxcable_status_json_with_incorrect_port(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(show.cli.commands["muxcable"].commands["status"], ["Ethernet33", "--json"], obj=db)

        assert result.exit_code == 1

    def test_muxcable_config_with_correct_port(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(show.cli.commands["muxcable"].commands["config"], ["Ethernet0"], obj=db)

        assert result.exit_code == 101

    def test_muxcable_config_json_with_correct_port(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(show.cli.commands["muxcable"].commands["config"], ["Ethernet0", "--json"], obj=db)

        assert result.exit_code == 101

    def test_muxcable_config_json_port_with_incorrect_index(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 1
            result = runner.invoke(show.cli.commands["muxcable"].commands["config"], ["Ethernet0", "--json"], obj=db)

        assert result.exit_code == 101

    def test_muxcable_config_json_with_incorrect_port_patch(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(show.cli.commands["muxcable"].commands["config"], ["Ethernet33", "--json"], obj=db)

        assert result.exit_code == 1

    def test_muxcable_status_json_port_eth0(self):
        runner = CliRunner()
        db = Db()
        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(show.cli.commands["muxcable"].commands["status"], ["Ethernet0"], obj=db)

        assert result.exit_code == 102

    def test_config_muxcable_tabular_port_Ethernet8_active(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["active", "Ethernet8"], obj=db)

        assert result.exit_code == 100

    def test_config_muxcable_tabular_port_Ethernet8_auto(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["auto", "Ethernet8"], obj=db)

        assert result.exit_code == 100

    def test_config_muxcable_mode_auto_json(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["auto", "all", "--json"], obj=db)

        assert result.exit_code == 100
        assert result.output == json_data_config_output_auto_expected

    def test_config_muxcable_mode_active_json(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["active", "all", "--json"], obj=db)
        f = open("newfile1", "w")
        f.write(result.output)

        assert result.exit_code == 100
        assert result.output == json_data_config_output_active_expected

    def test_config_muxcable_json_port_auto_Ethernet0(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], [
                                   "auto", "Ethernet0", "--json"], obj=db)

        assert result.exit_code == 100

    def test_config_muxcable_json_port_active_Ethernet0(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], [
                                   "active", "Ethernet0", "--json"], obj=db)

        assert result.exit_code == 100

    def test_config_muxcable_mode_auto_tabular(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["auto", "all"], obj=db)
        assert result.exit_code == 100

    def test_config_muxcable_mode_active_tabular(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["active", "all"], obj=db)
        f = open("newfile", "w")
        f.write(result.output)

        assert result.exit_code == 100

    def test_config_muxcable_tabular_port(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["active", "Ethernet0"], obj=db)

        assert result.exit_code == 100

    def test_config_muxcable_tabular_port_Ethernet4_active(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["active", "Ethernet4"], obj=db)

        assert result.exit_code == 100

    def test_config_muxcable_tabular_port_Ethernet4_auto(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["auto", "Ethernet4"], obj=db)

        assert result.exit_code == 100

    def test_config_muxcable_tabular_port_with_incorrect_index(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 2
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], ["active", "Ethernet0"], obj=db)

        assert result.exit_code == 1

    def test_config_muxcable_tabular_port_with_incorrect_port_index(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 7
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], [
                                   "active", "Ethernet33"], obj=db)

        assert result.exit_code == 1

    def test_config_muxcable_tabular_port_with_incorrect_port(self):
        runner = CliRunner()
        db = Db()

        with mock.patch('sonic_platform_base.sonic_sfp.sfputilhelper') as patched_util:
            patched_util.SfpUtilHelper.return_value.get_asic_id_for_logical_port.return_value = 0
            result = runner.invoke(config.config.commands["muxcable"].commands["mode"], [
                                   "active", "Ethernet33"], obj=db)

        assert result.exit_code == 1

    @mock.patch('os.geteuid', mock.MagicMock(return_value=0))
    @mock.patch('sonic_y_cable.y_cable.get_eye_info', mock.MagicMock(return_value=[0, 0]))
    def test_show_muxcable_eye_info(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["eyeinfo"],
                               ["0", "0"], obj=db)

        assert result.exit_code == 0

    @mock.patch('os.geteuid', mock.MagicMock(return_value=0))
    @mock.patch('sonic_y_cable.y_cable.get_ber_info', mock.MagicMock(return_value=[0, 0]))
    def test_show_muxcable_ber_info(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["berinfo"],
                               ["0", "0"], obj=db)

        assert result.exit_code == 0

    @mock.patch('os.geteuid', mock.MagicMock(return_value=0))
    @mock.patch('sonic_y_cable.y_cable.enable_prbs_mode', mock.MagicMock(return_value=1))
    def test_config_muxcable_enable_prbs(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["muxcable"].commands["prbs"].commands["enable"],
                               ["0", "0", "0", "0"], obj=db)

        assert result.exit_code == 100

    @mock.patch('os.geteuid', mock.MagicMock(return_value=0))
    @mock.patch('sonic_y_cable.y_cable.enable_loopback_mode', mock.MagicMock(return_value=1))
    def test_config_muxcable_enable_loopback(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["muxcable"].commands["loopback"].commands["enable"],
                               ["0", "0", "0"], obj=db)

        assert result.exit_code == 100

    @mock.patch('os.geteuid', mock.MagicMock(return_value=0))
    @mock.patch('sonic_y_cable.y_cable.disable_prbs_mode', mock.MagicMock(return_value=1))
    def test_config_muxcable_disble_prbs(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["muxcable"].commands["prbs"].commands["disable"],
                               ["0", "0"], obj=db)

        assert result.exit_code == 100

    @mock.patch('os.geteuid', mock.MagicMock(return_value=0))
    @mock.patch('sonic_y_cable.y_cable.disable_loopback_mode', mock.MagicMock(return_value=1))
    def test_config_muxcable_disable_loopback(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(config.config.commands["muxcable"].commands["loopback"].commands["disable"],
                               ["0", "0"], obj=db)

        assert result.exit_code == 100

    @mock.patch('sonic_y_cable.y_cable.get_pn_number_and_vendor_name', mock.MagicMock(return_value=(bytearray(b'CACL1X321P2PA1M'), bytearray(b'Credo          '))))
    @mock.patch('show.muxcable.platform_sfputil', mock.MagicMock(return_value=1))
    @mock.patch('utilities_common.platform_sfputil_helper.logical_port_name_to_physical_port_list', mock.MagicMock(return_value=[0]))
    def test_show_muxcable_cableinfo(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["cableinfo"],
                               ["Ethernet0"], obj=db)

        assert result.exit_code == 0

    @mock.patch('sonic_y_cable.y_cable.get_pn_number_and_vendor_name', mock.MagicMock(return_value=(False)))
    @mock.patch('show.muxcable.platform_sfputil', mock.MagicMock(return_value=1))
    @mock.patch('utilities_common.platform_sfputil_helper.logical_port_name_to_physical_port_list', mock.MagicMock(return_value=[0]))
    def test_show_muxcable_cableinfo_incorrect_port(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["cableinfo"],
                               ["Ethernet0"], obj=db)
        assert result.exit_code == 1

    @mock.patch('sonic_y_cable.y_cable.get_pn_number_and_vendor_name', mock.MagicMock(return_value=(False)))
    @mock.patch('show.muxcable.platform_sfputil', mock.MagicMock(return_value=1))
    @mock.patch('utilities_common.platform_sfputil_helper.logical_port_name_to_physical_port_list', mock.MagicMock(return_value=0))
    def test_show_muxcable_cableinfo_incorrect_port_return_value(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["cableinfo"],
                               ["Ethernet0"], obj=db)
        assert result.exit_code == 1

    @mock.patch('sonic_y_cable.y_cable.get_pn_number_and_vendor_name', mock.MagicMock(return_value=(False)))
    @mock.patch('show.muxcable.platform_sfputil', mock.MagicMock(return_value=1))
    @mock.patch('utilities_common.platform_sfputil_helper.logical_port_name_to_physical_port_list', mock.MagicMock(return_value=[0,1]))
    def test_show_muxcable_cableinfo_incorrect_logical_port_return_value(self):
        runner = CliRunner()
        db = Db()

        result = runner.invoke(show.cli.commands["muxcable"].commands["cableinfo"],
                               ["Ethernet0"], obj=db)
        assert result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
