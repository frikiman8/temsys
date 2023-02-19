#
#
# Pasos a seguir para validar usuario
#===================================
#
#1.- Obtenemos los sensores actuales
#
#2.- Probamos a consultar un sensor o mejor si somos capaces de saber si el token está caducado, pedimos el token
#
#3.- Realizar una llamada POST para validar usuario y obtener un token
#
#curl --insecure -X POST https://192.168.1.69:5000/api/user/login -H "Content-Type: application/json" -d '{"name":"antonio","password":"adr"}'
#{"name":"antonio","role":"user","token":{"value":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGciOiJIUzI1NiIsImV4cGlyZXMiOjE2NTk5OTE4NDMsIm93bmVyIjoiYW50b25pbyIsInJvbGUiOiJ1c2VyIn0.HmFFP_2Kh98Q7aUURc5WbpB5Q_9Xy9rNVH9VZSMDHsg","expires":"2022-08-08T20:50:43.60163054Z","owner":"antonio","role":"user"}}
#
#4.- Una vez tenemos el token podemos consultar a los sensores
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
        self.topic = "casa/"  
        

    def get_content(self, url, headers):
        content = None

        try:
            print("Try 1")
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


    def check_token(self):
        # if token vacío
        if self.token == None:
            self.token, self.expires, self.cookies = self.authtoken()
        # comprobamos validez del token
        else:
            now = datetime.datetime.now()
            self.expires = self.expires.replace("T"," ").replace("Z", " ").split(".")[0]
            expires_datetime = datetime.datetime.strptime(self.expires, '%Y-%m-%d %H:%M:%S')
            # if token expirado
            if now > expires_datetime:
                print("Token expirado...")
                self.token, self.expires, self.cookies = self.authtoken()

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

    def get_sensor(self, sensor):
        url = self.url + 'sensor/' + sensor + '/now'
        data = self.get_content(url, self.headers)
        return data



def main():
    # Primer bucle infinito
    while True:
        # Paso 1. Obtener los sensores
        try:
            temsys.get_sensors()
        except:    
            temsys = Temsys()
            temsys.get_sensors()
            pass

        print("\nSensores\n")
        for sensor in temsys.sensors:
            print(sensor)

        # Paso 2. Si no obtenemos token o ha caducado solicitamos uno.
        print("\nGetting token...")
        temsys.check_token()
        print("token: %s\nExpiracion: %s\nCoookies: %s" % (temsys.token, temsys.expires, temsys.cookies))

        # paso 3. Obtenemos los datos de los sensores
        #headers_auth = {'Content-Type': 'application/json;charset=UTF-8', 'Access-Control-Allow-Origin': '*', 'Authorization': 'Bearer {}'.format(token)}
        temsys.headers_auth = temsys.headers
        temsys.headers_auth['Authorization'] = 'Bearer {}'.format(temsys.token)
        
        # Una vez tenemos todos los datos, entramos en este bucle infinito y si no da error permanecemos en él
        print("Try 2")
        try: 
            while True:
                print("\n--- %s ---\n" % datetime.datetime.now())
                for s in temsys.sensors:
                    data = temsys.get_sensor(s)
                    # Si no obtenemos datos salimos del bucle infinito y volvemos a conseguir los datos
                    if data == "" or data == None:
                        raise BreakIt

                    for d in data:
                        print("%s %s %s" % (d['sensor'], d['type'].strip('\n'), d['value']))

                        topic = temsys.topic + d['sensor'] + "/" + d['type']
                        mqttc = mqtt_client.Client("casa")                                     # Create instance of client with client ID “test”
                        mqttc.username_pw_set("mqtt","mqttadr13164")                           # Establece credenciales
                        mqttc.connect("localhost", 1883, keepalive=60, bind_address="")        # Connect to (broker, port, keepalive-time)
                        #mqttc.loop_start()                                                    # Start networking daemon
                        mqttc.subscribe(topic)
                        mqttc.publish(topic, d['value'])  
                        #mqttc.loop_stop()                                                      # Kill networking daemon

                time.sleep(60)
                
        except:
            BreakIt

if __name__ == '__main__':
    main()
