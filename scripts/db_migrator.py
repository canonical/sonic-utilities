#!/usr/bin/env python

import os
import argparse
import json
import sys
import traceback

from sonic_py_common import device_info, logger
from swsssdk import ConfigDBConnector, SonicDBConfig, SonicV2Connector

INIT_CFG_FILE = '/etc/sonic/init_cfg.json'

# mock the redis for unit test purposes #
try:
    if os.environ["UTILITIES_UNIT_TESTING"] == "2":
        modules_path = os.path.join(os.path.dirname(__file__), "..")
        tests_path = os.path.join(modules_path, "sonic-utilities-tests")
        mocked_db_path = os.path.join(tests_path, "db_migrator_input")
        sys.path.insert(0, modules_path)
        sys.path.insert(0, tests_path)
        INIT_CFG_FILE = os.path.join(mocked_db_path, "init_cfg.json")
except KeyError:
    pass

SYSLOG_IDENTIFIER = 'db_migrator'

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)


class DBMigrator():
    def __init__(self, namespace, socket=None):
        """
        Version string format:
           version_<major>_<minor>_<build>
              major: starting from 1, sequentially incrementing in master
                     branch.
              minor: in github branches, minor version stays in 0. This minor
                     version creates space for private branches derived from
                     github public branches. These private branches shall use
                     none-zero values.
              build: sequentially increase within a minor version domain.
        """
        self.CURRENT_VERSION = 'version_1_0_4'

        self.TABLE_NAME      = 'VERSIONS'
        self.TABLE_KEY       = 'DATABASE'
        self.TABLE_FIELD     = 'VERSION'

        db_kwargs = {}
        if socket:
            db_kwargs['unix_socket_path'] = socket

        if namespace is None:
            self.configDB = ConfigDBConnector(**db_kwargs)
        else:
            self.configDB = ConfigDBConnector(use_unix_socket_path=True, namespace=namespace, **db_kwargs)
        self.configDB.db_connect('CONFIG_DB')

        self.appDB = SonicV2Connector(host='127.0.0.1')
        if self.appDB is not None:
            self.appDB.connect(self.appDB.APPL_DB)

        version_info = device_info.get_sonic_version_info()
        asic_type = version_info.get('asic_type')
        self.asic_type = asic_type

        if asic_type == "mellanox":
            from mellanox_buffer_migrator import MellanoxBufferMigrator
            self.mellanox_buffer_migrator = MellanoxBufferMigrator(self.configDB)

    def migrate_pfc_wd_table(self):
        '''
        Migrate all data entries from table PFC_WD_TABLE to PFC_WD
        '''
        data = self.configDB.get_table('PFC_WD_TABLE')
        for key in data.keys():
            self.configDB.set_entry('PFC_WD', key, data[key])
        self.configDB.delete_table('PFC_WD_TABLE')

    def is_ip_prefix_in_key(self, key):
        '''
        Function to check if IP address is present in the key. If it
        is present, then the key would be a tuple or else, it shall be
        be string
        '''
        return (isinstance(key, tuple))

    def migrate_interface_table(self):
        '''
        Migrate all data from existing INTERFACE table with IP Prefix
        to have an additional ONE entry without IP Prefix. For. e.g, for an entry
        "Vlan1000|192.168.0.1/21": {}", this function shall add an entry without
        IP prefix as ""Vlan1000": {}". This is for VRF compatibility.
        '''
        if_db = []
        if_tables = {
                     'INTERFACE',
                     'PORTCHANNEL_INTERFACE',
                     'VLAN_INTERFACE',
                     'LOOPBACK_INTERFACE'
                    }
        for table in if_tables:
            data = self.configDB.get_table(table)
            for key in data.keys():
                if not self.is_ip_prefix_in_key(key):
                    if_db.append(key)
                    continue

        for table in if_tables:
            data = self.configDB.get_table(table)
            for key in data.keys():
                if not self.is_ip_prefix_in_key(key) or key[0] in if_db:
                    continue
                log.log_info('Migrating interface table for ' + key[0])
                self.configDB.set_entry(table, key[0], data[key])
                if_db.append(key[0])

    def migrate_intf_table(self):
        '''
        Migrate all data from existing INTF table in APP DB during warmboot with IP Prefix
        to have an additional ONE entry without IP Prefix. For. e.g, for an entry
        "Vlan1000:192.168.0.1/21": {}", this function shall add an entry without
        IP prefix as ""Vlan1000": {}". This also migrates 'lo' to 'Loopback0' interface
        '''

        if self.appDB is None:
            return

        data = self.appDB.keys(self.appDB.APPL_DB, "INTF_TABLE:*")

        if data is None:
            return

        if_db = []
        for key in data:
            if_name = key.split(":")[1]
            if if_name == "lo":
                self.appDB.delete(self.appDB.APPL_DB, key)
                key = key.replace(if_name, "Loopback0")
                log.log_info('Migrating lo entry to ' + key)
                self.appDB.set(self.appDB.APPL_DB, key, 'NULL', 'NULL')

            if '/' not in key:
                if_db.append(key.split(":")[1])
                continue

        data = self.appDB.keys(self.appDB.APPL_DB, "INTF_TABLE:*")
        for key in data:
            if_name = key.split(":")[1]
            if if_name in if_db:
                continue
            log.log_info('Migrating intf table for ' + if_name)
            table = "INTF_TABLE:" + if_name
            self.appDB.set(self.appDB.APPL_DB, table, 'NULL', 'NULL')
            if_db.append(if_name)

    def migrate_feature_table(self):
        '''
        Combine CONTAINER_FEATURE and FEATURE tables into FEATURE table.
        '''
        feature_table = self.configDB.get_table('FEATURE')
        for feature, config in feature_table.items():
            state = config.get('status')
            if state is not None:
                config['state'] = state
                config.pop('status')
            self.configDB.set_entry('FEATURE', feature, config)

        container_feature_table = self.configDB.get_table('CONTAINER_FEATURE')
        for feature, config in container_feature_table.items():
            self.configDB.mod_entry('FEATURE', feature, config)
            self.configDB.set_entry('CONTAINER_FEATURE', feature, None)

    def version_unknown(self):
        """
        version_unknown tracks all SONiC versions that doesn't have a version
        string defined in config_DB.
        Nothing can be assumped when migrating from this version to the next
        version.
        Any migration operation needs to test if the DB is in expected format
        before migrating date to the next version.
        """

        log.log_info('Handling version_unknown')

        # NOTE: Uncomment next 3 lines of code when the migration code is in
        #       place. Note that returning specific string is intentional,
        #       here we only intended to migrade to DB version 1.0.1.
        #       If new DB version is added in the future, the incremental
        #       upgrade will take care of the subsequent migrations.
        self.migrate_pfc_wd_table()
        self.migrate_interface_table()
        self.migrate_intf_table()
        self.set_version('version_1_0_2')
        return 'version_1_0_2'

    def version_1_0_1(self):
        """
        Version 1_0_1.
        """
        log.log_info('Handling version_1_0_1')

        self.migrate_interface_table()
        self.migrate_intf_table()
        self.set_version('version_1_0_2')
        return 'version_1_0_2'

    def version_1_0_2(self):
        """
        Version 1_0_2.
        """
        log.log_info('Handling version_1_0_2')
        # Check ASIC type, if Mellanox platform then need DB migration
        if self.asic_type == "mellanox":
            if self.mellanox_buffer_migrator.mlnx_migrate_buffer_pool_size('version_1_0_2', 'version_1_0_3'):
                self.set_version('version_1_0_3')
        else:
            self.set_version('version_1_0_3')
        return 'version_1_0_3'

    def version_1_0_3(self):
        """
        Version 1_0_3.
        """
        log.log_info('Handling version_1_0_3')

        self.migrate_feature_table()

        # Check ASIC type, if Mellanox platform then need DB migration
        if self.asic_type == "mellanox":
            if self.mellanox_buffer_migrator.mlnx_migrate_buffer_pool_size('version_1_0_3', 'version_1_0_4') and self.mellanox_buffer_migrator.mlnx_migrate_buffer_profile('version_1_0_3', 'version_1_0_4'):
                self.set_version('version_1_0_4')
        else:
            self.set_version('version_1_0_4')

        return 'version_1_0_4'

    def version_1_0_4(self):
        """
        Version 1_0_4.
        """
        log.log_info('Handling version_1_0_4')

        # Check ASIC type, if Mellanox platform then need DB migration
        if self.asic_type == "mellanox":
            if self.mellanox_buffer_migrator.mlnx_migrate_buffer_pool_size('version_1_0_4', 'version_1_0_5') and self.mellanox_buffer_migrator.mlnx_migrate_buffer_profile('version_1_0_4', 'version_1_0_5'):
                self.set_version('version_1_0_5')
        else:
            self.set_version('version_1_0_5')

        return 'version_1_0_5'

    def version_1_0_5(self):
        """
        Current latest version. Nothing to do here.
        """
        log.log_info('Handling version_1_0_5')

        return None

    def get_version(self):
        version = self.configDB.get_entry(self.TABLE_NAME, self.TABLE_KEY)
        if version and version[self.TABLE_FIELD]:
            return version[self.TABLE_FIELD]

        return 'version_unknown'

    def set_version(self, version=None):
        if not version:
            version = self.CURRENT_VERSION
        log.log_info('Setting version to ' + version)
        entry = { self.TABLE_FIELD : version }
        self.configDB.set_entry(self.TABLE_NAME, self.TABLE_KEY, entry)

    def common_migration_ops(self):
        try:
            with open(INIT_CFG_FILE) as f:
                init_db = json.load(f)
        except Exception as e:
            raise Exception(str(e))

        for init_cfg_table, table_val in init_db.items():
            log.log_info("Migrating table {} from INIT_CFG to config_db".format(init_cfg_table))
            for key in table_val:
                curr_cfg = self.configDB.get_entry(init_cfg_table, key)
                init_cfg = table_val[key]

                # Override init config with current config.
                # This will leave new fields from init_config
                # in new_config, but not override existing configuration.
                new_cfg = init_cfg.copy()
                new_cfg.update(curr_cfg)
                self.configDB.set_entry(init_cfg_table, key, new_cfg)

    def migrate(self):
        version = self.get_version()
        log.log_info('Upgrading from version ' + version)
        while version:
            next_version = getattr(self, version)()
            if next_version == version:
                raise Exception('Version migrate from %s stuck in same version' % version)
            version = next_version
        # Perform common migration ops
        self.common_migration_ops()


def main():
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument('-o',
                            dest='operation',
                            metavar='operation (migrate, set_version, get_version)',
                            type = str,
                            required = False,
                            choices=['migrate', 'set_version', 'get_version'],
                            help = 'operation to perform [default: get_version]',
                            default='get_version')
        parser.add_argument('-s',
                        dest='socket',
                        metavar='unix socket',
                        type = str,
                        required = False,
                        help = 'the unix socket that the desired database listens on',
                        default = None )
        parser.add_argument('-n',
                        dest='namespace',
                        metavar='asic namespace',
                        type = str,
                        required = False,
                        help = 'The asic namespace whose DB instance we need to connect',
                        default = None )
        args = parser.parse_args()
        operation = args.operation
        socket_path = args.socket
        namespace = args.namespace

        if args.namespace is not None:
            SonicDBConfig.load_sonic_global_db_config(namespace=args.namespace)

        if socket_path:
            dbmgtr = DBMigrator(namespace, socket=socket_path)
        else:
            dbmgtr = DBMigrator(namespace)

        result = getattr(dbmgtr, operation)()
        if result:
            print(str(result))

    except Exception as e:
        log.log_error('Caught exception: ' + str(e))
        traceback.print_exc()
        print(str(e))
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
