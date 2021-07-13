"""
This CLI plugin was auto-generated by using 'sonic-cli-gen' utility, BUT
it was manually modified to meet the PBH HLD requirements.

PBH HLD - https://github.com/Azure/SONiC/pull/773
CLI Auto-generation tool HLD - https://github.com/Azure/SONiC/pull/78
"""

import click
import ipaddress
import re
import utilities_common.cli as clicommon

hash_field_types = [
    'INNER_IP_PROTOCOL',
    'INNER_L4_DST_PORT',
    'INNER_L4_SRC_PORT',
    'INNER_DST_IPV4',
    'INNER_SRC_IPV4',
    'INNER_DST_IPV6',
    'INNER_SRC_IPV6'
]
packet_action_types = ['SET_ECMP_HASH', 'SET_LAG_HASH']
flow_counter_state = ['DISABLED', 'ENABLED']

gre_key_re = r"(0x){1}[a-fA-F0-9]{1,8}/(0x){1}[a-fA-F0-9]{1,8}"
ip_protocol_re = r"(0x){1}[a-fA-F0-9]{1,2}"
ipv6_next_header_re = ip_protocol_re
l4_dst_port_re = r"(0x){1}[a-fA-F0-9]{1,4}"
inner_ether_type_re = l4_dst_port_re


def exit_with_error(*args, **kwargs):
    """ Print a message and abort CLI. """

    click.secho(*args, **kwargs)
    raise click.Abort()


def add_entry(db, table, key, data):
    """ Add new entry in table """

    cfg = db.get_config()
    cfg.setdefault(table, {})
    if key in cfg[table]:
        raise Exception("{} already exists".format(key))

    cfg[table][key] = data

    db.set_entry(table, key, data)


def update_entry(db, table, key, data, create_if_not_exists=False):
    """ Update entry in table and validate configuration.
        If attribute value in data is None, the attribute is deleted.
    """

    cfg = db.get_config()
    cfg.setdefault(table, {})

    if create_if_not_exists:
        cfg[table].setdefault(key, {})

    if key not in cfg[table]:
        raise Exception("{} does not exist".format(key))

    for attr, value in data.items():
        if value is None and attr in cfg[table][key]:
            cfg[table][key].pop(attr)
        else:
            cfg[table][key][attr] = value

    db.set_entry(table, key, cfg[table][key])


def del_entry(db, table, key):
    """ Delete entry in table """

    cfg = db.get_config()
    cfg.setdefault(table, {})
    if key not in cfg[table]:
        raise Exception("{} does not exist".format(key))

    cfg[table].pop(key)

    db.set_entry(table, key, None)


def ip_address_validator(ctx, param, value):
    """ Check if the given ip address is valid

        Args:
            ctx: click context,
            param: click parameter context,
            value: value of parameter

        Returns:
            str: ip address
    """

    if value is not None:
        try:
            ip = ipaddress.ip_address(value)
        except Exception as e:
            exit_with_error("Error: invalid value '{}' for '{}' option\n{}".format(value, param.name, e), fg="red")

        return str(ip)


def re_match(value, param_name, regexp):
    """ Regexp validation of given parameter

        Args:
            value: value to validate,
            param_name: parameter name,
            regexp: regular expression

        Return:
            str: validated value
    """

    if re.match(regexp, str(value)) is None:
        exit_with_error("Error: invalid value '{}' for '{}' option".format(str(value), param_name), fg="red")

    return value


def pbh_re_match(ctx, param, value):
    """ Check if PBH rule options are valid

        Args:
            ctx: click context,
            param: click parameter context,
            value: value of parameter

        Returns:
            str: validated parameter
    """

    if value is not None:
        if param.name == 'gre_key':
            return re_match(value, param.name, gre_key_re)
        elif param.name == 'ip_protocol':
            return re_match(value, param.name, ip_protocol_re)
        elif param.name == 'ipv6_next_header':
            return re_match(value, param.name, ipv6_next_header_re)
        elif param.name == 'l4_dst_port':
            return re_match(value, param.name, l4_dst_port_re)
        elif param.name == 'inner_ether_type':
            return re_match(value, param.name, inner_ether_type_re)


