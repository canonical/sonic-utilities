import click
import utilities_common.cli as clicommon

from jsonpatch import JsonPatchConflict
from time import sleep
from .utils import log
from .validated_config_db_connector import ValidatedConfigDBConnector

ADHOC_VALIDATION = True


#
# 'vlan' group ('config vlan ...')
#


@click.group(cls=clicommon.AbbreviationGroup, name='vlan')
def vlan():
    """VLAN-related configuration tasks"""
    pass


@vlan.command('add')
@click.argument('vid', metavar='<vid>', required=True)
@click.option('-m', '--multiple', is_flag=True, help="Add Multiple Vlans.")
@clicommon.pass_db
def add_vlan(db, vid, multiple):
    """Add VLAN"""

    ctx = click.get_current_context()
    config_db = ValidatedConfigDBConnector(db.cfgdb)

    vid_list = []
    # parser will parse the vid input if there are syntax errors it will throw error
    if multiple:
        vid_list = clicommon.multiple_vlan_parser(ctx, vid)
    else:
        if not vid.isdigit():
            ctx.fail("{} is not integer".format(vid))
        vid_list.append(int(vid))

    if ADHOC_VALIDATION:

        # loop will execute till an exception occurs
        for vid in vid_list:

            vlan = 'Vlan{}'.format(vid)

            # default vlan checker
            if vid == 1:
                # TODO: MISSING CONSTRAINT IN YANG MODEL
                ctx.fail("{} is default VLAN.".format(vlan))

            log.log_info("'vlan add {}' executing...".format(vid))

            if not clicommon.is_vlanid_in_range(vid):
                ctx.fail("Invalid VLAN ID {} (2-4094)".format(vid))

            # TODO: MISSING CONSTRAINT IN YANG MODEL
            if clicommon.check_if_vlanid_exist(db.cfgdb, vlan):
                log.log_info("{} already exists".format(vlan))
                ctx.fail("{} already exists".format(vlan))

            try:
                config_db.set_entry('VLAN', vlan, {'vlanid': str(vid)})
                click.echo("Vlan{} has been added".format(vid))
            except ValueError:
                ctx.fail("Invalid VLAN ID {} (2-4094)".format(vid))


@vlan.command('del')
@click.argument('vid', metavar='<vid>', required=True)
@click.option('-m', '--multiple', is_flag=True, help="Add Multiple Vlans.")
@clicommon.pass_db
def del_vlan(db, vid, multiple):
    """Delete VLAN"""

    ctx = click.get_current_context()
    config_db = ValidatedConfigDBConnector(db.cfgdb)

    vid_list = []
    # parser will parse the vid input if there are syntax errors it will throw error
    if multiple:
        vid_list = clicommon.multiple_vlan_parser(ctx, vid)
    else:
        if not vid.isdigit():
            ctx.fail("{} is not integer".format(vid))
        vid_list.append(int(vid))

    if ADHOC_VALIDATION:
        # loop will execute till an exception occurs
        for vid in vid_list:

            log.log_info("'vlan del {}' executing...".format(vid))

            if not clicommon.is_vlanid_in_range(vid):
                ctx.fail("Invalid VLAN ID {} (2-4094)".format(vid))

            vlan = 'Vlan{}'.format(vid)
            if clicommon.check_if_vlanid_exist(db.cfgdb, vlan) == False:
                log.log_info("{} does not exist".format(vlan))
                ctx.fail("{} does not exist".format(vlan))

            intf_table = db.cfgdb.get_table('VLAN_INTERFACE')
            for intf_key in intf_table:
                if ((type(intf_key) is str and intf_key == 'Vlan{}'.format(vid)) or  # TODO: MISSING CONSTRAINT IN YANG MODEL
                        (type(intf_key) is tuple and intf_key[0] == 'Vlan{}'.format(vid))):
                    ctx.fail("{} can not be removed. First remove IP addresses assigned to this VLAN".format(vlan))

            keys = [(k, v) for k, v in db.cfgdb.get_table('VLAN_MEMBER') if k == 'Vlan{}'.format(vid)]

            if keys:  # TODO: MISSING CONSTRAINT IN YANG MODEL
                ctx.fail("VLAN ID {} can not be removed. First remove all members assigned to this VLAN.".format(vid))

            vxlan_table = db.cfgdb.get_table('VXLAN_TUNNEL_MAP')
            for vxmap_key, vxmap_data in vxlan_table.items():
                if vxmap_data['vlan'] == 'Vlan{}'.format(vid):
                    ctx.fail("vlan: {} can not be removed. First remove vxlan mapping '{}' assigned to VLAN".format(vid, '|'.join(vxmap_key)))
            try:
                config_db.set_entry('VLAN', 'Vlan{}'.format(vid), None)
                click.echo("Vlan{} has deleted added".format(vid))
            except JsonPatchConflict:
                ctx.fail("{} does not exist".format(vlan))
                


