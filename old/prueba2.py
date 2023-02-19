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

host='192.168.1.69:5000'
url='https://' + host + '/api/'
api_login='antonio'
api_password='adr'
token = None
expires = ""
cookies = []
headers = {'Content-Type': 'application/json;charset=UTF-8', 'Access-Control-Allow-Origin': '*'}
headers_auth = {}


def get_content(url, headers=headers):

    content = None

    try:
        # Get content
        r = requests.get(url, headers=headers, verify=False)
        # Decode JSON response into a Python dict:
        if not r.ok:
           print("Error.", r.text)
           return ""
        content = r.json()

    except requests.exceptions.HTTPError as e:
        print("Bad HTTP status code:", e)

    except requests.exceptions.RequestException as e:
       print("Network error:", e)

    return content


def get_sensors(url):

    url= url + 'sensors'
    data = get_content(url)

    sensors = []
    for d in data:
       for k, v in d.items():
          if k == 'name':
             sensors.append(v)

    return sensors


def get_sensor(url, sensor):

    url = url + 'sensor/' + s + '/now'
    data = get_content(url, headers_auth)
    return data


def login(url, api_login, api_password):
    url = url + 'user/login'
    print("Getting token...")
    data_get = {'name': api_login,
                'password': api_password
                }
    #r = requests.post(url, 'Content-Type': 'application/json;charset=UTF-8', data=data_get, verify=False)
    r = requests.post(url, json=data_get, verify=False)
    if r.ok:
         #print("OK")
         authToken = r.content
         cookies = dict(r.cookies)
         return authToken, cookies
    else:
        print("HTTP %i - %s, Message %s" % (r.status_code, r.reason, r.text))
        return ""

def authtoken():
    authtoken, cookies = login(url, api_login, api_password)
    #(b'{"name":"antonio","role":"user","token":{"value":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhbGciOiJIUzI1NiIsImV4cGlyZXMiOjE2NjAwODIyNTgsIm93bmVyIjoiYW50b25pbyIsInJvbGUiOiJ1c2VyIn0.DMEDIVYG89D_rqvwI4x2_kNXYmmy6c9BTrhJ_mz0Z08","expires":"2022-08-09T21:57:38.932080509Z","owner":"antonio","role":"user"}}', {})
    # devuelve un binario que es necesario decodificar
    raw_data = authtoken.decode('utf-8').replace("'", '"')
    # los datos en bruto los pasamos a json y lo transformamos en diccionario
    data = json.loads(raw_data)
    print("token: %s\nexpires: %s\n" % (data["token"]["value"], data["token"]["expires"]))

    return data["token"]["value"], data["token"]["expires"], cookies


def check_token(token, expires, cookies):
    if token == None:
        token, expires, cookies = authtoken()
    else:
       now = datetime.datetime.now()
       expires = expires.replace("T"," ").replace("Z", " ").split(".")[0]
       expires_datetime = datetime.datetime.strptime(expires, '%Y-%m-%d %H:%M:%S')
       if now > expires_datetime:
           print("Token expirado...")
           token, expires, cookies = authtoken()

    return token, expires, cookies



if __name__ == '__main__':

    while True:
       # Paso 1. Obtener los sensores
       sensors = get_sensors(url)

       # paso 2. Si no tonemos token o ha caudcado pedimos uno. 
       token, expires, cookies = check_token(token, expires, cookies)

       # paso 3. Obtenemos los datos de los sensores
       headers_auth = {'Content-Type': 'application/json;charset=UTF-8', 'Access-Control-Allow-Origin': '*', 'Authorization': 'Bearer {}'.format(token)}
       for s in sensors:
          data = get_sensor(url, s)
 
          for d in data:
             print("%s %s %s" % (d['sensor'], d['type'].strip('\n'), d['value']))

       time.sleep(60) 
