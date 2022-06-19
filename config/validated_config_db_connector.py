import jsonpatch

from swsscommon.swsscommon import ConfigDBConnector
from generic_config_updater.generic_updater import GenericUpdater, ConfigFormat

def validate(config_db_connector):

    def validated_set_entry(table, key, value):
        if value:
            op = "add"
        else:
            op = "remove"
        path = "/{}/{}".format(table, key)
        gcu_json_input = []
        gcu_json = {"op": "{}".format(op),
                    "path": "{}".format(path)}
        if value:
            gcu_json["value"] = value

        gcu_json_input.append(gcu_json)
        gcu_patch = jsonpatch.JsonPatch(gcu_json_input)
        format = ConfigFormat.CONFIGDB.name
        config_format = ConfigFormat[format.upper()]
        GenericUpdater().apply_patch(patch=gcu_patch, config_format=config_format, verbose=False, dry_run=False, ignore_non_yang_tables=False, ignore_paths=None)

    config_db_connector.set_entry = validated_set_entry
    return config_db_connector
