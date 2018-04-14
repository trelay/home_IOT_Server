#!/usr/bin/python
import RPi.GPIO as GPIO
import sqlite3
from time import time as tm

from flask import Blueprint, request, session, g, redirect, url_for, abort, \
     render_template, flash, current_app, Flask

import logging, time
import smbus
import os

GPIO.setmode(GPIO.BCM)
file_path = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

def get_temp(table_name):
    db_path = os.path.join(file_path, 'Temp.db')
    sql_str = "select * from {0} where  date_time \
              =(select * from (select date_time from \
              {0} order by date_time desc) limit 2)".format(table_name)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(sql_str)
    all=c.fetchall()[0]
    try:
        temp = float(all[1])
    except ValueError:
        temp = "NA"
    update = str(all[0])
    c.close()
    return (temp,update)

def get_ambient(dev=0x23):
    ONE_TIME_HIGH_RES_MODE = 0x20
    bus = smbus.SMBus(1)
    data = bus.read_i2c_block_data(dev,ONE_TIME_HIGH_RES_MODE)
    light_val = (data[1] + (256 * data[0])) / 1.2
    light="%.2f"%(light_val)
    
    return light

def set_led(gpio_led=26):
    GPIO.setup(gpio_led, GPIO.OUT)
    GPIO.output(gpio_led,True)
    time.sleep(0.5)
    GPIO.output(gpio_led,False)

@app.route('/')
def index_show():
    in_tuple = get_temp("temp_in")
    out_tuple = get_temp("temp_out")
    in_temp = in_tuple[0]
    in_dt = in_tuple[1][0:-7]
    out_temp = out_tuple[0]
    out_dt = out_tuple[1][0:-7]

    readlight = get_ambient()
    style = "mediumhot"
    if in_temp < 20:
        style = "cold"
    elif in_temp > 26:
        style = "hot"
    return render_template("index.html",cssclass=style, light=readlight,\
            in_temp = in_temp, in_dt = in_dt,\
            out_temp= out_temp, out_dt = out_dt)

@app.route('/out')
def out_show():
    time_tk = float(tm())
    return render_template("temp.html",table='out', time_tk= time_tk)

@app.route('/in')
def in_show():
    time_tk = float(tm())
    return render_template("temp.html",table='in', time_tk= time_tk)

@app.route('/temp')
def temp_show():
    time_tk = float(tm())
    return render_template("temp_all.html", time_tk= time_tk)

if __name__ == '__main__':
    log_name = os.path.join(file_path, 'flask.log')
    logging.basicConfig(filename=log_name,level=logging.INFO)
    app.run(host='0.0.0.0',debug=True)
