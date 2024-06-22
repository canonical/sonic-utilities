"""
Module holding the correct values for show CLI command outputs for the wcmp_test.py
"""

show_wcmp_status_empty = """\
No configuration is present in CONFIG DB
"""

show_wcmp_status_single_enabled = """\
W-ECMP
--------
enabled
"""
show_wcmp_status_single_enabled_json = """\
{
    "w-ecmp": "enabled"
}
"""
show_wcmp_status_single_disabled = """\
W-ECMP
--------
disabled
"""
show_wcmp_status_single_disabled_json = """\
{
    "w-ecmp": "disabled"
}
"""

show_wcmp_status_multi_disabled = """\
ASIC ID    W-ECMP
---------  --------
asic0      disabled
asic1      disabled
"""

show_wcmp_status_multi_disabled_json = """\
{
    "asic0": {
        "w-ecmp": "disabled"
    },
    "asic1": {
        "w-ecmp": "disabled"
    }
}
"""

show_wcmp_status_multi_asic0_enabled = """\
ASIC ID    W-ECMP
---------  --------
asic0      enabled
asic1      disabled
"""

show_wcmp_status_multi_asic0_enabled_json = """\
{
    "asic0": {
        "w-ecmp": "enabled"
    },
    "asic1": {
        "w-ecmp": "disabled"
    }
}
"""

show_wcmp_status_multi_asic1_enabled = """\
ASIC ID    W-ECMP
---------  --------
asic0      disabled
asic1      enabled
"""

show_wcmp_status_multi_asic1_enabled_json = """\
{
    "asic0": {
        "w-ecmp": "disabled"
    },
    "asic1": {
        "w-ecmp": "enabled"
    }
}
"""

show_wcmp_status_multi_enabled = """\
ASIC ID    W-ECMP
---------  --------
asic0      enabled
asic1      enabled
"""

show_wcmp_status_multi_enabled_json = """\
{
    "asic0": {
        "w-ecmp": "enabled"
    },
    "asic1": {
        "w-ecmp": "enabled"
    }
}
"""