def restart_ndppd():
    verify_swss_running_cmd = "docker container inspect -f '{{.State.Status}}' swss"
    docker_exec_cmd = "docker exec -i swss {}"
    ndppd_config_gen_cmd = "sonic-cfggen -d -t /usr/share/sonic/templates/ndppd.conf.j2,/etc/ndppd.conf"
    ndppd_restart_cmd = "supervisorctl restart ndppd"

    output = clicommon.run_command(verify_swss_running_cmd, return_cmd=True)

    if output and output.strip() != "running":
        click.echo(click.style('SWSS container is not running, changes will take effect the next time the SWSS container starts', fg='red'),)
        return

    clicommon.run_command(docker_exec_cmd.format(ndppd_config_gen_cmd), display_cmd=True)
    sleep(3)
    clicommon.run_command(docker_exec_cmd.format(ndppd_restart_cmd), display_cmd=True)


@vlan.command('proxy_arp')
@click.argument('vid', metavar='<vid>', required=True, type=int)
@click.argument('mode', metavar='<mode>', required=True, type=click.Choice(["enabled", "disabled"]))
@clicommon.pass_db
def config_proxy_arp(db, vid, mode):
    """Configure proxy ARP for a VLAN"""

    log.log_info("'setting proxy ARP to {} for Vlan{}".format(mode, vid))

    ctx = click.get_current_context()

    vlan = 'Vlan{}'.format(vid)

    if not clicommon.is_valid_vlan_interface(db.cfgdb, vlan):
        ctx.fail("Interface {} does not exist".format(vlan))

    db.cfgdb.mod_entry('VLAN_INTERFACE', vlan, {"proxy_arp": mode})
    click.echo('Proxy ARP setting saved to ConfigDB')
    restart_ndppd()


#
# 'member' group ('config vlan member ...')
#


@vlan.group(cls=clicommon.AbbreviationGroup, name='member')
def vlan_member():
    pass


