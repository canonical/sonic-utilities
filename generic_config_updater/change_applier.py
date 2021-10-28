import copy
import json
import jsondiff
import importlib
import os
import tempfile
from collections import defaultdict
from swsscommon.swsscommon import ConfigDBConnector
from .gu_common import genericUpdaterLogging


UPDATER_CONF_FILE = "/etc/sonic/generic_config_updater.conf"
logger = genericUpdaterLogging.get_logger(title="Change Applier")

print_to_console = False
print_to_stdout = False

def set_print_options(to_console=False, to_stdout=False):
    global print_to_console, print_to_stdout

    print_to_console = to_console
    print_to_stdout = to_stdout


def log_debug(m):
    logger.log_debug(m, print_to_console)
    if print_to_stdout:
        print(m)


def log_error(m):
    logger.log_error(m, print_to_console)
    if print_to_stdout:
        print(m)


def get_config_db():
    config_db = ConfigDBConnector()
    config_db.connect()
    return config_db


def set_config(config_db, tbl, key, data):
    config_db.set_entry(tbl, key, data)


class ChangeApplier:

    updater_conf = None

    def __init__(self):
        self.config_db = get_config_db()
        if (not ChangeApplier.updater_conf) and os.path.exists(UPDATER_CONF_FILE):
            with open(UPDATER_CONF_FILE, "r") as s:
                ChangeApplier.updater_conf = json.load(s)


    def _invoke_cmd(self, cmd, old_cfg, upd_cfg, keys):
        # cmd is in the format as <package/module name>.<method name>
        #
        method_name = cmd.split(".")[-1]
        module_name = ".".join(cmd.split(".")[0:-1])

        module = importlib.import_module(module_name, package=None)
        method_to_call = getattr(module, method_name)

        return method_to_call(old_cfg, upd_cfg, keys)


    def _services_validate(self, old_cfg, upd_cfg, keys):
        lst_svcs = set()
        lst_cmds = set()
        if not keys:
            # calling apply with no config would invoke
            # default validation, if any
            #
            keys[""] = {}

        tables = ChangeApplier.updater_conf["tables"]
        for tbl in keys:
            lst_svcs.update(tables.get(tbl, {}).get("services_to_validate", []))

        services = ChangeApplier.updater_conf["services"]
        for svc in lst_svcs:
            lst_cmds.update(services.get(svc, {}).get("validate_commands", []))

        for cmd in lst_cmds:
            ret = self._invoke_cmd(cmd, old_cfg, upd_cfg, keys)
            if ret:
                log_error("service invoked: {} failed with ret={}".format(cmd, ret))
                return ret
            log_debug("service invoked: {}".format(cmd))
        return 0


    def _upd_data(self, tbl, run_tbl, upd_tbl, upd_keys):
        for key in set(run_tbl.keys()).union(set(upd_tbl.keys())):
            run_data = run_tbl.get(key, None)
            upd_data = upd_tbl.get(key, None)

            if run_data != upd_data:
                set_config(self.config_db, tbl, key, upd_data)
                upd_keys[tbl][key] = {}
                log_debug("Patch affected tbl={} key={}".format(tbl, key))


    def _report_mismatch(self, run_data, upd_data):
        log_error("run_data vs expected_data: {}".format(
            str(jsondiff.diff(run_data, upd_data))[0:40]))


    def apply(self, change):
        run_data = self._get_running_config()
        upd_data = change.apply(copy.deepcopy(run_data))
        upd_keys = defaultdict(dict)

        for tbl in sorted(set(run_data.keys()).union(set(upd_data.keys()))):
            self._upd_data(tbl, run_data.get(tbl, {}),
                    upd_data.get(tbl, {}), upd_keys)

        ret = self._services_validate(run_data, upd_data, upd_keys)
        if not ret:
            run_data = self._get_running_config()
            if upd_data != run_data:
                self._report_mismatch(run_data, upd_data)
                ret = -1
        if ret:
            log_error("Failed to apply Json change")
        return ret


    def _get_running_config(self):
        (_, fname) = tempfile.mkstemp(suffix="_changeApplier")
        os.system("sonic-cfggen -d --print-data > {}".format(fname))
        run_data = {}
        with open(fname, "r") as s:
            run_data = json.load(s)
        if os.path.isfile(fname):
            os.remove(fname)
        return run_data
