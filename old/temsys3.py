#
#
# Pasos a seguir para validar usuario
#===================================
#
#1.- Obtenemos los sensores actuales
#
#2.- Comprobamos token y si caducado obtenemos otro. Realizar una llamada POST para validar usuario y obtener un token
#
#3.- Consultamos sensor por sensor
#
#4.- Mandamos por MQTT los datos de los sensores.
#
#curl --insecure -X POST https://192.168.1.69:5000/api/user/login -H "Content-Type: application/json" -d '{"name":"antonio","password":"adr"}'
#{"name":"antonio","role":"user","token":{"value":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGciOiJIUzI1NiIsImV4cGlyZXMiOjE2NTk5OTE4NDMsIm93bmVyIjoiYW50b25pbyIsInJvbGUiOiJ1c2VyIn0.HmFFP_2Kh98Q7aUURc5WbpB5Q_9Xy9rNVH9VZSMDHsg","expires":"2022-08-08T20:50:43.60163054Z","owner":"antonio","role":"user"}}
#
#curl --insecure https://192.168.1.69:5000/api/sensor/habitacion/now -H "Content-Type: application/json" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGciOiJIUzI1NiIsImV4cGlyZXMiOjE2NTk5OTE4NDMsIm93bmVyIjoiYW50b25pbyIsInJvbGUiOiJ1c2VyIn0.HmFFP_2Kh98Q7aUURc5WbpB5Q_9Xy9rNVH9VZSMDHsg"
#[{"type":"temperature","sensor":"habitacion","date":"2022-08-08T15:55:19.858Z","value":30.9},{"type":"humidity","sensor":"habitacion","date":"2022-08-08T15:55:19.858Z","value":31}]
#
#
import requests
import json
import datetime
import time
import paho.mqtt.client as mqtt_client
import random
import logging

class BreakIt(Exception): pass

class Temsys():
    def __init__ (self):
        self.host = '192.168.1.69:5000'
        self.url = 'https://' + self.host + '/api/'
        self.api_login = 'antonio'
        self.api_password ='adr'
        self.sensors = []
        self.token = None
        self.expires = ""
        self.cookies = []
        self.headers = {'Content-Type': 'application/json;charset=UTF-8', 'Access-Control-Allow-Origin': '*'}
        self.headers_auth = {}
        self.logfile = 'temsys.log'
        self.mqttc = mqtt_client.Client("casa")
        self.mqttc.topic = "casa/"
        self.mqttc.username_pw_set("mqtt","mqttadr13164")
        self.mqttc.connect("192.168.1.63", 1883, keepalive=60, bind_address="")


    def get_content(self, url, headers):
        content = None

        try:
            # Get content
            r = requests.get(url, headers=headers, verify=False)
            # Decode JSON response into a Python dict:
            if not r.ok:
                raise ("Error. " + r.text)
                return ""
            else:
                content = r.json()

        except requests.exceptions.HTTPError as e:
            print("Bad HTTP status code:", e)

        except requests.exceptions.RequestException as e:
            print("Network error:", e)

        return content


    def get_sensors(self):
        url = self.url + 'sensors'
        data = self.get_content(url, self.headers)

        for d in data:
            for k, v in d.items():
                if k == 'name':
                    self.sensors.append(v)


    def get_sensor(self, sensor):
        url = self.url + 'sensor/' + sensor + '/now'
        data = self.get_content(url, self.headers)
        return data


    def check_token(self):
        # if token vacío
        if self.token == None:
            self.token, self.expires, self.cookies = self.authtoken()
            return 1
        # comprobamos validez del token
        else:
            now = datetime.datetime.now()
            self.expires = self.expires.replace("T"," ").replace("Z", " ").split(".")[0]
            expires_datetime = datetime.datetime.strptime(self.expires, '%Y-%m-%d %H:%M:%S')
            # if token expirado
            if now > expires_datetime:
                print("Token expirado...")
                self.token, self.expires, self.cookies = self.authtoken()
                return 1
            return 0

    def check_sensors(self, force=0):
        # if sensores vacío
        if self.sensors == None or self.sensors == [] or force == 1:
            self.get_sensors()
            return 1
        # Si tenemos ya sensores
        else:
            return 0


    def authtoken(self):
        authtoken, cookies = self.login()
        #(b'{"name":"antonio","role":"user","token":{"value":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGciOiJIUzI1NiIsImV4cGlyZXMiOjE2NjAwODIyNTgsIm93bmVyIjoiYW50b25pbyIsInJvbGUiOiJ1c2VyIn0.DMEDIVYG89D_rqvwI4x2_kNXYmmy6c9BTrhJ_mz0Z08","expires":"2022-08-09T21:57:38.932080509Z","owner":"antonio","role":"user"}}', {})
        # devuelve un binario que es necesario decodificar
        raw_data = authtoken.decode('utf-8').replace("'", '"')
        # los datos en bruto los pasamos a json y lo transformamos en diccionario
        data = json.loads(raw_data)

        return data["token"]["value"], data["token"]["expires"], cookies


    def login(self):
        url = self.url + 'user/login'
        data_get = {'name':     self.api_login,
                    'password': self.api_password
                    }
        r = requests.post(url, json=data_get, verify=False)
        if r.ok:
            #print("OK")
            authToken = r.content
            cookies = dict(r.cookies)
            return authToken, cookies
        else:
            print("HTTP %i - %s, Message %s" % (r.status_code, r.reason, r.text))
            return "", []



