import random

from paho.mqtt import client as mqtt_client


class mqttc(object):
    def __init__(self):
        self.broker = 'localhost'
        self.port = 1883
        self.topic = "casa/sala/temperatura"
        # generate client ID with pub prefix randomly
        self.client_id = f'python-mqtt-{random.randint(0, 100)}'
        self.username = 'mqtt'
        self.password = 'mqttadr13164'

    # Connection
    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.client_id)
        client.username_pw_set("username", "password")
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client

    # Publish
    def publish(self, client):
        msg_count = 0
        while True:
            time.sleep(1)
            msg = f"messages: {msg_count}"
            result = client.publish(self.topic, msg)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                print(f"Send `{msg}` to topic `{self.topic}`")
            else:
                print(f"Failed to send message to topic {self.topic}")
            msg_count += 1


    # Subscription
    def subscribe(self, client):
        def on_message(client, userdata, msg):
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

        client.subscribe(self.topic)
        client.on_message = on_message


def run():
    client = mqttc()
    client.connect_mqtt()
    client.loop_start()
    publish(client)
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