@vlan_member.command('add')
@click.argument('vid', metavar='<vid>', required=True)
@click.argument('port', metavar='port', required=True)
@click.option('-u', '--untagged', is_flag=True, help="Untagged status")
@click.option('-m', '--multiple', is_flag=True, help="Add Multiple Vlans")
@click.option('-e', '--except_flag', is_flag=True, help="Except vlans")
@clicommon.pass_db
def add_vlan_member(db, vid, port, untagged, multiple, except_flag):
    """Add VLAN member"""

    ctx = click.get_current_context()
    config_db = ValidatedConfigDBConnector(db.cfgdb)

    # parser will parse the vid input if there are syntax errors it will throw error

    vid_list = clicommon.vlan_member_input_parser(ctx, "add", db, except_flag, multiple, vid, port)

    hybrid_status = False
    port_table_data = db.cfgdb.get_table('PORT')

    if clicommon.get_interface_naming_mode() == "alias":  # TODO: MISSING CONSTRAINT IN YANG MODEL
        alias = port
        iface_alias_converter = clicommon.InterfaceAliasConverter(db)
        port = iface_alias_converter.alias_to_name(alias)
        if port is None:
            ctx.fail("cannot find port name for alias {}".format(alias))

    # TODO: MISSING CONSTRAINT IN YANG MODEL
    if clicommon.is_port_mirror_dst_port(db.cfgdb, port):
        ctx.fail("{} is configured as mirror destination port".format(port))

    if clicommon.is_valid_port(db.cfgdb, port):
        is_port = True
    elif clicommon.is_valid_portchannel(db.cfgdb, port):
        is_port = False
    else:
        ctx.fail("{} does not exist".format(port))

    if (is_port and clicommon.is_port_router_interface(db.cfgdb, port)) or \
            (not is_port and clicommon.is_pc_router_interface(db.cfgdb, port)):  # TODO: MISSING CONSTRAINT IN YANG MODEL
        ctx.fail("{} is a router interface!".format(port))

    portchannel_member_table = db.cfgdb.get_table('PORTCHANNEL_MEMBER')

    # TODO: MISSING CONSTRAINT IN YANG MODEL
    if (is_port and clicommon.interface_is_in_portchannel(portchannel_member_table, port)):
        ctx.fail("{} is part of portchannel!".format(port))

    if is_port:
        port_data = port_table_data[port]
        if "mode" in port_data:
            if port_data["mode"] == "hybrid":
                hybrid_status = True

    # multiple vlan command cannot be used to add multiple untagged vlan members
    # if the Ethernet is in Hybrid Mode, it can 
    if untagged:
        if hybrid_status:
            pass
        elif (multiple or except_flag or vid == "all"):
            ctx.fail("{} cannot have more than one untagged Vlan.".format(port))

    if ADHOC_VALIDATION:
        for vid in vid_list:

            # default vlan checker
            if vid == 1:
                ctx.fail("{} is default VLAN".format(vlan))

            log.log_info("'vlan member add {} {}' executing...".format(vid, port))

            if not clicommon.is_vlanid_in_range(vid):
                ctx.fail("Invalid VLAN ID {} (2-4094)".format(vid))

            vlan = 'Vlan{}'.format(vid)
            if clicommon.check_if_vlanid_exist(db.cfgdb, vlan) == False:
                log.log_info("{} does not exist".format(vlan))
                ctx.fail("{} does not exist".format(vlan))

            # TODO: MISSING CONSTRAINT IN YANG MODEL
            if clicommon.is_port_vlan_member(db.cfgdb, port, vlan):
                log.log_info("{} is already a member of {}".format(port, vlan))
                ctx.fail("{} is already a member of {}".format(port, vlan))
                
            # TODO: MISSING CONSTRAINT IN YANG MODEL
            if (clicommon.interface_is_untagged_member(db.cfgdb, port) and untagged and not hybrid_status):
                ctx.fail("{} is already untagged member!".format(port))
            
            # checking mode status of port if its access, trunk or routed
            if is_port:
                
                if "mode" not in port_data: 
                    ctx.fail("{} is in routed mode!\nUse switchport mode command to change port mode".format(port))
                else:
                    existing_mode = port_data["mode"]
                
                if existing_mode == "routed":
                    ctx.fail("{} is in routed mode!\nUse switchport mode command to change port mode".format(port))

                mode_type = "access" if untagged else "trunk"
                if existing_mode == "access" and mode_type == "trunk":  # TODO: MISSING CONSTRAINT IN YANG MODEL
                    ctx.fail("{} is in access mode! Tagged Members cannot be added".format(port))
                
                elif existing_mode == mode_type or (existing_mode == "trunk" and mode_type == "access"):
                    pass
            
            # in case of exception in list last added member will be shown to user
            try:
                config_db.set_entry('VLAN_MEMBER', (vlan, port), {'tagging_mode': "untagged" if untagged else "tagged"})
                click.echo("{} is added to {} as vlan member".format(port, vlan))
            except ValueError:
                ctx.fail("{} invalid or does not exist, or {} invalid or does not exist".format(vlan, port))


@vlan_member.command('del')
@click.argument('vid', metavar='<vid>', required=True)
@click.argument('port', metavar='<port>', required=True)
@click.option('-m', '--multiple', is_flag=True, help="Multiple vlans.")
@click.option('-e', '--except_flag', is_flag=True, help="Except vlans")
@clicommon.pass_db
def del_vlan_member(db, vid, port, multiple, except_flag):
    """Delete VLAN member"""

    ctx = click.get_current_context()
    config_db = ValidatedConfigDBConnector(db.cfgdb)

    # parser will parse the vid input if there are syntax errors it will throw error

    vid_list = clicommon.vlan_member_input_parser(ctx,"del", db, except_flag, multiple, vid, port)

    if ADHOC_VALIDATION:
        for vid in vid_list:

            log.log_info("'vlan member del {} {}' executing...".format(vid, port))

            if not clicommon.is_vlanid_in_range(vid):
                ctx.fail("Invalid VLAN ID {} (2-4094)".format(vid))

            vlan = 'Vlan{}'.format(vid)
            if clicommon.check_if_vlanid_exist(db.cfgdb, vlan) == False:
                log.log_info("{} does not exist".format(vlan))
                ctx.fail("{} does not exist".format(vlan))

            if clicommon.get_interface_naming_mode() == "alias":  # TODO: MISSING CONSTRAINT IN YANG MODEL
                alias = port
                iface_alias_converter = clicommon.InterfaceAliasConverter(db)
                port = iface_alias_converter.alias_to_name(alias)
                if port is None:
                    ctx.fail("cannot find port name for alias {}".format(alias))

            # TODO: MISSING CONSTRAINT IN YANG MODEL
            if not clicommon.is_port_vlan_member(db.cfgdb, port, vlan):
                ctx.fail("{} is not a member of {}".format(port, vlan))

            try:
                config_db.set_entry('VLAN_MEMBER', (vlan, port), None)
                click.echo("{} is removed from {} as vlan member".format(port, vlan))

            except JsonPatchConflict:
                ctx.fail("{} invalid or does not exist, or {} is not a member of {}".format(vlan, port, vlan))
