#!/usr/bin/env python
import paho.mqtt.client as mqtt
import sqlite3
import datetime
import os
from time import sleep
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

Topic="TEMP"
Broker="192.168.0.106"
wr_db=None
max_row = 200

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
def read_temp():
    conn = sqlite3.connect('Temp.db')
    c = conn.cursor()
    c.execute('SELECT * FROM temp_out')
    values =c.fetchall()
    conn.close()
    return values

def create_img():
    #values = read_temp('temp_out')
    values = read_temp()
    temp_array=[]
    for value in values:
        try:
            temp_array.append(float(value[1]))
        except ValueError:
            pass
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.plot(temp_array)
    plt.savefig("./static/txt.png")


def on_message(client, userdata, msg):

    #insert out_sensor
    print(msg.payload)
    temp_str = msg.payload.split(":")
    wr_out.w_record(temp_str[1], temp_str[0], 'temp_out')
    print(msg.topic+" "+msg.payload)
    wr_out.del_un('temp_out')

    #insert in_sensor
    print("record sensor in room")
    wr_in.w_record(str(get_temp()), "127.0.0.1", 'temp_in')
    wr_in.del_un('temp_in')
    create_img()

if __name__=="__main__":
    client = mqtt.Client()
    wr_out = WR_DB("temp_out")
    wr_in = WR_DB("temp_in")
    client.on_connect = on_connect
    client.on_message = on_message
    while True:
        try:
            client.connect(Broker, 1883, 62)
            break
        except:
            sleep(1)
     
    
    client.loop_forever()
