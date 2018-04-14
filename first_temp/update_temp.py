#!/usr/bin/env python
import paho.mqtt.client as mqtt
import sqlite3
import datetime
import os
from multiprocessing import Process
from time import sleep
import RPi.GPIO as GPIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime


GPIO.setmode(GPIO.BCM)
Topic="TEMP"
Broker="192.168.0.106"
wr_db=None
max_row = 400

class WR_DB():
    def __init__(self, table_name):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),\
                  "Temp.db")
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        sql = 'create table if not exists {0}\
              (date_time text, temp text, sensor text)'\
              .format(table_name)
        self.c.execute(sql)
        self.conn.commit()
		
    def w_record(self, temp_str, sensor, table_name):
        time_str = datetime.datetime.now()
        data = (time_str, temp_str, sensor)
        wr_str='INSERT INTO {0} values (?,?,?)'.format(table_name)
        self.c.execute(wr_str, data)
        self.conn.commit()

    def del_un(self, table_name):
        del_str="delete from {1} where (select count(date_time) \
                from {1})> {0} and date_time in (select date_time\
                from {1} order by date_time desc limit (select\
                count(date_time) from {1}) offset {0})"\
                .format(max_row, table_name)
        self.c.execute(del_str)
        self.conn.commit()

    def close(self):
        self.conn.close()
class Select_db():
    def __init__(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),\
                  "Temp.db")
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
    def get_dt(self, table_name):
        sql = 'SELECT * FROM {0}'.format(table_name) 
        self.c.execute(sql)
        return self.c.fetchall()
    def close_dt(self):
        self.conn.close()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(Topic)

def get_temp():
    file_name = "/sys/bus/w1/devices/28-000007eb5874/w1_slave"
    f=open(file_name)
    temp_all=f.readlines()
    f.close()
    temp_float=float(temp_all[1].split('t=')[1])/1000

    return temp_float

def set_led(gpio_led=26):
    GPIO.setup(gpio_led, GPIO.OUT)
    GPIO.output(gpio_led,True)
    sleep(1)
    GPIO.output(gpio_led,False)

def read_temp(table_name):
    get_temp = Select_db()
    values = get_temp.get_dt(table_name)
    get_temp.close_dt()
    return values

def create_img(table_name):
    file_path = os.path.dirname(os.path.abspath(__file__))
    filename = "{0}.png".format(table_name.split("_")[1])
    img_path = os.path.join(file_path, 'static', filename)

    #values = read_temp('temp_out')
    
    values = read_temp(table_name)
    last_update = ""
    temp_array=[]
    for value in values:
        try:
            temp_array.append(float(value[1]))
            last_update = value[0]
        except ValueError:
            pass
    last_update_s = datetime.datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S.%f")
    last_update = last_update_s.strftime("%Y-%m-%d %H:%M:%S")
    
    plt.plot(temp_array)
    title = "Last update: {0}".format(last_update)
    plt.title(title)
    plt.savefig(img_path)
    plt.close()

def on_message(client, userdata, msg):

    #insert out_sensor
    temp_str = msg.payload.split(":")
    wr_out.w_record(temp_str[1], temp_str[0], 'temp_out')
    print(msg.topic+" "+msg.payload)
    wr_out.del_un('temp_out')
    create_img('temp_out')
    set_led()

def fun_in(db_obj):
    #insert in_sensor
    sleep(5)
    while True:
        print("record sensor in room")
        db_obj.w_record(str(get_temp()), "127.0.0.1", 'temp_in')
        db_obj.del_un('temp_in')
        create_img('temp_in')
        sleep(30)
    

def fun_out():
    client.on_connect = on_connect
    client.on_message = on_message
    while True:
        try:
            client.connect(Broker, 1883, 62)
            break
        except:
            sleep(1)
    client.loop_forever()


if __name__=="__main__":
    client = mqtt.Client()
    wr_out = WR_DB("temp_out")
    wr_in = WR_DB("temp_in")
    procs = []
    procs.append(Process(target=fun_in, args=(wr_in,)))
    procs.append(Process(target=fun_out, args=()))
    for x in procs:
        x.start()
