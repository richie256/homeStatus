# OutsideTemp service

from flask import Flask
from flask import Response
from flask import jsonify
from flask import request

from flask_restful import Resource, Api

# import urllib2
from urllib.request import urlopen

#import datetime, time
#import pytz
import json

from dateutil import tz
import calendar
import sys

import logging



class OutsideTemp(Resource):

    CONST_JSON = 'JSON'
    CONST_INFLUX = 'influx'

    global location
    global tempVal
    global relativeHumidity
    global observation_epoch

    global sunrise
    global sunset
    global sunrise_dict
    global sunset_dict

    global wind_string
    global wind_dir
    global wind_degrees
    global wind_kph
    global wind_gust_kph

    global OPENWEATHER_LOCATION_ID
    global OPENWEATHER_API_KEY
    global OPENWEATHER_UNITS

    def __init__(self):

        self.tempVal = 0
        self.pressure = 0
        self.humidity = 0
        self.observation_epoch = 0

        # Wind
        self.windSpeed = 0
        self.windDeg = 0

        # Weather condition
        self.weatherId = 0
        self.weatherMain = ''
        self.weatherDescription = ''

        self.location = ''

        self.success_result = True
        self.opt_format = request.args.get("format")
        if self.opt_format is None:
            self.opt_format = self.CONST_JSON

        # Load variables
        with open('openweather-vars.json') as f:
            configdata = json.load(f)
 
 		self.OPENWEATHER_LOCATION_ID = configdata['LOCATION_ID']
        self.OPENWEATHER_API_KEY = configdata['API_KEY']
        self.OPENWEATHER_UNITS = configdata['UNITS']


    def getOutsideInfos(self, location):
        try:
            self.location = location

            iconnected=False
            nboftrials=0

            while not iconnected and nboftrials<5:
                iconnected=internet()
                if not iconnected:
                    nboftrials+=1
                    sleep(10)

            # logger.debug('Trying to get JSON from openweathermap')

 
            #Python 3.4:
            openweathermap = None
            openweathermap = urlopen('http://api.openweathermap.org/data/2.5/weather?id=' + OPENWEATHER_LOCATION_ID + '&appid=' + OPENWEATHER_API_KEY + '&units=metric' + OPENWEATHER_UNITS )


            json_string = openweathermap.read()
            parsed_json = json.loads(json_string)

            # Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
            self.tempVal = int(parsed_json['main']['temp'])

            # Atmospheric pressure (on the sea level, if there is no sea_level or grnd_level data), hPa
            self.pressure = int(parsed_json['main']['pressure'])

            # Humidity, %
            self.humidity = int(parsed_json['main']['humidity'])

            # Time of data calculation, unix, UTC
            self.observation_epoch = int(parsed_json['dt'])

            # Wind
            # Unit Default: meter/sec, Metric: meter/sec, Imperial: miles/hour.
            self.windSpeed = parsed_json['wind']['speed']
            self.windDeg   = parsed_json['wind']['deg']

            # Weather condition
            self.weatherId = parsed_json['weather']['id']
            self.weatherMain = parsed_json['weather']['main']
            self.weatherDescription = parsed_json['weather']['description']

            self.location = parsed_json['name']


        except:
            self.success_result = False
            if openweathermap is not None:
                logger.error('Problem with getting outside infos in JSON. openweathermap = '+str(openweathermap) +' and json_string = '+str(json_string))
            else:
                logger.error('Problem with getting outside infos in JSON. openweathermap is None.')


            logger.error(sys.exc_info()[0])
            return sys.exc_info()[0]

        finally:
            if openweathermap is not None:
                openweathermap.close()

    def get(self,location):

        self.getOutsideInfos(location)

        if (not self.success_result):
            return ''

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

            influxdb_measurement = apidata
            influxdb_tag_set = 'source=wunderground,location=' + self.location + ',opt_format=' + self.opt_format
            influxdb_field_set = 'tempVal=' + str(self.tempVal) + ',humidity=' + str(self.humidity) + ',windSpeed=' + str(windSpeed) + ',windDeg=' + str(windDeg) + ',weatherId=' + str(weatherId)
            influxdb_timestamp = self.observation_epoch + '000000000'

            returnValue = ( influxdb_measurement + ',' + influxdb_tag_set + ' ' + influxdb_field_set + ' ' + influxdb_timestamp + '\n' )

            return Response(returnValue, mimetype='text/xml')


    #GET /conditions/Brossard?format=influx

api.add_resource(OutsideTemp, '/conditions/<string:location>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

