

from flask import Flask
from flask import Response
from flask import jsonify
from flask import request

import json



class OutsideTemp(Resource):

    CONST_JSON = 'JSON'
    CONST_INFLUX = 'influx'
    CONST_DROPWIZARD = 'dropwizard'

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
        self.location = ''
        self.tempVal = ''
        self.relativeHumidity = 0
        self.observationTS = ''
        self.observation_epoch = ''

        self.sunrise = ''
        self.sunset = ''
        self.sunrise_dict = dict()
        self.sunset_dict = dict()

        self.wind_string = ''
        self.wind_dir = ''
        self.wind_degrees = ''
        self.wind_kph = 0
        self.wind_gust_kph = 0

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

            # logger.debug('Trying to get JSON from wunderground')



            # http://api.openweathermap.org/data/2.5/weather?id=5909629&appid=f4df49fe8112224e1cbc4818c810a73b&units=metric
 
            #Python 3.4:
            openweathermap = None
            openweathermap = urlopen('http://api.openweathermap.org/data/2.5/weather?id=' + OPENWEATHER_LOCATION_ID + '&appid=' + OPENWEATHER_API_KEY + '&units=metric' + OPENWEATHER_UNITS )


            json_string = openweathermap.read()
            parsed_json = json.loads(json_string)


			# Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
            self.tempVal = parsed_json['main']['temp']
            self.humidity = int(parsed_json['main']['humidity'])

            # Time of data calculation, unix, UTC
            observationDT = parsed_json['dt']


            #Wind
            # Unit Default: meter/sec, Metric: meter/sec, Imperial: miles/hour.
			self.windSpeed = parsed_json['wind']['speed']
			self.windDeg   = parsed_json['wind']['deg']



            self.wind_string = parsed_json['current_observation']['wind_string']
            self.wind_dir = parsed_json['current_observation']['wind_dir']
            self.wind_degrees =  parsed_json['current_observation']['wind_degrees']
            self.wind_kph =      parsed_json['current_observation']['wind_kph']
            self.wind_gust_kph = parsed_json['current_observation']['wind_gust_kph']




