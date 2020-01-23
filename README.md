# iTest_Automation
Repo containing API python scripts to be used by iTest


## Assumptions for Velocloud Testing Setup
1. Edge's Firewall > Port Forwarding Rules: A port forwarding rule must be configured to get to the CPE behind the Edge. The rule's name must contain the
 string 'itest' for easy identification.
2. Edge's Device > WAN Settings: A link must be configured to be public wired and be named 'WAN - IP', example: 'WAN - 216.241.61.8'.