def is_exist_in_db(db, obj_list, conf_db_key):
    """ Check if provided CLI option already exist in Config DB,
        i.g in case of --hash-field-list option it will check
        if 'hash-field' was previously added by
        'config pbh hash-field ...' CLI command

        Args:
            db: reference to Config DB,
            obj_list: value of 'click' option
            conf_db_key: key to search in Config DB
    """

    if obj_list is None:
        return True

    table = db.cfgdb.get_table(conf_db_key)
    correct_list = list(table.keys())

    splited_list = obj_list.split(',')

    for elem in splited_list:
        if elem not in correct_list:
            return False

    return True


def ip_mask_hash_field_correspondence_validator(ip_mask, hash_field):
    """ Check if the --ip-mask option are correspond to
        the --hash-field option

        Args:
            ip_mask: ip address or None,
            hash_field: hash field value, which was configured before
    """

    hf_v4 = ['INNER_DST_IPV4', 'INNER_SRC_IPV4']
    hf_v6 = ['INNER_DST_IPV6', 'INNER_SRC_IPV6']
    hf_v4_and_v6 = hf_v4 + hf_v6
    hf_no_ip = ['INNER_IP_PROTOCOL', 'INNER_L4_DST_PORT', 'INNER_L4_SRC_PORT']

    if (hash_field in hf_no_ip) and (ip_mask):
        exit_with_error("Error: the value of '--hash-field'='{}' is NOT compatible with the value of '--ip-mask'='{}'".format(hash_field, ip_mask), fg='red')

    if (hash_field in hf_v4_and_v6) and (ip_mask is None):
        exit_with_error("Error: the value of '--hash-field'='{}' is NOT compatible with the value of '--ip-mask'='{}'".format(hash_field, ip_mask), fg='red')

    if (ip_mask is not None):
        ip_addr_version = ipaddress.ip_address(ip_mask).version

        if (hash_field in hf_v4) and (ip_addr_version != 4):
            exit_with_error("Error: the value of '--hash-field'='{}' is NOT compatible with the value of '--ip-mask'='{}'".format(hash_field, ip_mask), fg='red')

        if (hash_field in hf_v6) and (ip_addr_version != 6):
            exit_with_error("Error: the value of '--hash-field'='{}' is NOT compatible with the value of '--ip-mask'='{}'".format(hash_field, ip_mask), fg='red')


def ip_mask_hash_field_update_validator(db, hash_field_name, ip_mask, hash_field):
    """ Function to validate --ip-mask and --hash-field
        correspondence, during update flow

        Args:
            db: reference to CONFIG DB,
            hash_field_name: name of the hash-field,
            ip_mask: ip address,
            hash_field: native hash field value
    """

    if (ip_mask is None) and (hash_field is None):
        return

    table = db.cfgdb.get_table('PBH_HASH_FIELD')
    hash_field_obj = table[hash_field_name]

    if (ip_mask is None) and (hash_field is not None):

        try:
            ip_mask = hash_field_obj['ip_mask']
        except Exception as e:
            ip_mask = None

        ip_mask_hash_field_correspondence_validator(ip_mask, hash_field)

    if (ip_mask is not None) and (hash_field is None):

        try:
            hash_field = hash_field_obj['hash_field']
        except Exception as e:
            hash_field = None

        ip_mask_hash_field_correspondence_validator(ip_mask, hash_field)


@click.group(
    name='pbh',
    cls=clicommon.AliasedGroup
)
def PBH():
    """ Configure PBH (Policy based hashing) feature """

    pass


@PBH.group(
    name="hash-field",
    cls=clicommon.AliasedGroup
)
def PBH_HASH_FIELD():
    """ Configure PBH hash field """

    pass


