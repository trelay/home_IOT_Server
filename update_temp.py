#!/usr/bin/env python3
from config import *

def get_temp():
    file_name = "/sys/bus/w1/devices/28-000007eb5874/w1_slave"
    f=open(file_name)
    temp_all=f.readlines()
    f.close()
    temp_float=float(temp_all[1].split('t=')[1])/1000

    return temp_float     
    
class LEDThread(threading.Thread):
    def __init__(self,led=26):
        threading.Thread.__init__(self)
        self.led= led
    def run(self):
        GPIO.setup(self.led, GPIO.OUT)
        GPIO.output(self.led,True)
        sleep(0.2)
        GPIO.output(self.led,False)

def read_temp(table_name):
    df = pd.DataFrame(columns=['ip', 'temp', 'timestamp'])
    out_list = r.lrange(table_name,0,-1)
    tmp_list=[]
    for ele in out_list:
        elelist = ele.split(":")
        elelist[1] = float(elelist[1])
        elelist[2] = pd.to_datetime(float(elelist[2]),unit='s')
        tmp_list.append(elelist)
    df = pd.DataFrame(tmp_list)
    df.columns=['ip', 'temp', 'timestamp']
    df.index = df.timestamp
    return df

def create_img(table_name):
    print("start creating img")
    file_path = os.path.dirname(os.path.abspath(__file__))
    table_type = table_name.split(":")[1]
    filename = "{0}.png".format(table_type)
    img_path = os.path.join(file_path, 'static', filename)
    
    df = read_temp(table_name)
    last_update = r.hgetall("last_update")[table_type]
    
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.set_title("host:{0}\n last_update:{1}".format(df['ip'][0], last_update))
    del df["ip"]
    del df["timestamp"]
    try:
        df.plot(ax=ax, style='b-')
        fig.savefig(img_path)
    except:
        print("Error")
        pass
    finally:
        plt.cla()
        plt.close(fig)
    print("finished creating img")
    
def fun_in(client):
    sleep(5)
    while True:
        client.publish(Topic,Broker+":"+str(get_temp()))
        sleep(30)

    
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(Topic)
    
def on_message(client, userdata, msg):
    #Light LED if new data comes in
    setled = LEDThread(led)
    setled.daemon = True
    setled.start()

    msg_s = msg.payload.decode()
    ip,temp = msg_s.split(":")
    print("MQTT: got {0} from {1}".format(temp,ip))
    
    if ip.strip() in out_ip:
        table_type = "out"
        table_name = Topic +":"+ table_type

    elif ip.strip() in in_ip:
        table_type = "in"
        table_name = Topic +":"+ table_type
    else:
        table_type = "un"
        table_name = Topic+ ":un"

    global r
    r.lpush(table_name, msg_s +":"+str(time()+28800))
    r.ltrim(table_name,0,data_len)
    last_update = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
    r.hset("last_update", table_type, last_update)
    create_img(table_name)

def Subscribe_TEMP(client):
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_forever()


if __name__=="__main__":
    client = mqtt.Client()
    
    while True:
        try:
            client.connect(Broker, 1883, 62)
            break
        except:
            sleep(1)
    
    global r
    r = redis.StrictRedis(host=redis_host, port=redis_port, \
            password=redis_password, decode_responses=True)
    procs = []
    procs.append(Process(target=fun_in, args=(client,)))
    procs.append(Process(target=Subscribe_TEMP, args=(client,)))
    for x in procs:
        x.start()
