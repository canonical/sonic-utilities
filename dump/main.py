import os
import sys
import json
import re
import click
from tabulate import tabulate
from sonic_py_common import multi_asic
from utilities_common.constants import DEFAULT_NAMESPACE
from dump.match_infra import RedisSource, JsonSource, ConnectionPool
from dump import plugins


# Autocompletion Helper
def get_available_modules(ctx, args, incomplete):
    return [k for k in plugins.dump_modules.keys() if incomplete in k]


# Display Modules Callback
def show_modules(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    header = ["Module", "Identifier"]
    display = []
    for mod in plugins.dump_modules:
        display.append((mod, plugins.dump_modules[mod].ARG_NAME))
    click.echo(tabulate(display, header))
    ctx.exit()


@click.group()
def dump():
    pass


@dump.command()
@click.pass_context
@click.argument('module', required=True, type=str, autocompletion=get_available_modules)
@click.argument('identifier', required=True, type=str)
@click.option('--show', '-s', is_flag=True, default=False, expose_value=False,
              callback=show_modules, help='Display Modules Available', is_eager=True)
@click.option('--db', '-d', multiple=True,
              help='Only dump from these Databases or the CONFIG_FILE')
@click.option('--table', '-t', is_flag=True, default=False,
              help='Print in tabular format', show_default=True)
@click.option('--key-map', '-k', is_flag=True, default=False, show_default=True,
              help="Only fetch the keys matched, don't extract field-value dumps")
@click.option('--verbose', '-v', is_flag=True, default=False, show_default=True,
              help="Prints any intermediate output to stdout useful for dev & troubleshooting")
@click.option('--namespace', '-n', default=DEFAULT_NAMESPACE, type=str,
              show_default=True, help='Dump the redis-state for this namespace.')
def state(ctx, module, identifier, db, table, key_map, verbose, namespace):
    """
    Dump the current state of the identifier for the specified module from Redis DB or CONFIG_FILE
    """
    if not multi_asic.is_multi_asic() and namespace != DEFAULT_NAMESPACE:
        click.echo("Namespace option is not valid for a single-ASIC device")
        ctx.exit()

    if multi_asic.is_multi_asic() and (namespace != DEFAULT_NAMESPACE and namespace not in multi_asic.get_namespace_list()):
        click.echo("Namespace option is not valid. Choose one of {}".format(multi_asic.get_namespace_list()))
        ctx.exit()

    if module not in plugins.dump_modules:
        click.echo("No Matching Plugin has been Implemented")
        ctx.exit()

    if verbose:
        os.environ["VERBOSE"] = "1"
    else:
        os.environ["VERBOSE"] = "0"

    ctx.module = module
    obj = plugins.dump_modules[module]()

    if identifier == "all":
        ids = obj.get_all_args(namespace)
    else:
        ids = identifier.split(",")

    params = {}
    collected_info = {}
    params['namespace'] = namespace
    for arg in ids:
        params[plugins.dump_modules[module].ARG_NAME] = arg
        try:
            collected_info[arg] = obj.execute(params)
        except ValueError as err:
            click.fail(f"Failed to execute plugin: {err}")

    if len(db) > 0:
        collected_info = filter_out_dbs(db, collected_info)

    vidtorid = extract_rid(collected_info, namespace)

    if not key_map:
        collected_info = populate_fv(collected_info, module, namespace)

    for id in vidtorid.keys():
        collected_info[id]["ASIC_DB"]["vidtorid"] = vidtorid[id]

    print_dump(collected_info, table, module, identifier, key_map)

    return


def extract_rid(info, ns):
    r = RedisSource(ConnectionPool())
    r.connect("ASIC_DB", ns)
    vidtorid = {}
    vid_cache = {}  # Cache Entries to reduce number of Redis Calls
    for arg in info.keys():
        mp = get_v_r_map(r, info[arg], vid_cache)
        if mp:
            vidtorid[arg] = mp
    return vidtorid


def get_v_r_map(r, single_dict, vid_cache):
    v_r_map = {}
    asic_obj_ptrn = "ASIC_STATE:.*:oid:0x\w{1,14}"

    if "ASIC_DB" in single_dict and "keys" in single_dict["ASIC_DB"]:
        for redis_key in single_dict["ASIC_DB"]["keys"]:
            if re.match(asic_obj_ptrn, redis_key):
                matches = re.findall(r"oid:0x\w{1,14}", redis_key)
                if matches:
                    vid = matches[0]
                    if vid in vid_cache:
                        rid = vid_cache[vid]
                    else:
                        rid = r.hget("ASIC_DB", "VIDTORID", vid)
                        vid_cache[vid] = rid
                    v_r_map[vid] = rid if rid else "Real ID Not Found"
    return v_r_map


# Filter dbs which are not required
def filter_out_dbs(db_list, collected_info):
    args_ = list(collected_info.keys())
    for arg in args_:
        dbs = list(collected_info[arg].keys())
        for db in dbs:
            if db not in db_list:
                del collected_info[arg][db]
    return collected_info


def populate_fv(info, module, namespace):
    all_dbs = set()
    for id in info.keys():
        for db_name in info[id].keys():
            all_dbs.add(db_name)

    db_cfg_file = JsonSource()
    db_conn = ConnectionPool().initialize_connector(namespace)
    for db_name in all_dbs:
        if db_name == "CONFIG_FILE":
            db_cfg_file.connect(plugins.dump_modules[module].CONFIG_FILE, namespace)
        else:
            db_conn.connect(db_name)

    final_info = {}
    for id in info.keys():
        final_info[id] = {}
        for db_name in info[id].keys():
            final_info[id][db_name] = {}
            final_info[id][db_name]["keys"] = []
            final_info[id][db_name]["tables_not_found"] = info[id][db_name]["tables_not_found"]
            for key in info[id][db_name]["keys"]:
                if db_name == "CONFIG_FILE":
                    fv = db_cfg_file.get(db_name, key)
                else:
                    fv = db_conn.get_all(db_name, key)
                final_info[id][db_name]["keys"].append({key: fv})

    return final_info


def get_dict_str(key_obj):
    table = []
    for field, value in key_obj.items():
        if field.endswith('@'):
            field = field[:-1]
            value = '\n'.join(value.split(','))
        table.append((field, value))
    return tabulate(table, headers=["field", "value"], tablefmt="psql")


# print dump
def print_dump(collected_info, table, module, identifier, key_map):
    if not table:
        click.echo(json.dumps(collected_info, indent=4))
        return

    top_header = [plugins.dump_modules[module].ARG_NAME, "DB_NAME", "DUMP"]
    final_collection = []
    for ids in collected_info.keys():
        for db in collected_info[ids].keys():
            total_info = ""

            if collected_info[ids][db]["tables_not_found"]:
                tabulate_fmt = []
                for tab in collected_info[ids][db]["tables_not_found"]:
                    tabulate_fmt.append([tab])
                total_info += tabulate(tabulate_fmt, ["Tables Not Found"], tablefmt="grid")
                total_info += "\n"

            if not key_map:
                values = []
                hdrs = ["Keys", "field-value pairs"]
                for key_obj in collected_info[ids][db]["keys"]:
                    if isinstance(key_obj, dict) and key_obj:
                        key = list(key_obj.keys())[0]
                        values.append([key, get_dict_str(key_obj[key])])
                total_info += str(tabulate(values, hdrs, tablefmt="grid"))
            else:
                temp = []
                for key_ in collected_info[ids][db]["keys"]:
                    temp.append([key_])
                total_info += str(tabulate(temp, headers=["Keys Collected"], tablefmt="grid"))

            total_info += "\n"
            if "vidtorid" in collected_info[ids][db]:
                temp = []
                for pair in collected_info[ids][db]["vidtorid"].items():
                    temp.append(list(pair))
                total_info += str(tabulate(temp, headers=["vid", "rid"], tablefmt="grid"))
            final_collection.append([ids, db, total_info])

    click.echo(tabulate(final_collection, top_header, tablefmt="grid"))
    return


if __name__ == '__main__':
    dump()
