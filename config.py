#!/usr/bin/env python3
from pkg import *

Topic="TEMP"
Broker="192.168.0.106"
out_ip = "192.168.0.102"
in_ip = "192.168.0.106"
data_len = 100

redis_host = "localhost"
redis_port = 6379
redis_password = ""


GPIO.setmode(GPIO.BCM)
led = 26

r=np.NaN
