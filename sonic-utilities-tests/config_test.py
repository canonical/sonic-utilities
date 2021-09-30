import importlib
import os
import traceback
import unittest
from unittest import mock

import click
from click.testing import CliRunner

import config.main as config

load_minigraph_command_output="""\
Stopping SONiC target ...
Running command: /usr/local/bin/sonic-cfggen -H -m --write-to-db
Running command: pfcwd start_default
Running command: config qos reload --no-dynamic-buffer
Restarting SONiC target ...
Reloading Monit configuration ...
Please note setting loaded from minigraph will be lost after system reboot. To preserve setting, run `config save`.
"""

TEST_PATH = os.path.dirname(os.path.abspath(__file__))

load_minigraph_command_output_with_dscp="""\
Stopping SONiC target ...
Running command: /usr/local/bin/sonic-cfggen -H -m --write-to-db
Running command: /usr/local/bin/sonic-cfggen -j {}/everflow_dscp_input/policer.json   --write-to-db
Running command: /usr/local/bin/sonic-cfggen -j {}/everflow_dscp_input/mirror_session.json   --write-to-db
Running command: /usr/local/bin/sonic-cfggen -j {}/everflow_dscp_input/acl_rule.json   --write-to-db
Running command: pfcwd start_default
Running command: config qos reload --no-dynamic-buffer
Restarting SONiC target ...
Reloading Monit configuration ...
Please note setting loaded from minigraph will be lost after system reboot. To preserve setting, run `config save`.
""".format(TEST_PATH, TEST_PATH, TEST_PATH)

def mock_run_command_side_effect(*args, **kwargs):
    command = args[0]

    if kwargs.get('display_cmd'):
        click.echo(click.style("Running command: ", fg='cyan') + click.style(command, fg='green'))

    if kwargs.get('return_cmd'):
        if command == "systemctl list-dependencies --plain sonic-delayed.target | sed '1d'":
            return 'snmp.timer'
        elif command == "systemctl list-dependencies --plain sonic.target | sed '1d'":
            return 'swss'
        else:
            return ''


class TestLoadMinigraph(object):
    @classmethod
    def setup_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "1"
        print("SETUP")
        import config.main
        importlib.reload(config.main)

    def test_load_minigraph(self, get_cmd_module, setup_single_broadcom_asic):
        with mock.patch("utilities_common.cli.run_command", mock.MagicMock(side_effect=mock_run_command_side_effect)) as mock_run_command:
            (config, show) = get_cmd_module
            runner = CliRunner()
            result = runner.invoke(config.config.commands["load_minigraph"], ["-y"])
            print(result.exit_code)
            print(result.output)
            traceback.print_tb(result.exc_info[2])
            assert result.exit_code == 0
            assert "\n".join([l.rstrip() for l in result.output.split('\n')]) == load_minigraph_command_output
            # Verify "systemctl reset-failed" is called for services under sonic.target
            mock_run_command.assert_any_call('systemctl reset-failed swss')
            # Verify "systemctl reset-failed" is called for services under sonic-delayed.target
            mock_run_command.assert_any_call('systemctl reset-failed snmp')
            assert mock_run_command.call_count == 10

    def test_load_minigraph_with_mirror_dscp(self, get_cmd_module, setup_single_broadcom_asic):
        with mock.patch(
            "utilities_common.cli.run_command",
            mock.MagicMock(side_effect=mock_run_command_side_effect)) as mock_run_command:
            with mock.patch("config.main.is_mirror_dscp_present", return_value=True):
                # Verify load_minigraph is completed without error if config files are not present
                runner = CliRunner()
                result = runner.invoke(config.config.commands["load_minigraph"], ["-y"])
                assert result.exit_code == 0
                assert "\n".join([l.rstrip() for l in result.output.split('\n')]) == load_minigraph_command_output
                assert mock_run_command.call_count == 10

                mock_run_command.call_count = 0
                config.DSCP_ACL_RULE_CONFIG_PATH = os.path.join(TEST_PATH, "everflow_dscp_input/acl_rule.json")
                config.DSCP_POLICER_CONFIG_PATH = os.path.join(TEST_PATH, "everflow_dscp_input/policer.json")
                config.DSCP_MIRROR_SESSION_CONFIG_PATH = os.path.join(TEST_PATH, "everflow_dscp_input/mirror_session.json")
                result = runner.invoke(config.config.commands["load_minigraph"], ["-y"])
                assert result.exit_code == 0
                assert "\n".join([l.rstrip() for l in result.output.split('\n')]) == load_minigraph_command_output_with_dscp
                assert mock_run_command.call_count == 13

    @classmethod
    def teardown_class(cls):
        os.environ['UTILITIES_UNIT_TESTING'] = "0"
        print("TEARDOWN")
