#!/usr/bin/env python3
import os
import sys
import click
from swsscommon.swsscommon import ConfigDBConnector
from tabulate import tabulate
from natsort import natsorted

ALL_PRIORITIES = [str(x) for x in range(8)]
PRIORITY_STATUS = ['on', 'off']

# mock the redis for unit test purposes #
try:
    if os.environ["UTILITIES_UNIT_TESTING"] == "2":
        modules_path = os.path.join(os.path.dirname(__file__), "..")
        tests_path = os.path.join(modules_path, "tests")
        sys.path.insert(0, modules_path)
        sys.path.insert(0, tests_path)
except KeyError:
    pass

class Pfc(object):


    def __init__(self, db=None):
        self.db = None
        self.cfgdb = db

    def configPfcAsym(self, interface, pfc_asym):
        """
        PFC handler to configure asymmetric PFC.
        """

        configdb = self.cfgdb
        if configdb is None:
            configdb = ConfigDBConnector()
            configdb.connect()

        configdb.mod_entry("PORT", interface, {'pfc_asym': pfc_asym})

        if "UTILITIES_UNIT_TESTING" in os.environ and os.environ["UTILITIES_UNIT_TESTING"] == "2":
            self.showPfcAsym(interface)

    def showPfcAsym(self, interface):
        """
        PFC handler to display asymmetric PFC information.
        """
        header = ('Interface', 'Asymmetric')

        configdb = self.cfgdb
        if configdb is None:
            configdb = ConfigDBConnector()
            configdb.connect()

        if interface:
            db_keys = configdb.keys(configdb.CONFIG_DB, 'PORT|{0}'.format(interface))
        else:
            db_keys = configdb.keys(configdb.CONFIG_DB, 'PORT|*')

        table = []

        for i in db_keys or [None]:
            key = None
            if i:
                key = i.split('|')[-1]

            if key and key.startswith('Ethernet'):
                entry = configdb.get_entry('PORT', key)
                table.append([key, entry.get('pfc_asym', 'N/A')])

        sorted_table = natsorted(table)

        click.echo()
        click.echo(tabulate(sorted_table, headers=header, tablefmt="simple", missingval=""))
        click.echo()

    def configPfcPrio(self, status, interface, priority):
        configdb = self.cfgdb
        if configdb is None:
            configdb = ConfigDBConnector()
            configdb.connect()

        if interface not in configdb.get_keys('PORT_QOS_MAP'):
            click.echo('Cannot find interface {0}'.format(interface))
            return

        """Current lossless priorities on the interface"""
        entry = configdb.get_entry('PORT_QOS_MAP', interface)
        enable_prio = entry.get('pfc_enable').split(',')

        """Avoid '' in enable_prio"""
        enable_prio = [x.strip() for x in enable_prio if x.strip()]

        if status == 'on' and priority in enable_prio:
            click.echo('Priority {0} has already been enabled on {1}'.format(priority, interface))
            return

        if status == 'off' and priority not in enable_prio:
            click.echo('Priority {0} is not enabled on {1}'.format(priority, interface))
            return

        if status == 'on':
            enable_prio.append(priority)

        else:
            enable_prio.remove(priority)

        enable_prio.sort()
        configdb.mod_entry("PORT_QOS_MAP", interface, {'pfc_enable': ','.join(enable_prio)})

        """Show the latest PFC configuration"""
        self.showPfcPrio(interface)
        
    def showPfcPrio(self, interface):
        """
        PFC handler to display PFC enabled priority information.
        """
        header = ('Interface', 'Lossless priorities')
        table = []

        configdb = self.cfgdb
        if configdb is None:
            configdb = ConfigDBConnector()
            configdb.connect()

        """Get all the interfaces with QoS map information"""
        intfs = configdb.get_keys('PORT_QOS_MAP')

        """The user specifies an interface but we cannot find it"""
        if interface and interface not in intfs:
            click.echo('Cannot find interface {0}'.format(interface))
            return

        if interface:
            intfs = [interface]

        for intf in intfs:
            entry = configdb.get_entry('PORT_QOS_MAP', intf)
            table.append([intf, entry.get('pfc_enable', 'N/A')])

        sorted_table = natsorted(table)
        click.echo()
        click.echo(tabulate(sorted_table, headers=header, tablefmt="simple", missingval=""))
        click.echo()
    
@click.group()
@click.pass_context
def cli(ctx):
    # Use the db object if given as input.
    db = None if ctx.obj is None else ctx.obj.cfgdb
    """PFC Command Line"""
    ctx.obj = {'pfc': Pfc(db)}

@cli.group()
@click.pass_context
def config(ctx):
    """Config PFC"""
    pass

@cli.group()
@click.pass_context
def show(ctx):
    """Show PFC information"""
    pass

@click.command()
@click.argument('status', type=click.Choice(PRIORITY_STATUS))
@click.argument('interface', type=click.STRING)
@click.pass_context
def configAsym(ctx, status, interface):
    """Configure asymmetric PFC on a given port."""
    ctx.obj['pfc'].configPfcAsym(interface, status)

@click.command()
@click.argument('status', type=click.Choice(PRIORITY_STATUS))
@click.argument('interface', type=click.STRING)
@click.argument('priority', type=click.Choice(ALL_PRIORITIES))
@click.pass_context
def configPrio(ctx, status, interface, priority):
    """Configure PFC on a given priority."""
    ctx.obj['pfc'].configPfcPrio(status, interface, priority)

@click.command()
@click.argument('interface', type=click.STRING, required=False)
@click.pass_context
def showAsym(ctx, interface):
    """Show asymmetric PFC information"""
    ctx.obj['pfc'].showPfcAsym(interface)

@click.command()
@click.argument('interface', type=click.STRING, required=False)
@click.pass_context
def showPrio(ctx, interface):
    """Show PFC priority information"""
    ctx.obj['pfc'].showPfcPrio(interface)

config.add_command(configAsym, "asymmetric")
config.add_command(configPrio, "priority")
show.add_command(showAsym, "asymmetric")
show.add_command(showPrio, "priority")
