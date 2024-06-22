from unittest import mock
import show.main as show
import pytest
import logging
import importlib
import os
from click.testing import CliRunner
from unittest.mock import patch
from utilities_common.db import Db

from .mock_tables import dbconnector
from .wcmp_input import assert_show_output

test_path = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(test_path, "wcmp_input")
mock_config_path = os.path.join(input_path, "mock_config")

logger = logging.getLogger(__name__)

SUCCESS = 0


class TestWcmpSingleAsic:
    @classmethod
    def setup_class(cls):
        logger.info("Setup class: {}".format(cls.__name__))
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    @classmethod
    def teardown_class(cls):
        logger.info("Teardown class: {}".format(cls.__name__))
        os.environ["UTILITIES_UNIT_TESTING"] = "0"
        dbconnector.dedicated_dbs.clear()

    # ---------- SHOW W-ECMP ---------- #

    @pytest.mark.parametrize("cfgdb,output",
                             [pytest.param(os.path.join(mock_config_path,
                                                        "empty"),
                                           {"plain": assert_show_output.show_wcmp_status_empty,
                                            "json": assert_show_output.show_wcmp_status_empty,
                                            },
                                           id="empty",
                                           ),
                                 pytest.param(os.path.join(mock_config_path,
                                                           "enabled"),
                                              {"plain": assert_show_output.show_wcmp_status_single_enabled,
                                               "json": assert_show_output.show_wcmp_status_single_enabled_json,
                                               },
                                              id="single-asic-enabled",
                                              ),
                                 pytest.param(os.path.join(mock_config_path,
                                                           "disabled"),
                                              {"plain": assert_show_output.show_wcmp_status_single_disabled,
                                               "json": assert_show_output.show_wcmp_status_single_disabled_json,
                                               },
                                              id="single-asic-disabled",
                                              ),
                              ],
                             )
    @pytest.mark.parametrize("format", ["plain", "json"])
    def test_show_wcmp_status_single_asic(self, cfgdb, output, format):
        dbconnector.dedicated_dbs["CONFIG_DB"] = cfgdb

        db = Db()
        runner = CliRunner()

        result = runner.invoke(
            show.cli.commands["w-ecmp"].commands["status"],
            [] if format == "plain" else ["--json"],
            obj=db,
        )

        logger.debug("\n" + result.output)
        logger.debug(result.exit_code)

        assert result.output == output[format]
        assert result.exit_code == SUCCESS


class TestWcmpMultipleAsic:
    @classmethod
    def setup_class(cls):
        logger.info(f"Setup class: {cls.__name__}")
        from .mock_tables import mock_multi_asic

        importlib.reload(mock_multi_asic)
        dbconnector.load_namespace_config()

    @classmethod
    def teardown_class(cls):
        logger.info(f"Teardown class: {cls.__name__}")
        from .mock_tables import mock_single_asic

        importlib.reload(mock_single_asic)
        dbconnector.load_namespace_config()
        dbconnector.namespaces.clear()
        dbconnector.dedicated_dbs.clear()

    @pytest.mark.parametrize("cfgdb,output",
                             [pytest.param({"asic0": os.path.join(mock_config_path,
                                                                  "disabled"),
                                            "asic1": os.path.join(mock_config_path,
                                                                  "disabled"),
                                            },
                                           {"plain": assert_show_output.show_wcmp_status_multi_disabled,
                                            "json": assert_show_output.show_wcmp_status_multi_disabled_json,
                                            },
                                           id="all-disabled",
                                           ),
                                 pytest.param({"asic0": os.path.join(mock_config_path,
                                                                     "enabled"),
                                               "asic1": os.path.join(mock_config_path,
                                                                     "disabled"),
                                               },
                                              {"plain": assert_show_output.show_wcmp_status_multi_asic0_enabled,
                                               "json": assert_show_output.show_wcmp_status_multi_asic0_enabled_json,
                                               },
                                              id="asic0-enabled",
                                              ),
                                 pytest.param({"asic0": os.path.join(mock_config_path,
                                                                     "disabled"),
                                               "asic1": os.path.join(mock_config_path,
                                                                     "enabled"),
                                               },
                                              {"plain": assert_show_output.show_wcmp_status_multi_asic1_enabled,
                                               "json": assert_show_output.show_wcmp_status_multi_asic1_enabled_json,
                                               },
                                              id="asic1-enabled",
                                              ),
                                 pytest.param({"asic0": os.path.join(mock_config_path,
                                                                     "enabled"),
                                               "asic1": os.path.join(mock_config_path,
                                                                     "enabled"),
                                               },
                                              {"plain": assert_show_output.show_wcmp_status_multi_enabled,
                                               "json": assert_show_output.show_wcmp_status_multi_enabled_json,
                                               },
                                              id="both-enabled",
                                              ),
                              ],
                             )
    @pytest.mark.parametrize("format", ["plain", "json"])
    @patch("show.wcmp_cli.multi_asic.is_multi_asic",
           mock.Mock(return_value=True))
    @patch(
        "show.wcmp_cli.multi_asic.get_namespace_list",
        mock.Mock(return_value=["asic0", "asic1"]),
    )
    def test_show_wcmp_status_multi_asic(self, cfgdb, output, format):
        for namespace in cfgdb.keys():
            dbconnector.namespaces[namespace] = {"CONFIG_DB": cfgdb[namespace]}

        runner = CliRunner()
        cmd_args = ["--json"] if format == "json" else []
        result = runner.invoke(
            show.cli.commands["w-ecmp"].commands["status"], cmd_args)

        logger.debug(f"\n{result.output}")
        logger.debug(f"Exit code: {result.exit_code}")

        assert result.output == output[format]
        assert result.exit_code == SUCCESS
