from silverpeak import *


def login():
    sp = Silverpeak(user='juan.brena', user_pass='1Maule1!', sp_server='cpesp.lab-sv.telepacific.com', disable_warnings=True, auto_login=True)
    return sp
