import click
import ipaddress
import utilities_common.cli as clicommon
import utilities_common.dhcp_relay_util as dhcp_relay_util


DHCP_RELAY_TABLE = "DHCP_RELAY"
DHCPV6_SERVERS = "dhcpv6_servers"
IPV6 = 6

VLAN_TABLE = "VLAN"
DHCPV4_SERVERS = "dhcp_servers"
IPV4 = 4


def validate_ips(ctx, ips, ip_version):
    for ip in ips:
        try:
            ip_address = ipaddress.ip_address(ip)
        except Exception:
            ctx.fail("{} is invalid IP address".format(ip))

        if ip_address.version != ip_version:
            ctx.fail("{} is not IPv{} address".format(ip, ip_version))


def get_dhcp_servers(db, vlan_name, ctx, table_name, dhcp_servers_str):
    table = db.cfgdb.get_entry(table_name, vlan_name)
    if len(table.keys()) == 0:
        ctx.fail("{} doesn't exist".format(vlan_name))

    dhcp_servers = table.get(dhcp_servers_str, [])

    return dhcp_servers, table


def get_dhcp_table_servers_key(ip_version):
    table_name = DHCP_RELAY_TABLE if ip_version == 6 else VLAN_TABLE
    dhcp_servers_str = DHCPV6_SERVERS if ip_version == 6 else DHCPV4_SERVERS
    return table_name, dhcp_servers_str


def add_dhcp_relay(vid, dhcp_relay_ips, db, ip_version):
    table_name, dhcp_servers_str = get_dhcp_table_servers_key(ip_version)
    vlan_name = "Vlan{}".format(vid)
    ctx = click.get_current_context()
    # Verify ip addresses are valid
    validate_ips(ctx, dhcp_relay_ips, ip_version)
    dhcp_servers, table = get_dhcp_servers(db, vlan_name, ctx, table_name, dhcp_servers_str)
    added_ips = []

    for dhcp_relay_ip in dhcp_relay_ips:
        # Verify ip addresses not duplicate in add list
        if dhcp_relay_ip in added_ips:
            ctx.fail("Error: Find duplicate DHCP relay ip {} in add list".format(dhcp_relay_ip))
        # Verify ip addresses not exist in DB
        if dhcp_relay_ip in dhcp_servers:
            click.echo("{} is already a DHCP relay for {}".format(dhcp_relay_ip, vlan_name))
            return

        dhcp_servers.append(dhcp_relay_ip)
        added_ips.append(dhcp_relay_ip)

    table[dhcp_servers_str] = dhcp_servers

    db.cfgdb.set_entry(table_name, vlan_name, table)
    click.echo("Added DHCP relay address [{}] to {}".format(",".join(dhcp_relay_ips), vlan_name))
    dhcp_relay_util.handle_restart_dhcp_relay_service()


def del_dhcp_relay(vid, dhcp_relay_ips, db, ip_version):
    table_name, dhcp_servers_str = get_dhcp_table_servers_key(ip_version)
    vlan_name = "Vlan{}".format(vid)
    ctx = click.get_current_context()
    # Verify ip addresses are valid
    validate_ips(ctx, dhcp_relay_ips, ip_version)
    dhcp_servers, table = get_dhcp_servers(db, vlan_name, ctx, table_name, dhcp_servers_str)
    removed_ips = []

    for dhcp_relay_ip in dhcp_relay_ips:
        # Verify ip addresses not duplicate in del list
        if dhcp_relay_ip in removed_ips:
            ctx.fail("Error: Find duplicate DHCP relay ip {} in del list".format(dhcp_relay_ip))
        # Remove dhcp servers if they exist in the DB
        if dhcp_relay_ip not in dhcp_servers:
            ctx.fail("{} is not a DHCP relay for {}".format(dhcp_relay_ip, vlan_name))

        dhcp_servers.remove(dhcp_relay_ip)
        removed_ips.append(dhcp_relay_ip)

    if len(dhcp_servers) == 0:
        del table[dhcp_servers_str]
    else:
        table[dhcp_servers_str] = dhcp_servers

    db.cfgdb.set_entry(table_name, vlan_name, table)
    click.echo("Removed DHCP relay address [{}] from {}".format(",".join(dhcp_relay_ips), vlan_name))
    dhcp_relay_util.handle_restart_dhcp_relay_service()


@click.group(cls=clicommon.AbbreviationGroup, name="dhcp_relay")
def dhcp_relay():
    """config DHCP_Relay information"""
    pass


@dhcp_relay.group(cls=clicommon.AbbreviationGroup, name="ipv6")
def dhcp_relay_ipv6():
    pass


@dhcp_relay_ipv6.group(cls=clicommon.AbbreviationGroup, name="destination")
def dhcp_relay_ipv6_destination():
    pass


@dhcp_relay_ipv6_destination.command("add")
@click.argument("vid", metavar="<vid>", required=True, type=int)
@click.argument("dhcp_relay_destinations", nargs=-1, required=True)
@clicommon.pass_db
def add_dhcp_relay_ipv6_destination(db, vid, dhcp_relay_destinations):
    add_dhcp_relay(vid, dhcp_relay_destinations, db, IPV6)


@dhcp_relay_ipv6_destination.command("del")
@click.argument("vid", metavar="<vid>", required=True, type=int)
@click.argument("dhcp_relay_destinations", nargs=-1, required=True)
@clicommon.pass_db
def del_dhcp_relay_ipv6_destination(db, vid, dhcp_relay_destinations):
    del_dhcp_relay(vid, dhcp_relay_destinations, db, IPV6)


@dhcp_relay.group(cls=clicommon.AbbreviationGroup, name="ipv4")
def dhcp_relay_ipv4():
    pass


@dhcp_relay_ipv4.group(cls=clicommon.AbbreviationGroup, name="helper")
def dhcp_relay_ipv4_helper():
    pass


@dhcp_relay_ipv4_helper.command("add")
@click.argument("vid", metavar="<vid>", required=True, type=int)
@click.argument("dhcp_relay_helpers", nargs=-1, required=True)
@clicommon.pass_db
def add_dhcp_relay_ipv4_helper(db, vid, dhcp_relay_helpers):
    add_dhcp_relay(vid, dhcp_relay_helpers, db, IPV4)


@dhcp_relay_ipv4_helper.command("del")
@click.argument("vid", metavar="<vid>", required=True, type=int)
@click.argument("dhcp_relay_helpers", nargs=-1, required=True)
@clicommon.pass_db
def del_dhcp_relay_ipv4_helper(db, vid, dhcp_relay_helpers):
    del_dhcp_relay(vid, dhcp_relay_helpers, db, IPV4)
