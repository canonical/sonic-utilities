show_pg_wm_shared_output="""\
Ingress shared pool occupancy per PG:
     Port    PG0    PG1    PG2    PG3    PG4    PG5    PG6    PG7
---------  -----  -----  -----  -----  -----  -----  -----  -----
Ethernet0    100    101    102    103    104    105    106    107
Ethernet4    400    401    402    403    404    405    406    407
Ethernet8    800    801    802    803    804    805    806    807
"""

show_pg_wm_hdrm_output="""\
Ingress headroom per PG:
     Port    PG0    PG1    PG2    PG3    PG4    PG5    PG6    PG7
---------  -----  -----  -----  -----  -----  -----  -----  -----
Ethernet0    100    101    102    103    104    105    106    107
Ethernet4    400    401    402    403    404    405    406    407
Ethernet8    800    801    802    803    804    805    806    807
"""

show_pg_persistent_wm_shared_output="""\
Ingress shared pool occupancy per PG:
     Port    PG0    PG1    PG2    PG3    PG4    PG5    PG6    PG7
---------  -----  -----  -----  -----  -----  -----  -----  -----
Ethernet0    200    201    202    203    204    205    206    207
Ethernet4    500    501    502    503    504    505    506    507
Ethernet8    900    901    902    903    904    905    906    907
"""

show_pg_persistent_wm_hdrm_output="""\
Ingress headroom per PG:
     Port    PG0    PG1    PG2    PG3    PG4    PG5    PG6    PG7
---------  -----  -----  -----  -----  -----  -----  -----  -----
Ethernet0    200    201    202    203    204    205    206    207
Ethernet4    500    501    502    503    504    505    506    507
Ethernet8    900    901    902    903    904    905    906    907
"""

show_queue_wm_unicast_output="""\
Egress shared pool occupancy per unicast queue:
     Port      UC0      UC1    UC2    UC3    UC4    UC5    UC6    UC7    UC8    UC9
---------  -------  -------  -----  -----  -----  -----  -----  -----  -----  -----
Ethernet0  2057328  2056704      0      0      0      0      0   2704    416     20
Ethernet4        0        0      0   1986   2567      0      0      0      0      0
Ethernet8        0        0   1040      0      0      0      0      0   8528   7696
"""

show_queue_pwm_unicast_output="""\
Egress shared pool occupancy per unicast queue:
     Port      UC0      UC1    UC2    UC3    UC4    UC5    UC6    UC7    UC8    UC9
---------  -------  -------  -----  -----  -----  -----  -----  -----  -----  -----
Ethernet0  3057328  3056704      0      0      0      0      0   3704    516     30
Ethernet4        0        0      0   2986   3567      0      0      0      0      0
Ethernet8        0        0   2040      0      0      0      0      0   9528   8696
"""

show_queue_wm_multicast_output="""\
Egress shared pool occupancy per multicast queue:
     Port    MC10    MC11    MC12    MC13    MC14    MC15    MC16    MC17    MC18    MC19
---------  ------  ------  ------  ------  ------  ------  ------  ------  ------  ------
Ethernet0     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A
Ethernet4     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A
Ethernet8     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A     N/A
"""

show_buffer_pool_wm_output="""\
Shared pool maximum occupancy:
                 Pool    Bytes
---------------------  -------
 egress_lossless_pool     1000
    egress_lossy_pool     2000
ingress_lossless_pool     3000
"""

show_buffer_pool_persistent_wm_output="""\
Shared pool maximum occupancy:
                 Pool    Bytes
---------------------  -------
 egress_lossless_pool     2000
    egress_lossy_pool     3000
ingress_lossless_pool     4000
"""

testData = {
             'show_pg_wm_shared' :  [ {'cmd' : ['priority-group', 'watermark', 'shared'],
                                       'rc_output': show_pg_wm_shared_output
                                      }
                                    ],
             'show_pg_wm_hdrm' :  [ {'cmd' : ['priority-group', 'watermark', 'headroom'],
                                     'rc_output': show_pg_wm_hdrm_output
                                    }
                                  ],
             'show_pg_pwm_shared' :  [ {'cmd' : ['priority-group', 'persistent-watermark', 'shared'],
                                        'rc_output': show_pg_persistent_wm_shared_output
                                       }
                                     ],
             'show_pg_pwm_hdrm' :  [ {'cmd' : ['priority-group', 'persistent-watermark', 'headroom'],
                                      'rc_output': show_pg_persistent_wm_hdrm_output
                                     }
                                   ],
             'show_q_wm_unicast' :  [ {'cmd' : ['queue', 'watermark', 'unicast'],
                                      'rc_output': show_queue_wm_unicast_output
                                      }
                                    ],
             'show_q_pwm_unicast' :  [ {'cmd' : ['queue', 'persistent-watermark', 'unicast'],
                                      'rc_output': show_queue_pwm_unicast_output
                                       }
                                     ],
             'show_q_wm_multicast' :  [ {'cmd' : ['queue', 'watermark', 'multicast'],
                                         'rc_output': show_queue_wm_multicast_output
                                        }
                                      ],
             'show_q_pwm_multicast' :  [ {'cmd' : ['queue', 'persistent-watermark', 'multicast'],
                                          'rc_output': show_queue_wm_multicast_output
                                         }
                                       ],
             'show_buffer_pool_wm' :  [ {'cmd' : ['buffer_pool', 'watermark'],
                                         'rc_output': show_buffer_pool_wm_output
                                        }
                                      ],
             'show_buffer_pool_pwm' :  [ {'cmd' : ['buffer_pool', 'persistent-watermark'],
                                          'rc_output': show_buffer_pool_persistent_wm_output
                                         }
                                       ]
           }
