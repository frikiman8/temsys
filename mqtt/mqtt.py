import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/+")


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    print(payload)
    Iclient.write.points(payload, protocol='line')


def main():
    
    client = mqtt.Client ()
    client.username_pw_set('mqtt', 'mqttadr13164')
    client.on_message = on_message
    client.connect('localhost', 1883, 60)
    client.on_connect = on_connect
    Iclient = InfluxDBClient('localhost', '8086', 'mqtt', 'mqttadr13164')
    client.loop_forever()


if __name__ == '__main__':
    main()         