@PBH_HASH_FIELD.command(name="add")
@click.argument(
    "hash-field-name",
    nargs=1,
    required=True,
)
@click.option(
    "--hash-field",
    help="Configure native hash field for this hash field",
    required=True,
    type=click.Choice(hash_field_types)
)
@click.option(
    "--ip-mask",
    help="""Configures IPv4/IPv6 address mask for this hash field required when the value of --hash-field are - INNER_DST_IPV4 or
    INNER_SRC_IPV4 or INNER_SRC_IPV4 or INNER_SRC_IPV4 """,
    callback=ip_address_validator,
)
@click.option(
    "--sequence-id",
    help="Configures in which order the fields are hashed and defines which fields should be associative",
    required=True,
    type=click.INT,
)
@clicommon.pass_db
def PBH_HASH_FIELD_add(db, hash_field_name, hash_field, ip_mask, sequence_id):
    """ Add object to PBH_HASH_FIELD table """

    ip_mask_hash_field_correspondence_validator(ip_mask, hash_field)

    table = "PBH_HASH_FIELD"
    key = hash_field_name
    data = {}
    if hash_field is not None:
        data["hash_field"] = hash_field
    if ip_mask is not None:
        data["ip_mask"] = ip_mask
    if sequence_id is not None:
        data["sequence_id"] = sequence_id

    try:
        add_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_HASH_FIELD.command(name="update")
@click.argument(
    "hash-field-name",
    nargs=1,
    required=True,
)
@click.option(
    "--hash-field",
    help="Configures native hash field for this hash field",
    type=click.Choice(hash_field_types)
)
@click.option(
    "--ip-mask",
    help="Configures IPv4/IPv6 address mask for this hash field",
    callback=ip_address_validator,
)
@click.option(
    "--sequence-id",
    help="Configures in which order the fields are hashed and defines which fields should be associative",
    type=click.INT,
)
@clicommon.pass_db
def PBH_HASH_FIELD_update(db, hash_field_name, hash_field, ip_mask, sequence_id):
    """ Update object in PBH_HASH_FIELD table """

    ip_mask_hash_field_update_validator(db, hash_field_name, ip_mask, hash_field)

    table = "PBH_HASH_FIELD"
    key = hash_field_name
    data = {}
    if hash_field is not None:
        data["hash_field"] = hash_field
    if ip_mask is not None:
        data["ip_mask"] = ip_mask
    if sequence_id is not None:
        data["sequence_id"] = sequence_id

    try:
        update_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_HASH_FIELD.command(name="delete")
@click.argument(
    "hash-field-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_HASH_FIELD_delete(db, hash_field_name):
    """ Delete object from PBH_HASH_FIELD table """

    table = "PBH_HASH_FIELD"
    key = hash_field_name
    try:
        del_entry(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH.group(
    name="hash",
    cls=clicommon.AliasedGroup
)
def PBH_HASH():
    """ Configure PBH hash """

    pass


@PBH_HASH.command(name="add")
@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)
@click.option(
    "--hash-field-list",
    help="The list of hash fields to apply with this hash",
    required=True,
)
@clicommon.pass_db
def PBH_HASH_add(db, hash_name, hash_field_list):
    """ Add object to PBH_HASH table """

    if not is_exist_in_db(db, hash_field_list, "PBH_HASH_FIELD"):
        exit_with_error("Error: invalid value '{}' for '--hash-field-list' option".format(hash_field_list), fg="red")

    table = "PBH_HASH"
    key = hash_name
    data = {}
    if hash_field_list is not None:
        data["hash_field_list"] = hash_field_list.split(",")

    try:
        add_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_HASH.command(name="update")
@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)
@click.option(
    "--hash-field-list",
    help="The list of hash fields to apply with this hash",
)
@clicommon.pass_db
def PBH_HASH_update(db, hash_name, hash_field_list):
    """ Update object in PBH_HASH table """

    if not is_exist_in_db(db, hash_field_list, "PBH_HASH_FIELD"):
        exit_with_error("Error: invalid value '{}' for '--hash-field-list' option".format(hash_field_list), fg="red")

    table = "PBH_HASH"
    key = hash_name
    data = {}
    if hash_field_list is not None:
        data["hash_field_list"] = hash_field_list.split(",")

    try:
        update_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_HASH.command(name="delete")
