#!/usr/bin/env python
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
from argparse import ArgumentParser
import os
import sys
import requests
import json
import datetime
import time
import paho.mqtt.client as mqtt_client
import random
import logging
from dblite import *
from datetime import datetime
    


class Temsys():
    # Inicializa objeto. TODO: pasar por parametros algunas constantes y definirlos por defecto
    def __init__ (self, servidor_temsys='192.168.1.69', port_temsys='5000', user_temsys='antonio', password_temsys='adr', work_dir='/usr/local/MisScripts/temsys/', 
              mqtt_server='localhost', mqtt_port='1883', mqtt_user='mqtt', mqtt_password='mqttadr13164', mqtt_root_topic='casa'):
        self.host = servidor_temsys + ':' + port_temsys
        self.url = 'https://' + self.host + '/api/'
        self.api_login = user_temsys
        self.api_password = password_temsys
        self.sensors = []
        self.token = None
        self.expires = ""
        self.cookies = []
        self.headers = {'Content-Type': 'application/json;charset=UTF-8', 'Access-Control-Allow-Origin': '*'}
        self.headers_auth = {}
        self.workdir = work_dir
        self.logfile = "log/temsys.log"
        self.delay = 60
        self.bdatos = "db/sensoresTHV.db"
        self.mqttc = mqtt_client.Client(mqtt_root_topic)
        self.mqttc.topic = mqtt_root_topic + '/'
        self.mqttc.username_pw_set(mqtt_user, mqtt_password)
        self.mqttserver_name = mqtt_server
        self.mqttserver_port = mqtt_port
        self.mqttserver_connected = False

    # Obtiene el contenido de los request al API
    def get_content(self, url, headers):
        content = None

        try:
            # Get content
            r = requests.get(url, headers=headers, verify=False, timeout=5.0)
            # Decode JSON response into a Python dict:
            if r.ok:
                content = r.json()
                return content
        except requests.exceptions.Timeout as e:
            #print("Response timeout:", e)
            logging.error("\tResponse timeout:")
        except requests.exceptions.HTTPError as e:
            #print("Bad HTTP status code:", e)
            logging.error("\tBad HTTP status code:")
        except requests.exceptions.RequestException as e:
            #print("Network error:", e)
            logging.error("\tNetwork error:")


    # Consultamos los sensores existentes. No necesario token. Devuelve lista de sensores
    def get_sensors(self):
        self.sernsors = []
        url = self.url + 'sensors'
        data = self.get_content(url, self.headers)

        if data:
            for d in data:
                for k, v in d.items():
                    if k == 'name':
                        self.sensors.append(v)


    # consulta datos de un sensor. Necesita token. Devuelve datos como diccionario
    def get_sensor(self, sensor):
        url = self.url + 'sensor/' + sensor + '/now'
        data = self.get_content(url, self.headers)
        return data

     # Comprueba expiración de tokens. Si lo ha pedido devuelve 1, si no es necesario devuelve 0
    def check_token(self):
        if self.token == None:
            self.token, self.expires, self.cookies = self.authtoken()
            return 1
        # comprobamos validez del token. si es actual devuelve 0 sino lo pide y devuelve 1
        else:
            now = datetime.now()
            self.expires = self.expires.replace("T"," ").replace("Z", " ").split(".")[0]
            expires_datetime = datetime.strptime(self.expires, '%Y-%m-%d %H:%M:%S')
            # if token expirado. pide un token
            if now > expires_datetime:
                #print("Token expirado...")
                logging.info("\tExpired token...")
                self.token, self.expires, self.cookies = self.authtoken()
                return 1
            return 0

    # if sensores vacío o necesitamos forzar el obtener los sensores
    def check_sensors(self, force=0):
        if self.sensors == None or self.sensors == [] or force == 1:
            self.get_sensors()
            return 1
        # Si tenemos ya sensores
        else:
            return 0


    # Decodicifica el token devuelto en el login. Retorna token, expiración y cookies
    def authtoken(self):
        authtoken, cookies = self.login()
        #(b'{"name":"antonio","role":"user","token":{"value":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGciOiJIUzI1NiIsImV4cGlyZXMiOjE2NjAwODIyNTgsIm93bmVyIjoiYW50b25pbyIsInJvbGUiOiJ1c2VyIn0.DMEDIVYG89D_rqvwI4x2_kNXYmmy6c9BTrhJ_mz0Z08","expires":"2022-08-09T21:57:38.932080509Z","owner":"antonio","role":"user"}}', {})
        # devuelve un binario que es necesario decodificar
        raw_data = authtoken.decode('utf-8').replace("'", '"')
        # los datos en bruto los pasamos a json y lo transformamos en diccionario
        data = json.loads(raw_data)

        return data["token"]["value"], data["token"]["expires"], cookies


    # realiza un login para obtener el token. Retorna token codificado y cookies
    def login(self):
        url = self.url + 'user/login'
        data_get = {'name':     self.api_login,
                    'password': self.api_password
                    }
        r = requests.post(url, json=data_get, verify=False)
        if r.ok:
            authToken = r.content
            cookies = dict(r.cookies)
            return authToken, cookies
        else:
            #print("HTTP %i - %s, Message %s" % (r.status_code, r.reason, r.text))
            logging.info("\tHTTP %i - %s, Message %s" % (r.status_code, r.reason, r.text))
            return "", []

    # Abre la base de datos  
    def open_database(self, dir, filename):
        if dir == "" : 
            dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        if filename == "": 
            basedatos = dir + '/db/sensoresTHV.db' 
        else:
            basedatos = dir + filename
        logging.debug("\t### Opening database -> %s" % basedatos)
        return(SqliteDatabase(basedatos))

    # Callback on connect to mqtt server
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging("\tConnected OK returned code = ", rc)
            self.mqttserver_connected == True
        else:
             logging("Connected Not OK returned code = ", rc)
             self.mqttserver_connected == False

    # Realiza conexión servidor mqtt
    def connect_mqttserver(self, server="localhost", port=1883, keepalive=60, bind_address=""):
        self.mqttserver_name = server
        self.mqttserver_port = port
        try:
            self.mqttc.on_connect = self.on_connect
            self.mqttc.connect(self.mqttserver_name, self.mqttserver_port, keepalive, bind_address)
            self.mqttc.loop_start()
            time.sleep(4)
            self.mqttserver_connected = self.mqttc.is_connected()
            self.mqttc.loop_stop()
        except: 
            #print("Error al conectar con servidor mqtt " + server)
            self.mqttserver_connected = self.mqttc.is_connected()

    # Publica para sensor
    def public_mqtt_sensor(self, data):
        if (self.mqttserver_connected == False): 
            logging.info("\tWe do not publish because we are not connected to the mqtt server %s ", self.mqttserver_name)
            self.connect_mqttserver()
        else:
            for n in range(len(data)):
                #self.mqttc.loop_start()
                topic = self.mqttc.topic + data[n]['sensor'] + "/" + data[n]['type']
                self.mqttc.publish(topic, data[n]['value'])
                logging.info("Sensor: %s tipo: %s valor: %s -> topic publicado: %s" % (data[n]['sensor'], data[n]['type'].strip('\n'), data[n]['value'], topic))
                #self.mqttc.loop_stop()
                self.mqttserver_connected = self.mqttc.is_connected()


