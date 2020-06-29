#!/usr/bin/env python
#
# main.py
#
# Command-line utility for interacting with HW Watchdog in SONiC
#

try:
    import sys
    import os
    import click
    import syslog
    import sonic_platform
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))

VERSION = '2.0'

SYSLOG_IDENTIFIER = "watchdogutil"

WATCHDOG_LOAD_ERROR = -1
CHASSIS_LOAD_ERROR = -2

# Global platform-specific watchdog class instance
platform_watchdog = None


# ========================== Syslog wrappers ==========================


def log_info(msg, also_print_to_console=False):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_INFO, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


def log_warning(msg, also_print_to_console=False):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_WARNING, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


def log_error(msg, also_print_to_console=False):
    syslog.openlog(SYSLOG_IDENTIFIER)
    syslog.syslog(syslog.LOG_ERR, msg)
    syslog.closelog()

    if also_print_to_console:
        click.echo(msg)


# ==================== Methods for initialization ====================

# Loads platform specific watchdog module from source
def load_platform_watchdog():
    global platform_watchdog

    platform = sonic_platform.platform.Platform()

    chassis = platform.get_chassis()
    if not chassis:
        log_error("Failed to get chassis")
        return CHASSIS_LOAD_ERROR

    platform_watchdog = chassis.get_watchdog()
    if not platform_watchdog:
        log_error("Failed to get watchdog module")
        return WATCHDOG_LOAD_ERROR

    return 0


# ==================== CLI commands and groups ====================


# This is our main entrypoint - the main 'watchdogutil' command
@click.group()
def watchdogutil():
    """watchdogutil - Command line utility for providing HW watchdog interface"""

    if os.geteuid() != 0:
        click.echo("Root privileges are required for this operation")
        sys.exit(1)

    # Load platform-specific watchdog class
    err = load_platform_watchdog()
    if err != 0:
        sys.exit(2)

# 'version' subcommand
@watchdogutil.command()
def version():
    """Display version info"""
    click.echo("watchdogutil version {0}".format(VERSION))

# 'status' subcommand
@watchdogutil.command()
def status():
    """Check the watchdog status with remaining_time if it's armed"""
    status = platform_watchdog.is_armed()
    remaining_time = platform_watchdog.get_remaining_time()
    if status is True:
        click.echo("Watchdog armed with remaining {} seconds".format(remaining_time))
    else:
        click.echo("Watchdog unarmed")


# 'disarm' subcommand
@watchdogutil.command()
def disarm():
    """Disarm HW watchdog"""
    result = platform_watchdog.disarm()
    if result is True:
        click.echo("Watchdog disarmed successfully")
    else:
        click.echo("Failed to disarm Watchdog")

# 'arm' subcommand
@watchdogutil.command()
@click.option('-s', '--seconds', default=180, type=int, help="the default timeout of HW watchdog")
def arm(seconds):
    """Arm HW watchdog"""
    result = int(platform_watchdog.arm(seconds))
    if result == seconds:
        click.echo("Watchdog armed for {} seconds".format(seconds))
    else:
        click.echo("Failed to arm Watchdog for {} seconds".format(seconds))

if __name__ == '__main__':
    cli()
