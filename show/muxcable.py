import json
import os
import sys

import click
import utilities_common.cli as clicommon

from sonic_py_common import multi_asic, device_info
from swsscommon import swsscommon

platform_sfputil = None

REDIS_TIMEOUT_MSECS = 0


# ==================== Methods for initialization ====================


# Loads platform specific sfputil module from source
def load_platform_sfputil():
    global platform_sfputil

    try:
        import sonic_platform_base.sonic_sfp.sfputilhelper
        platform_sfputil = sonic_platform_base.sonic_sfp.sfputilhelper.SfpUtilHelper()
    except Exception as e:
        click.echo("Failed to instantiate platform_sfputil due to {}".format(repr(e)))
        return -1

    return 0


#
# 'muxcable' command ("show muxcable")
#
@click.group(name='muxcable', cls=clicommon.AliasedGroup)
def muxcable():
    """SONiC command line - 'show muxcable' command"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    # Load platform-specific sfputil class
    err = load_platform_sfputil()
    if err != 0:
        sys.exit(2)

    # Load port info
    try:
        if multi_asic.is_multi_asic():
            # For multi ASIC platforms we pass DIR of port_config_file_path and the number of asics
            (platform_path, hwsku_path) = device_info.get_paths_to_platform_and_hwsku_dirs()

            # Load platform module from source
            platform_sfputil.read_all_porttab_mappings(hwsku_path, multi_asic.get_num_asics())
        else:
            # For single ASIC platforms we pass port_config_file_path and the asic_inst as 0
            port_config_file_path = device_info.get_path_to_port_config_file()
            platform_sfputil.read_porttab_mappings(port_config_file_path, 0)
    except Exception as e:
        log.log_error("Error reading port info (%s)" % str(e), True)
        sys.exit(3)

    return


@muxcable.command()
@click.argument('port', required=False, default=None)
def status(port):
    """Show muxcable summary information"""

    state_db = {}
    y_cable_tbl = {}
    port_table_keys = {}

    # Getting all front asic namespace and correspding config and state DB connector

    namespaces = multi_asic.get_front_end_namespaces()
    for namespace in namespaces:
        asic_id = multi_asic.get_asic_index_from_namespace(namespace)
        state_db[asic_id] = swsscommon.DBConnector("STATE_DB", REDIS_TIMEOUT_MSECS, True, namespace)
        y_cable_tbl[asic_id] = swsscommon.Table(state_db[asic_id], "HW_MUX_CABLE_TABLE_NAME")
        port_table_keys[asic_id] = y_cable_tbl[asic_id].getKeys()

    if port is not None:
        asic_index = platform_sfputil.get_asic_id_for_logical_port(port)
        click.echo("asic_index {} \n".format(asic_index))
        if asic_index is None:
            click.echo("Got invalid asic index for port {}, cant retreive mux status".format(port))
            return

        y_cable_asic_table = y_cable_tbl.get(asic_index, None)
        if y_cable_asic_table is not None:
            y_cable_asic_table_keys = y_cable_asic_table.getKeys()
            if port in y_cable_asic_table_keys:
                port_status_dict = {}
                port_status_dict["mux_cable"] = {}
                (status, fvs) = y_cable_asic_table.get(str(port))
                if status is not True:
                    click.echo("could not retrieve port values for port".format(port))
                fvp = dict(fvs)
                status_value = fvp.get("status", None)
                port_status_dict["mux_cable"][port] = {"status": status_value}

                click.echo("muxcable Ports status : \n {}".format(json.dumps(port_status_dict, indent=4)))
            else:
                click.echo("this is not a valid port present on mux_cable".format(port))
        else:
            click.echo("there is not a valid asic table for this asic_index".format(asic_index))

    else:

        port_status_dict = {}
        port_status_dict["mux_cable"] = {}
        for namespace in namespaces:
            asic_id = multi_asic.get_asic_index_from_namespace(namespace)
            for key in port_table_keys[asic_id]:
                (status, fvs) = y_cable_tbl[asic_id].get(key)
                if status is not True:
                    click.echo("could not retrieve port values for port".format(key))
                fvp = dict(fvs)
                status_value = fvp.get("status", None)
                port_status_dict["mux_cable"][key] = {"status": status_value}

        click.echo("muxcable Ports status : \n {}".format(json.dumps(port_status_dict, indent=4)))


@muxcable.command()
def summary():
    """Show muxcable summary information"""

    state_db = {}
    y_cable_tbl = {}
    port_table_keys = {}

    # Getting all front asic namespace and correspding config and state DB connector

    namespaces = multi_asic.get_front_end_namespaces()
    for namespace in namespaces:
        asic_id = multi_asic.get_asic_index_from_namespace(namespace)
        state_db[asic_id] = swsscommon.DBConnector("STATE_DB", REDIS_TIMEOUT_MSECS, True, namespace)
        y_cable_tbl[asic_id] = swsscommon.Table(state_db[asic_id], "HW_MUX_CABLE_TABLE_NAME")
        port_table_keys[asic_id] = y_cable_tbl[asic_id].getKeys()

    port_status_dict = {}
    port_status_dict["mux_cable"] = {}
    for namespace in namespaces:
        asic_id = multi_asic.get_asic_index_from_namespace(namespace)
        for key in port_table_keys[asic_id]:
            (status, fvs) = y_cable_tbl[asic_id].get(key)
            if status is not True:
                click.echo("could not retrieve port values for port".format(key))
            fvp = dict(fvs)
            status_value = fvp.get("status", None)
            port_status_dict["mux_cable"][key] = {"status": status_value}

    click.echo("muxcable Ports status : \n {}".format(json.dumps(port_status_dict, indent=4)))