@click.argument(
    "hash-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_HASH_delete(db, hash_name):
    """ Delete object from PBH_HASH table """

    table = "PBH_HASH"
    key = hash_name
    try:
        del_entry(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH.group(
    name="rule",
    cls=clicommon.AliasedGroup
)
def PBH_RULE():
    """ Configure PBH rule """

    pass


@PBH_RULE.command(name="add")
@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "rule-name",
    nargs=1,
    required=True,
)
@click.option(
    "--priority",
    help="Configures priority",
    required=True,
    type=click.INT,
)
@click.option(
    "--gre-key",
    help="Configures packet match: GRE key (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--ip-protocol",
    help="Configures packet match: IP protocol (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--ipv6-next-header",
    help="Configures packet match: IPv6 Next header (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--l4-dst-port",
    help="Configures packet match: L4 destination port (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--inner-ether-type",
    help="Configures packet match: inner EtherType (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--hash",
    required=True,
    help="Configures the hash to apply",
)
@click.option(
    "--packet-action",
    help="Configures packet action",
    type=click.Choice(packet_action_types)
)
@click.option(
    "--flow-counter",
    help="Enables/Disables packet/byte counter",
    type=click.Choice(flow_counter_state)
)
@clicommon.pass_db
def PBH_RULE_add(
    db,
    table_name,
    rule_name,
    priority,
    gre_key,
    ip_protocol,
    ipv6_next_header,
    l4_dst_port,
    inner_ether_type,
    hash,
    packet_action,
    flow_counter
):
    """ Add object to PBH_RULE table """

    if not is_exist_in_db(db, table_name, "PBH_TABLE"):
        exit_with_error("Error: invalid value '{}' for 'table-name' argument".format(table_name), fg="red")
    if not is_exist_in_db(db, hash, "PBH_HASH"):
        exit_with_error("Error: invalid value '{}' for '--hash' option".format(hash), fg="red")

    table = "PBH_RULE"
    key = table_name, rule_name
    data = {}
    if priority is not None:
        data["priority"] = priority
    if gre_key is not None:
        data["gre_key"] = gre_key
    if ip_protocol is not None:
        data["ip_protocol"] = ip_protocol
    if ipv6_next_header is not None:
        data["ipv6_next_header"] = ipv6_next_header
    if l4_dst_port is not None:
        data["l4_dst_port"] = l4_dst_port
    if inner_ether_type is not None:
        data["inner_ether_type"] = inner_ether_type
    if hash is not None:
        data["hash"] = hash
    if packet_action is not None:
        data["packet_action"] = packet_action
    if flow_counter is not None:
        data["flow_counter"] = flow_counter

    try:
        add_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_RULE.command(name="update")
@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "rule-name",
    nargs=1,
    required=True,
)
@click.option(
    "--priority",
    help="Configures priority",
    type=click.INT,
)
@click.option(
    "--gre-key",
    help="Configures packet match: GRE key (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--ip-protocol",
    help="Configures packet match: IP protocol (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--ipv6-next-header",
    help="Configures packet match: IPv6 Next header (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--l4-dst-port",
    help="Configures packet match: L4 destination port (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--inner-ether-type",
    help="Configures packet match: inner EtherType (value/mask)",
    callback=pbh_re_match,
)
@click.option(
    "--hash",
    help="The hash to apply with this rule",
)
@click.option(
    "--packet-action",
    help="Configures packet action",
    type=click.Choice(packet_action_types)
)
@click.option(
    "--flow-counter",
    help="Enables/Disables packet/byte counter",
    type=click.Choice(flow_counter_state)
)
@clicommon.pass_db
def PBH_RULE_update(
    db,
    table_name,
    rule_name,
    priority,
    gre_key,
    ip_protocol,
    ipv6_next_header,
    l4_dst_port,
    inner_ether_type,
    hash,
    packet_action,
    flow_counter
):
    """ Update object in PBH_RULE table """

    if not is_exist_in_db(db, table_name, "PBH_TABLE"):
        exit_with_error("Error: invalid value '{}' for 'table-name' argument".format(table_name), fg="red")
    if not is_exist_in_db(db, hash, "PBH_HASH"):
        exit_with_error("Error: invalid value '{}' for '--hash' option".format(hash), fg="red")

    table = "PBH_RULE"
    key = table_name, rule_name
    data = {}
    if priority is not None:
        data["priority"] = priority
    if gre_key is not None:
        data["gre_key"] = gre_key
    if ip_protocol is not None:
        data["ip_protocol"] = ip_protocol
    if ipv6_next_header is not None:
        data["ipv6_next_header"] = ipv6_next_header
    if l4_dst_port is not None:
        data["l4_dst_port"] = l4_dst_port
    if inner_ether_type is not None:
        data["inner_ether_type"] = inner_ether_type
    if hash is not None:
        data["hash"] = hash
    if packet_action is not None:
        data["packet_action"] = packet_action
    if flow_counter is not None:
        data["flow_counter"] = flow_counter

    try:
        update_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_RULE.command(name="delete")
