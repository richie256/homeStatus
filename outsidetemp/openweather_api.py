# OutsideTemp service

from flask import Flask
from flask import Response
from flask import jsonify
from flask import request

from flask_restful import Resource, Api

# import urllib2
from urllib.request import urlopen

import json
import time

from dateutil import tz
import calendar
import sys

import logging


# create logger with 'openweather_application'
logger = logging.getLogger('openweather_application')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('openweather.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

app = Flask(__name__)
api = Api(app)

import socket

def internet(host="1.1.1.1", port=53, timeout=3):
    """
    Host: 1.1.1.1 (1dot1dot1dot1.cloudflare-dns.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print(ex.message)
        return False

class OutsideTemp(Resource):

    CONST_JSON = 'JSON'
    CONST_INFLUX = 'influx'

    global location
    global location_id
    global tempVal
    global observation_epoch

    global pressure
    global humidity

    # Wind
    global windSpeed
    global windDeg

    # Weather condition
    global weatherId
    global weatherMain
    global weatherDescription

    #global OPENWEATHER_LOCATION_ID
    global OPENWEATHER_API_KEY
    global OPENWEATHER_UNITS

    def __init__(self):

        self.tempVal = ''
        self.pressure = 0
        self.humidity = 0
        self.observation_epoch = 0

        # Wind
        self.windSpeed = ''
        self.windDeg = 0

        # Weather condition
        self.weatherId = 0
        self.weatherMain = ''
        self.weatherDescription = ''

        self.location = ''

        logger.info('About to retrieve the format')
        self.success_result = True
        self.opt_format = request.args.get("format")
        if self.opt_format is None:
            self.opt_format = self.CONST_JSON

        # Load variables
        with open('openweather-vars.json') as f:
            configdata = json.load(f)

            #self.OPENWEATHER_LOCATION_ID = configdata['LOCATION_ID']
            self.OPENWEATHER_API_KEY = configdata['API_KEY']
            self.OPENWEATHER_UNITS = configdata['UNITS']
        logger.info('Api Key:' + self.OPENWEATHER_API_KEY)
        logger.info('Units:' + self.OPENWEATHER_UNITS)


    def getOutsideInfos(self, location_id):
        #Initialize
        self.success_result = True
        openweathermap = None
        iconnected=False

        try:
            self.location_id = location_id

            nboftrials=0

            while not iconnected and nboftrials<5:
                iconnected=internet()
                if not iconnected:
                    nboftrials+=1
                    sleep(10)

            #Python 3.4:
            openweathermap = urlopen('http://api.openweathermap.org/data/2.5/weather?id=' + str(location_id) + '&appid=' + self.OPENWEATHER_API_KEY + '&units=' + self.OPENWEATHER_UNITS )


            json_string = openweathermap.read()
            parsed_json = json.loads(json_string)

            # Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
            self.tempVal = parsed_json['main']['temp']

            # Atmospheric pressure (on the sea level, if there is no sea_level or grnd_level data), hPa
            self.pressure = int(parsed_json['main']['pressure'])

            # Humidity, %
            self.humidity = int(parsed_json['main']['humidity'])

            # Time of data calculation, unix, UTC
            self.observation_epoch = int(parsed_json['dt'])

            # Wind
            # Unit Default: meter/sec, Metric: meter/sec, Imperial: miles/hour.
            self.windSpeed = parsed_json['wind']['speed']
            self.windDeg   = int(parsed_json['wind']['deg'])

            # Weather condition
            self.weatherId = int(parsed_json['weather'][0]['id'])
            self.weatherMain = parsed_json['weather'][0]['main']
            self.weatherDescription = parsed_json['weather'][0]['description']

            self.location = parsed_json['name']


        except:
            self.success_result = False
            if openweathermap is not None:
                logger.error('Problem with getting outside infos in JSON. openweathermap = '+str(openweathermap) +' and json_string = '+str(json_string))
            else:
                logger.error('Problem with getting outside infos in JSON. openweathermap is None.')

            # logger.error(sys.exc_info()[0])
            logger.error(sys.exc_info())
            return sys.exc_info()[0]

        finally:
            if openweathermap is not None:
                openweathermap.close()

    def get(self,location_id):
        logger.info('Receive a request. location_id: ' + str(location_id))
        count = 0
        self.success_result = False

        while (not self.success_result):
            self.getOutsideInfos(location_id)

            count += 1
            if (count >= 3) or (self.success_result == True):
                break
            else:
                time.sleep(3)

        if (not self.success_result):
            abort(500)

        # JSON Format
        if self.opt_format == self.CONST_JSON:

            outsideTemp = { 'service': 'outsideTemp',
                            'tempVal': self.tempVal,
                            'pressure': self.pressure,
                            'humidity': self.humidity,
                            'observation_epoch': self.observation_epoch,
                            'windSpeed': self.windSpeed,
                            'windDeg': self.windDeg,
                            'weatherId': self.weatherId,
                            'weatherMain': self.weatherMain,
                            'weatherDescription': self.weatherDescription,
                            'location': self.location
                          }

            return jsonify(outsideTemp)

        # Infux format
        elif self.opt_format == self.CONST_INFLUX:

            influxdb_measurement = 'apidata'
            influxdb_tag_set = 'source=wunderground,location=' + self.location + ',opt_format=' + self.opt_format
            influxdb_field_set = 'tempVal=' + str(self.tempVal) + ',humidity=' + str(self.humidity) + ',windSpeed=' + str(self.windSpeed) + ',windDeg=' + str(self.windDeg) + ',weatherId=' + str(self.weatherId)
            influxdb_timestamp = str(self.observation_epoch) + '000000000'

            returnValue = ( influxdb_measurement + ',' + influxdb_tag_set + ' ' + influxdb_field_set + ' ' + influxdb_timestamp + '\n' )

            return Response(returnValue, mimetype='text/xml')


    #GET /conditions/Brossard?format=influx

api.add_resource(OutsideTemp, '/conditions/<int:location_id>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