def main():
    # Instanciamos Temsys
    temsys = Temsys()

    # Establecemos logging
    logging.basicConfig(filename=temsys.logfile, level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

    while True:
        #print("\n--- %s ---\n" % datetime.datetime.now())
        logging.info("--- %s ---" % datetime.datetime.now())
        # Paso 1. Comprobar sensores, los obtiene si no los tiene
        #print("\nCheck sensors...")
        logging.info("   Check sensors...")
        temsys.check_sensors()

        # Imprimimos los sensores existentes
        #print("\nSensores\n")
        logging.info("   Sensores...")
        for sensor in temsys.sensors:
            #print(sensor)
            logging.info(sensor)

        # Paso 2. Obtenemos token si es necesario. Si ha caducado solicitamos uno.
        #print("\nCheck token...")
        logging.info("   Check token...")
        if temsys.check_token() == 1:
            #print("New token: %s\nExpiracion: %s\nCoookies: %s" % (temsys.token, temsys.expires, temsys.cookies))
            logging.info("New token: %s\nExpiracion: %s\nCoookies: %s" % (temsys.token, temsys.expires, temsys.cookies))

        # paso 3. Obtenemos los datos de los sensores
        #         Añadimos a cabecera estandar la autorización -> 'Authorization': 'Bearer {}'.format(token)}
        temsys.headers_auth = temsys.headers
        temsys.headers_auth['Authorization'] = 'Bearer {}'.format(temsys.token)

        # Para cada sensor
        for s in temsys.sensors:
            data = temsys.get_sensor(s)
            # Si no obtenemos datos salimos del bucle infinito y volvemos a conseguir los datos
            if data == "" or data == None:
                #printf("No tenemos datos de los sensores")
                logging.Error("No tenemos datos de los sensores")
                break

            for d in data:
                #print("%s %s %s" % (d['sensor'], d['type'].strip('\n'), d['value']))
                topic = temsys.mqttc.topic + d['sensor'] + "/" + d['type']
                logging.info("Sensor: %s tipo: %s valor: %s -> topic publicado: %s" % (d['sensor'], d['type'].strip('\n'), d['value'], topic))
                #temsys.mqttc.subscribe(topic)
                temsys.mqttc.loop_start()
                temsys.mqttc.publish(topic, d['value'])
                temsys.mqttc.loop_stop()


        time.sleep(60)


if __name__ == '__main__':
    main()
