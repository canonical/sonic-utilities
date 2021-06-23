"""
Module holding correct show CLI command outputs for the pbh_test.py
"""

show_pbh_hash_fields="""\
NAME               FIELD              MASK         SEQUENCE  SYMMETRIC
-----------------  -----------------  ---------  ----------  -----------
inner_ip_proto     INNER_IP_PROTOCOL  N/A                 1  No
inner_l4_dst_port  INNER_L4_DST_PORT  N/A                 2  Yes
inner_l4_src_port  INNER_L4_SRC_PORT  N/A                 2  Yes
inner_dst_ipv4     INNER_DST_IPV4     255.0.0.0           3  Yes
inner_src_ipv4     INNER_SRC_IPV4     0.0.0.255           3  Yes
inner_dst_ipv6     INNER_DST_IPV6     ffff::              4  Yes
inner_src_ipv6     INNER_SRC_IPV6     ::ffff              4  Yes
"""


show_pbh_hash="""\
NAME           HASH FIELD
-------------  -----------------
inner_v4_hash  inner_ip_proto
               inner_l4_dst_port
               inner_l4_src_port
               inner_dst_ipv4
               inner_src_ipv4
inner_v6_hash  inner_ip_proto
               inner_l4_dst_port
               inner_l4_src_port
               inner_dst_ipv6
               inner_src_ipv6
"""


show_pbh_table="""\
NAME        INTERFACE        DESCRIPTION
----------  ---------------  ---------------
pbh_table1  Ethernet0        NVGRE
            Ethernet4
pbh_table2  PortChannel0001  VxLAN
            PortChannel0002
pbh_table3  Ethernet0        NVGRE and VxLAN
            Ethernet4
            PortChannel0001
            PortChannel0002
"""


show_pbh_rule="""\
TABLE       RULE      PRIORITY  MATCH                                 HASH           ACTION         COUNTER
----------  ------  ----------  ------------------------------------  -------------  -------------  ---------
pbh_table1  nvgre            1  gre_key:           0x2500/0xffffff00  inner_v6_hash  SET_ECMP_HASH  DISABLED
                                inner_ether_type:  0x86dd/0xffff
pbh_table2  vxlan            2  ip_protocol:       0x11/0xff          inner_v4_hash  SET_LAG_HASH   ENABLED
                                l4_dst_port:       0x12b5/0xffff
                                inner_ether_type:  0x0800/0xfff
"""