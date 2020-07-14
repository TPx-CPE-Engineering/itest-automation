
# Used in BGP Test Cases
# bgp_3.00_verify_neighbor_adjacency_advertised_received
# bgp_3.01_verify_md5_authentication
# bgp_3.02_verify_prepend_count
# bgp_3.03_verify_med

DEFAULT_BGP_INFORMATION = {
    'Config System': {
        'enable': True,                 # Enable BGP, default True
        'asn': 64514,                   # Autonomous System Number, default 64514
        'rtr_id': '192.168.131.1',      # Router ID, default 192.168.131.1
        'graceful_restart_en': False,   # Graceful Restart, default False
        'max_restart_time': 120,        # Max Restart Time, default 120
        'stale_path_time': 150,         # Stale Path Time, default 150
        'remote_as_path_advertise': False,      # AS Path Propagate, default False
        'redist_ospf': True,            # Redistribute OSPF Routes to BGP, default True
        'redist_ospf_filter': 0,        # Filter Tag, default 0
        'log_nbr_msgs': True            # default, True
    },
    'BGP Peers': [{
        '192.168.131.99': {             # Default Neighbor 192.168.131.99
            'enable': True,             # Enable Peer, default True
            'self': '192.168.131.99',   # Peer IP, default 192.168.131.99
            'remote_as': 64514,         # Peer ASN, default 64514
            'import_rtes': True,        # Enable Imports, default True
            'type': 'Branch',           # Peer Type, default Branch
            'loc_pref': 100,            # Local Preference, default 100
            'med': 0,                   # MED, default 0
            'as_prepend': 0,            # AS Prepend Count (0..10), default 0
            'next_hop_self': False,     # Next-Hop-Self, default False
            'in_med': 0,                # Input Metric, default 0
            'ka': 30,                   # Keep Alive Timer*, default 30
            'hold': 90,                 # Hold Timer*, default 90
                                        # * Timer changes only take effect when BGP session is reset. Admin Down, Up
                                        #   for changes to take effect immediately.
            'export_map': 4294967295,
            'password': ''              # MD5 Password, empty string to be disabled, default empty string/disabled
        }
    }]
}