def options():
    argp = ArgumentParser(
       prog="temsys.py",
       description="Make temsys api call and send data by MQtt",
       #version="23-Septiembre-2022",
       epilog="Antonio Delgado Rodriguez",
       add_help=True
    )

    argp.add_argument('-d','--debug_level',help='Nivel de debug CRITICAL 50, ERROR 40 WARNING 30 INFO 20 DEBUG 10 NOTSET 0',
                    required=False,dest='debug_level',type=int, default=20)
    argp.add_argument('-st','--servidor_temsys',help='Servidor temsys',
                    required=False,dest='servidor_temsys',type=str, default='192.168.1.69')
    argp.add_argument('-pt','--port_temsys',help='Puerto escucha servidor temsys',
                    required=False,dest='port_temsys', type=str, default='5000')
    argp.add_argument('-ut','--user_temsys',help='Usuario api temsys',
                    required=False,dest='user_temsys', type=str, default='antonio')
    argp.add_argument('-Pt','--password_temsys',help='Password api temsys',
                    required=False,dest='password_temsys', type=str, default='adr')
    argp.add_argument('-wd','--work_dir',help='Directorio de trabajo',
                    required=False,dest='work_dir', type=str, default='/usr/local/MisScripts/temsys/')
    argp.add_argument('-ms','--mqtt_server',help='Servidor MQtt',
                    required=False,dest='mqtt_server', type=str, default='localhost')
    argp.add_argument('-mp','--mqtt_port',help='Port servidor MQtt',
                    required=False,dest='mqtt_port', type=str, default='1883')
    argp.add_argument('-mu','--mqtt_user',help='Usuario MQtt',
                    required=False,dest='mqtt_user', type=str, default='mqtt')
    argp.add_argument('-mP','--mqtt_password',help='Password MQtt',
                    required=False,dest='mqtt_password', type=str, default='mqttadr13164')
    argp.add_argument('-mt','--mqtt_root_topic',help='Root topic MQtt',
                    required=False,dest='mqtt_root_topic', type=str, default='casa')
    #
    # Obtenemos argumentos linea comandos
    #
    args = argp.parse_args()
    return args
    