@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.argument(
    "rule-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_RULE_delete(db, table_name, rule_name):
    """ Delete object from PBH_RULE table """

    table = "PBH_RULE"
    key = table_name, rule_name
    try:
        del_entry(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH.group(
    name="table",
    cls=clicommon.AliasedGroup
)
def PBH_TABLE():
    """ Configure PBH table"""

    pass

def interfaces_list_validator(db, interface_list, is_update: bool):
    if is_update and (interface_list is None):
        return

    error = False
    interfaces = interface_list.split(',')

    for intf in interfaces:
        if intf.startswith('Ethernet'):
            if not clicommon.is_valid_port(db.cfgdb, intf):
                error = True
        elif intf.startswith('PortChannel'):
            if not clicommon.is_valid_portchannel(db.cfgdb, intf):
                error = True
        else:
            error = True

    if error:
        exit_with_error("Error: invalid value '{}', for '--interface-list' option".format(interface_list), fg="red")


@PBH_TABLE.command(name="add")
@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.option(
    "--description",
    help="The description of this table",
    required=True,
)
@click.option(
    "--interface-list",
    help="Interfaces to which this table is applied",
    required=True,
)
@clicommon.pass_db
def PBH_TABLE_add(db, table_name, description, interface_list):
    """ Add object to PBH_TABLE table """

    interfaces_list_validator(db, interface_list, is_update=False)

    table = "PBH_TABLE"
    key = table_name
    data = {}
    if description is not None:
        data["description"] = description
    if interface_list is not None:
        data["interface_list"] = interface_list.split(",")

    try:
        add_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_TABLE.command(name="update")
@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@click.option(
    "--description",
    help="The description of this table",
)
@click.option(
    "--interface-list",
    help="Interfaces to which this table is applied",
)
@clicommon.pass_db
def PBH_TABLE_update(db, table_name, description, interface_list):
    """ Update object in PBH_TABLE table """

    interfaces_list_validator(db, interface_list, is_update=True)

    table = "PBH_TABLE"
    key = table_name
    data = {}
    if description is not None:
        data["description"] = description
    if interface_list is not None:
        data["interface_list"] = interface_list.split(",")

    try:
        update_entry(db.cfgdb, table, key, data)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


@PBH_TABLE.command(name="delete")
@click.argument(
    "table-name",
    nargs=1,
    required=True,
)
@clicommon.pass_db
def PBH_TABLE_delete(db, table_name):
    """ Delete object from PBH_TABLE table """

    table = "PBH_TABLE"
    key = table_name
    try:
        del_entry(db.cfgdb, table, key)
    except Exception as err:
        exit_with_error("Error: {}".format(err), fg="red")


def register(cli):
    cli_node = PBH
    if cli_node.name in cli.commands:
        raise Exception("{} already exists in CLI".format(cli_node.name))
    cli.add_command(PBH)

