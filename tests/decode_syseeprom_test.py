import importlib
import os
import sys
from unittest import mock

import pytest
from click.testing import CliRunner


test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
scripts_path = os.path.join(modules_path, 'scripts')
sys.path.insert(0, modules_path)

sys.modules['sonic_platform'] = mock.MagicMock()


decode_syseeprom_path = os.path.join(scripts_path, 'decode-syseeprom')
loader = importlib.machinery.SourceFileLoader('decode-syseeprom', decode_syseeprom_path)
spec = importlib.util.spec_from_loader(loader.name, loader)
decode_syseeprom = importlib.util.module_from_spec(spec)
loader.exec_module(decode_syseeprom)


class TestDecodeSyseeprom(object):
    def test_print_eeprom_dict(self, capsys):
        tlv_dict = {
            'header': {
                'id': 'TlvInfo',
                'version': '1',
                'length': '170'
            },
            'tlv_list': [{
                    'code': '0x21',
                    'name': 'Product Name',
                    'length': '8',
                    'value': 'S6100-ON'
                }, {
                    'code': '0x22',
                    'name': 'Part Number',
                    'length': '6',
                    'value': '0F6N2R'
                }, {
                    'code': '0x23',
                    'name': 'Serial Number',
                    'length': '20',
                    'value': 'TH0F6N2RCET0007600NG'
                }, {
                    'code': '0x24',
                    'name': 'Base MAC Address',
                    'length': '6',
                    'value': '0C:29:EF:CF:AC:A0'
                }, {
                    'code': '0x25',
                    'name': 'Manufacture Date',
                    'length': '19',
                    'value': '07/07/2020 15:05:34'
                }, {
                    'code': '0x26',
                    'name': 'Device Version',
                    'length': '1',
                    'value': '1'
                }, {
                    'code': '0x27',
                    'name': 'Label Revision',
                    'length': '3',
                    'value': 'A08'
                }, {
                    'code': '0x28',
                    'name': 'Platform Name',
                    'length': '26',
                    'value': 'x86_64-dell_s6100_c2538-r0'
                }, {
                    'code': '0x29',
                    'name': 'ONIE Version',
                    'length': '8',
                    'value': '3.15.1.0'
                }, {
                    'code': '0x2a',
                    'name': 'MAC Addresses',
                    'length': '2',
                    'value': '384'
                }, {
                    'code': '0x2b',
                    'name': 'Manufacturer',
                    'length': '5',
                    'value': 'CET00'
                }, {
                    'code': '0x2c',
                    'name': 'Manufacture Country',
                    'length': '2',
                    'value': 'TH'
                }, {
                    'code': '0x2d',
                    'name': 'Vendor Name',
                    'length': '4',
                    'value': 'DELL'
                }, {
                    'code': '0x2e',
                    'name': 'Diag Version',
                    'length': '8',
                    'value': '3.25.4.1'
                }, {
                    'code': '0x2f',
                    'name': 'Service Tag',
                    'length': '7',
                    'value': 'F3CD9Z2'
                }
            ],
            'checksum_valid': True
        }

        expected_output = '''\
TlvInfo Header:
   Id String:    TlvInfo
   Version:      1
   Total Length: 170
TLV Name             Code      Len  Value
-------------------  ------  -----  --------------------------
Product Name         0X21        8  S6100-ON
Part Number          0X22        6  0F6N2R
Serial Number        0X23       20  TH0F6N2RCET0007600NG
Base MAC Address     0X24        6  0C:29:EF:CF:AC:A0
Manufacture Date     0X25       19  07/07/2020 15:05:34
Device Version       0X26        1  1
Label Revision       0X27        3  A08
Platform Name        0X28       26  x86_64-dell_s6100_c2538-r0
ONIE Version         0X29        8  3.15.1.0
MAC Addresses        0X2A        2  384
Manufacturer         0X2B        5  CET00
Manufacture Country  0X2C        2  TH
Vendor Name          0X2D        4  DELL
Diag Version         0X2E        8  3.25.4.1
Service Tag          0X2F        7  F3CD9Z2

(checksum valid)
'''

        decode_syseeprom.print_eeprom_dict(tlv_dict)
        captured = capsys.readouterr()
        assert captured.out == expected_output