def main():
    #
    # Obtenemos argumentos linea comandos
    #
    args = options()

    # Instanciamos Temsys
    temsys = Temsys(args.servidor_temsys, args.port_temsys, args.user_temsys, args.password_temsys, args.work_dir, args.mqtt_server, 
                     args.mqtt_port, args.mqtt_user, args.mqtt_password, args.mqtt_root_topic)

    # Establecemos logging
    logging.basicConfig(filename=temsys.workdir + temsys.logfile, level=logging.getLevelName(args.debug_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

    logging.info('\t### Start')
    # Abre la base de datos
    db = temsys.open_database(temsys.workdir, temsys.bdatos)
    
    while True:
        logging.info('\t### Loop start')
        # Hora actual numerico y texto
        now = datetime.now()
        tnow = now.strftime('%d/%m/%Y %H:%M:%S')
        logging.info("\t--- %s ---" % tnow)
        # Paso 1. Comprobar sensores, los obtiene si no los tiene y si falla continua el bucle
        logging.info("\tCheck sensors...")
        temsys.check_sensors()
        if temsys.sensors == []:
            logging.info("\tI haven't sensors. wait 3 seconds...")
            time.sleep(3)
            continue

        # Comprueba que tenemos conexión con el servidor mqtt. Tres intentos de conexión
        for i in range(1,3):
            logging.info("\tTry connect with server mqtt %s..." % temsys.mqttserver_name)
            temsys.connect_mqttserver()
            if (temsys.mqttserver_connected == False):
                logging.info("\tError connecting to server mqtt %s" % temsys.mqttserver_name)
                time.sleep(1)
            else:
                logging.info("\tConnected to server mqtt %s" % temsys.mqttserver_name)
                break

        # Imprimimos los sensores existentes
        logging.info("\tSensors...")
        for sensor in temsys.sensors:
            logging.info("\t\t%s" % sensor)

        # Paso 2. Obtenemos token si es necesario. Si ha caducado solicitamos uno.
        logging.info("\tCheck token...")
        if temsys.check_token() == 1:
            logging.info("\tNew token: %s\nExpiration: %s\nCoookies: %s" % (temsys.token, temsys.expires, temsys.cookies))
        else:
            logging.info("I have token. Expiration %s" % (temsys.expires))

        # paso 3. Obtenemos los datos de los sensores
        #         Añadimos a cabecera estandar la autorización -> 'Authorization': 'Bearer {}'.format(token)}
        temsys.headers_auth = temsys.headers
        temsys.headers_auth['Authorization'] = 'Bearer {}'.format(temsys.token)

        # Para cada sensor
        for s in temsys.sensors:
            record = {'id_sensor': -1, 'temperature': 0.0, 'humidity': 0.0, 'VOD': ""}
            data = temsys.get_sensor(s)
            # Si no obtenemos datos salimos del bucle infinito y volvemos a conseguir los datos
            if data == "" or data == None:
                logging.error("\tNo %s sensor data..." % s)
                continue
            else:
                logging.debug(data)
                for n in range(len(data)):
                    id_sensor = db.select("select id_sensor from sensores where nombre = \'%s\';" % data[n]['sensor'])
                    if not id_sensor:
                        db.execute("insert into sensores (id_tipo, nombre, descripcion) values (%d, \'%s\', \'%s\');" \
                            % (0, data[n]['sensor'], data[n]['sensor']))
                        id_sensor = db.select("select id_sensor from sensores where nombre = \'%s\';" % data[n]['sensor'])
                        if not id_sensor:
                            logging.error("\tRecords are not inserted in the DB for not having defined sensors.....")
                            continue
                    record['id_sensor'] = id_sensor[0][0]
                    if data[n]['value']:
                        record[data[n]['type']] = data[n]['value']

                #Insertamos registro en la base de datos
                db.execute("insert into datos (id_sensor, temperatura, humedad, VOD, fecha) values (%d, %0.2f, %0.2f, \'%s\', \'%s\');" \
                            % (record['id_sensor'], record['temperature'], record['humidity'], record['VOD'], tnow))
                
                temsys.public_mqtt_sensor(data)

        # Desconectamos del servidor mqtt y esperamos 1 minuto
        temsys.mqttc.disconnect()
        logging.info('\t### Wait for %d seconds' % temsys.delay)
        time.sleep(temsys.delay)


if __name__ == '__main__':
    main()
