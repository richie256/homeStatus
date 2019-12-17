# OutsideTemp service

import pyecobee

from flask import Flask
from flask import Response
from flask import jsonify
from flask import request

import requests
import os
import json
from datetime import datetime
import calendar
import pytz

from requests.exceptions import RequestException;


from flask_restful import Resource, Api

import logging
import inspect

from dateutil import tz


# create logger with 'ecobee_application'
logger = logging.getLogger('ecobee_application')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('ecobee.log')
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

def config_from_file(filename, config=None):
    ''' Small configuration file management function'''
    if config:
        # We're writing configuration
        try:
            with open(filename, 'w') as fdesc:
                fdesc.write(json.dumps(config))
        except IOError as error:
            logger.exception(error)
            return False
        return True
    else:
        # We're reading config
        if os.path.isfile(filename):
            try:
                with open(filename, 'r') as fdesc:
                    return json.loads(fdesc.read())
            except IOError as error:
                return False
        else:
            return {}


class Ecobee(object):
    ''' Class for storing Ecobee Thermostats and Sensors '''
    CONST_JSON = 'JSON'
    CONST_INFLUX = 'influx'
    CONST_DROPWIZARD = 'dropwizard'

    def __init__(self, config_filename=None, api_key=None, config=None):
        self.thermostats = list()
        self.pin = None
        self.authenticated = False
        self.include_occupancy = True

        if config is None:
            self.file_based_config = True
            if config_filename is None:
                if api_key is None:
                    logger.error("Error. No API Key was supplied.")
                    return
                jsonconfig = {"API_KEY": api_key}
                config_filename = 'ecobee.conf'
                config_from_file(config_filename, jsonconfig)
            config = config_from_file(config_filename)
        else:
            self.file_based_config = False
        self.api_key = config['API_KEY']
        self.config_filename = config_filename

        if 'ACCESS_TOKEN' in config:
            self.access_token = config['ACCESS_TOKEN']
        else:
            self.access_token = ''

        if 'AUTHORIZATION_CODE' in config:
            self.authorization_code = config['AUTHORIZATION_CODE']
        else:
            self.authorization_code = ''

        if 'REFRESH_TOKEN' in config:
            self.refresh_token = config['REFRESH_TOKEN']
        else:
            # We don't want to mess up with authorisation in progress.
            if 'AUTHORIZATION_CODE' not in config:
                self.refresh_token = ''
                self.request_pin()
            return

        self.update()

        self.opt_format = request.args.get("format")
        if self.opt_format is None:
        	self.opt_format = self.CONST_JSON


    def request_pin(self):
        ''' Method to request a PIN from ecobee for authorization '''
        url = 'https://api.ecobee.com/authorize'
        params = {'response_type': 'ecobeePin',
                  'client_id': self.api_key, 'scope': 'smartWrite'}
        try:
            request = requests.get(url, params=params)
        except RequestException:
            logger.warn("Error connecting to Ecobee.  Possible connectivity outage."
                        "Could not request pin.")
            return
        try:
            self.authorization_code = request.json()['code']
        except:
            logger.error('Error calling request_pin.\nRequest output:\n' + json.dumps(request.json(), indent = 4) + '\nRequest params:\n' + json.dumps(params, indent = 4) + '\nRequest URL: ' + url)

        self.pin = request.json()['ecobeePin']
        logger.error('Please authorize your ecobee developer app with PIN code '
              + self.pin + '\nGoto https://www.ecobee.com/consumerportal'
              '/index.html, click\nMy Apps, Add application, Enter Pin'
              ' and click Authorize.\nAfter authorizing, call request_'
              'tokens() method.')
        # new:
        self.write_tokens_to_file()

    def request_tokens(self):
        ''' Method to request API tokens from ecobee '''
        url = 'https://api.ecobee.com/token'
        params = {'grant_type': 'ecobeePin', 'code': self.authorization_code,
                  'client_id': self.api_key}
        try:
            request = requests.post(url, params=params)
        except RequestException:
            logger.warn("Error connecting to Ecobee.  Possible connectivity outage."
                        "Could not request token.")
            return
        if request.status_code == requests.codes.ok:
            self.access_token = request.json()['access_token']
            self.refresh_token = request.json()['refresh_token']
            self.write_tokens_to_file()
            self.pin = None
        else:
            logger.warn('Error while requesting tokens from ecobee.com.'
                  ' Status code: ' + str(request.status_code) + '\n' +
                  'request: ' + json.dumps(request.json(), indent = 4) + '\n' +
                  'params: ' +  json.dumps(params, indent = 4))
            return

    def refresh_tokens(self):
        ''' Method to refresh API tokens from ecobee '''
        url = 'https://api.ecobee.com/token'
        params = {'grant_type': 'refresh_token',
                  'refresh_token': self.refresh_token,
                  'client_id': self.api_key}
        request = requests.post(url, params=params)
        if request.status_code == requests.codes.ok:
            self.access_token = request.json()['access_token']
            self.refresh_token = request.json()['refresh_token']
            self.write_tokens_to_file()
            return True
        else:
            self.request_pin()


    ''' DO NOT poll at an interval quicker than once every 3 minutes, which is the shortest interval at which data might change. '''
    def getThermostatSummary(self):
        url = 'https://api.ecobee.com/1/thermostat'
        header = {'Content-Type': 'application/json;charset=UTF-8',
                  'Authorization': 'Bearer ' + self.access_token}
        params = {'json': ('{"selection":{"selectionType":"registered",'
                            '"selectionMatch":"",'
                            '"includeEquipmentStatus":"true"}}')}
        try:
            request = requests.get(url, headers=header, params=params)
        except RequestException:
            logger.warn("Error connecting to Ecobee.  Possible connectivity outage.")
            return None
        if request.status_code == requests.codes.ok:
            self.authenticated = True
            self.thermostats = request.json()['thermostatList']
            # logger.info("Autheticated. there is returned value: " + json.dumps(self.thermostats[0], indent = 4))
            return self.thermostats


        ''' "selectionType":"registered","selectionMatch":"","includeEquipmentStatus":true '''


    def get_thermostats(self):
        ''' Set self.thermostats to a json list of thermostats from ecobee '''
        url = 'https://api.ecobee.com/1/thermostat'
        header = {'Content-Type': 'application/json;charset=UTF-8',
                  'Authorization': 'Bearer ' + self.access_token}
        params = {'json': ('{"selection":{"selectionType":"registered",'
                            '"includeRuntime":"true",'
                            '"includeExtendedRuntime":"true",'
                            '"includeSensors":"true",'
                            '"includeProgram":"true",'
                            '"includeEquipmentStatus":"true",'
                            '"includeEvents":"true",'
                            '"includeWeather":"true",'
                            '"includeSettings":"true"}}')}
        try:
            request = requests.get(url, headers=header, params=params)
        except RequestException:
            logger.warn("Error connecting to Ecobee.  Possible connectivity outage.")
            return None
        if request.status_code == requests.codes.ok:
            self.authenticated = True
            self.thermostats = request.json()['thermostatList']
            # logger.info("Autheticated. there is returned value: " + json.dumps(self.thermostats[0], indent = 4))
            return self.thermostats
        else:
            self.authenticated = False
            logger.info("Error connecting to Ecobee while attempting to get "
                  "thermostat data.  Refreshing tokens and trying again.")
            if self.refresh_tokens():
                return self.get_thermostats()
            else:
                return None

    def get_thermostat(self, index):
        ''' Return a single thermostat based on index '''
        return self.thermostats[index]

    def get_remote_sensors(self, index):
        ''' Return remote sensors based on index '''
        return self.thermostats[index]['remoteSensors']

    def write_tokens_to_file(self):
        ''' Write api tokens to a file '''
        config = dict()
        try:
            if self.api_key != '':
                config['API_KEY'] = self.api_key
        except:
            pass
        try:
            if self.access_token != '':
                config['ACCESS_TOKEN'] = self.access_token
        except:
            pass
        try:
            if self.refresh_token != '':
                config['REFRESH_TOKEN'] = self.refresh_token
        except:
            pass
        try:
            if self.authorization_code != '':
                config['AUTHORIZATION_CODE'] = self.authorization_code
        except:
            pass
        if self.file_based_config:
            config_from_file(self.config_filename, config)
        else:
            self.config = config

    def update(self):
        ''' Get new thermostat data from ecobee '''
        self.get_thermostats()

    def make_request(self, body, log_msg_action):
        url = 'https://api.ecobee.com/1/thermostat'
        header = {'Content-Type': 'application/json;charset=UTF-8',
                  'Authorization': 'Bearer ' + self.access_token}
        params = {'format': 'json'}
        try:
            request = requests.post(url, headers=header, params=params, data=json.dumps(body))
        except RequestException:
            logger.warn("Error connecting to Ecobee.  Possible connectivity outage.")
            return None
        if request.status_code == requests.codes.ok:
            return request
        else:
            logger.info("Error connecting to Ecobee while attempting to %s.  "
                        "Refreshing tokens and trying again.", log_msg_action)
            if self.refresh_tokens():
                return self.make_request(json.dumps(body), log_msg_action)
            else:
                return None

    def set_hvac_mode(self, index, hvac_mode):
        ''' possible hvac modes are auto, auxHeatOnly, cool, heat, off '''
        body = {"selection": {"selectionType": "thermostats",
                              "selectionMatch": self.thermostats[index]['identifier']},
                              "thermostat": {
                                  "settings": {
                                      "hvacMode": hvac_mode
                                  }
                              }}
        log_msg_action = "set HVAC mode"
        return self.make_request(body, log_msg_action)

    def set_fan_min_on_time(self, index, fan_min_on_time):
        ''' The minimum time, in minutes, to run the fan each hour. Value from 1 to 60 '''
        body = {"selection": {"selectionType": "thermostats",
                        "selectionMatch": self.thermostats[index]['identifier']},
                        "thermostat": {
                            "settings": {
                                "fanMinOnTime": fan_min_on_time
                            }
                        }}
        log_msg_action = "set fan minimum on time."
        return self.make_request(body, log_msg_action)

    def set_fan_mode(self, index, fan_mode, cool_temp, heat_temp, hold_type="nextTransition"):
        ''' Set fan mode. Values: auto, minontime, on '''
        body = {"selection": {
                    "selectionType": "thermostats",
                    "selectionMatch": self.thermostats[index]['identifier']},
                "functions": [{"type": "setHold", "params": {
                    "holyType": hold_type,
                    "coolHoldTemp": cool_temp * 10,
                    "heatHoldTemp": heat_temp * 10,
                    "fan": fan_mode
                }}]}
        log_msg_action = "set fan mode"
        return self.make_request(body, log_msg_action)

    def set_hold_temp(self, index, cool_temp, heat_temp,
                      hold_type="nextTransition"):
        ''' Set a hold '''
        body = {"selection": {
                    "selectionType": "thermostats",
                    "selectionMatch": self.thermostats[index]['identifier']},
                "functions": [{"type": "setHold", "params": {
                    "holyType": hold_type,
                    "coolHoldTemp": cool_temp * 10,
                    "heatHoldTemp": heat_temp * 10
                }}]}
        log_msg_action = "set hold temp"
        return self.make_request(body, log_msg_action)

    def set_climate_hold(self, index, climate, hold_type="nextTransition"):
        ''' Set a climate hold - ie away, home, sleep '''
        body = {"selection": {
                    "selectionType": "thermostats",
                    "selectionMatch": self.thermostats[index]['identifier']},
                "functions": [{"type": "setHold", "params": {
                    "holyType": hold_type,
                    "holdClimateRef": climate
                }}]}
        log_msg_action = "set climate hold"
        return self.make_request(body, log_msg_action)

    def delete_vacation(self, index, vacation):
        ''' Delete the vacation with name vacation '''
        body = {"selection": {
                    "selectionType": "thermostats",
                    "selectionMatch": self.thermostats[index]['identifier']},
                "functions": [{"type": "deleteVacation", "params": {
                    "name": vacation
                }}]}

        log_msg_action = "delete a vacation"
        return self.make_request(body, log_msg_action)

    def resume_program(self, index, resume_all=False):
        ''' Resume currently scheduled program '''
        body = {"selection": {
                    "selectionType": "thermostats",
                    "selectionMatch": self.thermostats[index]['identifier']},
                "functions": [{"type": "resumeProgram", "params": {
                    "resumeAll": resume_all
                }}]}

        log_msg_action = "resume program"
        return self.make_request(body, log_msg_action)

    def send_message(self, index, message="Hello from python-ecobee!"):
        ''' Send a message to the thermostat '''
        body = {"selection": {
                    "selectionType": "thermostats",
                    "selectionMatch": self.thermostats[index]['identifier']},
                "functions": [{"type": "sendMessage", "params": {
                    "text": message[0:500]
                }}]}

        log_msg_action = "send message"
        return self.make_request(body, log_msg_action)

    def set_humidity(self, index, humidity):
        ''' Set humidity level'''
        body = {"selection": {"selectionType": "thermostats",
                              "selectionMatch": self.thermostats[index]['identifier']},
                              "thermostat": {
                                  "settings": {
                                      "humidity": int(humidity)
                                  }
                              }}

        log_msg_action = "set humidity level"
        return self.make_request(body, log_msg_action)


    def getExtendedRuntime(self, index):

        # return self.thermostats[index]['extendedRuntime'];
        # return self.thermostats[index];

        # get the serial number for this thermostat (as a string)
        stat_id = str(self.thermostats[index]['identifier']) + '_'

        # extendedRuntimeList = self.thermostat['extendedRuntime']

        # return jsonify(self.thermostat)

        # extendedRuntimeList = self.thermostat.get('extendedRuntime')
        # extendedRuntimeList = self.thermostat['extendedRuntime']

        # self.thermostats[index]['remoteSensors']


        # reference: https://git.ahfc.us/energy/bmon/blob/e8a13fc1487a7209419bac45c81b27051c57481c/bmsapp/periodic_scripts/ecobee.py

        # get the UNIX timestamps for the three readings present in the
        # ExtendedRuntime object.  The three readings are for three 5-minute
        # intervals.  The timestamp of the last interval is given as a string.
        # It marks the beginning of the interval, so I shift it forward to the middle
        # of the interval here.


        # The UTC timestamp of the last value read. This timestamp is updated at a 15 min
        # interval by the thermostat. For the 1st value, it is timestamp - 10 mins, for
        # the 2nd value it is timestamp - 5 mins. Consider day boundaries being straddled
        # when using these values.

        # Influx timestamp:
        # The timestamp for your data point in nanosecond-precision Unix time. The timestamp is optional in Line Protocol.
        # If you do not specify a timestamp for your data point InfluxDB uses the server’s local nanosecond timestamp in UTC.

        last_ts_str = self.thermostats[index]['extendedRuntime']['lastReadingTimestamp']
        # last_ts = self.ts_from_datestr(last_ts_str)
        last_ts = self.ts_utc_from_datestr(last_ts_str)

        tstamps = [last_ts - 600, last_ts - 300, last_ts]

        # get temperature values
        vals = self.thermostats[index]['extendedRuntime']['actualTemperature']
        vals = [round(self.toCelsius(val / 10.0),2) for val in vals]   # they are expressed in tenths, so convert
        actualTemperature = vals

        # get Humidity values
        vals = self.thermostats[index]['extendedRuntime']['actualHumidity']
        actualHumidity = vals

        # get heating setpoints
        vals = self.thermostats[index]['extendedRuntime']['desiredHeat']
        vals = [round(self.toCelsius(val / 10.0),2) for val in vals]  # they are expressed in tenths, so convert
        desiredHeat = vals

        # get cooling setpoints
        vals = self.thermostats[index]['extendedRuntime']['desiredCool']
        vals = [round(self.toCelsius(val / 10.0),2) for val in vals]  # they are expressed in tenths, so convert
        desiredCool = vals

        # get humidity setpoints
        # The last three 5 minute desired humidity readings.
        vals = self.thermostats[index]['extendedRuntime']['desiredHumidity']
        # vals = [val / 10.0 for val in vals]  # they are expressed in tenths, so convert
        desiredHumidity = vals

        # get de-humidity setpoints
        # The last three 5 minute desired de-humidification readings.
        vals = self.thermostats[index]['extendedRuntime']['desiredDehumidity']
        # vals = [val / 10.0 for val in vals]  # they are expressed in tenths, so convert
        desiredDehumidity = vals


        # get HVAC Runtime values in seconds (0-300 seconds) of heat pump stage 1 runtime values
        vals = self.thermostats[index]['extendedRuntime']['heatPump1']
        # convert to fractional runtime from seconds / 5 minute interval
        vals = [val / 300.0 for val in vals]
        heatPump1 = vals

        # # get HVAC Runtime values in seconds (0-300 seconds) of heat pump stage 2 runtime values
        # vals = self.thermostats[index]['extendedRuntime']['heatPump2']
        # # convert to fractional runtime from seconds / 5 minute interval
        # vals = [val / 300.0 for val in vals]

        # get HVAC Runtime values in seconds (0-300 seconds) of auxiliary heat stage 1 values
        vals = self.thermostats[index]['extendedRuntime']['auxHeat1']
        # convert to fractional runtime from seconds / 5 minute interval
        vals = [val / 300.0 for val in vals]
        auxHeat1 = vals

        # Runtime values (0-300 seconds) of cooling stage 1
        vals = self.thermostats[index]['extendedRuntime']['fan']
        # convert to fractional runtime from seconds / 5 minute interval
        vals = [val / 300.0 for val in vals]
        fan = vals

        # # get HVAC Runtime values in seconds (0-300 seconds) of auxiliary heat stage 2 values
        # vals = self.thermostats[index]['extendedRuntime']['auxHeat2']
        # # convert to fractional runtime from seconds / 5 minute interval
        # vals = [val / 300.0 for val in vals]

        # # get HVAC Runtime values in seconds (0-300 seconds) of auxiliary heat stage 3 values
        # vals = self.thermostats[index]['extendedRuntime']['auxHeat3']
        # # convert to fractional runtime from seconds / 5 minute interval
        # vals = [val / 300.0 for val in vals]

        # Runtime values (0-300 seconds) of cooling stage 1
        vals = self.thermostats[index]['extendedRuntime']['cool1']
        # convert to fractional runtime from seconds / 5 minute interval
        vals = [val / 300.0 for val in vals]
        cool1 = vals

        # # Runtime values (0-300 seconds) of cooling stage 2
        # vals = self.thermostats[index]['extendedRuntime']['cool2']
        # # convert to fractional runtime from seconds / 5 minute interval
        # vals = [val / 300.0 for val in vals]

        returnValue = ''

        for x in range(0, 3):
            returnValue += 'apidata,source=ecobee,location=Brossard,opt_format=' + self.opt_format + ' ' + 'actualTemperature=' + str(actualTemperature[x]) + ',actualHumidity=' + str(actualHumidity[x]) + ',desiredHeat=' + str(desiredHeat[x]) + ',desiredCool=' + str(desiredCool[x]) + ',desiredHumidity=' + str(desiredHumidity[x]) + ',desiredDehumidity=' + str(desiredDehumidity[x]) + ',heatPump1=' + str(heatPump1[x]) + ',auxHeat1=' + str(auxHeat1[x]) + ',cool1=' + str(cool1[x]) + ',fan=' + str(fan[x]) + ' ' + str(int(tstamps[x])) + '000000000' + '\n'

        return Response(returnValue, mimetype='text/xml')

        """
        lastReadingTimestamp
        runtimeDate
        runtimeInterval
        actualTemperature
        actualHumidity
        desiredHeat
        desiredCool
        desiredHumidity
        desiredDehumidity
        dmOffset
        hvacMode
        heatPump1
        heatPump2
        auxHeat1
        auxHeat2
        auxHeat3
        cool1
        cool2
        fan
        humidifier
        dehumidifier
        economizer
        ventilator
        currentElectricityBill
        projectedElectricityBill
        """

    def getRuntimeAndRemoteSensors(self, index):


        stat_id = str(self.thermostats[index]['identifier']) + '_'

        # Loop through ther Remote Sensors collection, extracting data available there.
        # Use the lastStatusModified timestamp as the indicator of the time of these
        # readings.

        remoteSensors = self.thermostats[index]['remoteSensors']

        # Extract runtime and remoteSensors

        sensor_ts_str = self.thermostats[index]['runtime']['lastStatusModified']
        # sensor_ts = self.ts_from_datestr(sensor_ts_str)
        sensor_ts = self.ts_utc_from_datestr(sensor_ts_str)

        sensors = []

        # The current HVAC mode the thermostat is in. Values: auto, auxHeatOnly, cool, heat, off.
        self.hvacMode = self.thermostats[index]['settings']['hvacMode']


        val = self.thermostats[index]['runtime']['desiredHeat']
        self.desiredHeat = round(self.toCelsius(val / 10.0),2)

        val = self.thermostats[index]['runtime']['desiredCool']
        self.desiredCool = round(self.toCelsius(val / 10.0),2)


        if self.hvacMode == 'cool':
            self.desiredTemperature = self.desiredCool

        elif self.hvacMode == 'heat' or self.hvacMode == 'auxHeatOnly':
            self.desiredTemperature = self.desiredHeat

        else:
            self.desiredTemperature = 0


        # for sensor in stat['remoteSensors']:
        for sensor in self.thermostats[index]['remoteSensors']:
            # variables determining whether we will store particular types of readings
            # for this sensor.

            use_temp = False
            use_occupancy = False
            sens_id = ''        # the ID prefix to use for this sensor
            if sensor['type'] == 'ecobee3_remote_sensor':
                use_temp = True
                use_occupancy = self.include_occupancy
                sens_id = '%s%s' % (stat_id, str(sensor['code']))
                name = sensor['name']

            elif sensor['type'] == 'thermostat':
                # use_temp = False    # we already gathered temperature for the main thermostat
                use_occupancy = self.include_occupancy
                sens_id = stat_id

            # loop through reading types of this sensor and store the requested ones
            for capability in sensor['capability']:
                # if capability['type'] == 'temperature' and use_temp:
                if capability['type'] == 'temperature':

                    # readings.append((sensor_ts, sens_id + 'temp', float(capability['value'])/10.0))
                    if sensor['type'] == 'ecobee3_remote_sensor':
                        tempval = round(self.toCelsius(int(capability['value']) / 10.0),2)

                        # remote_temp = float(capability['value'])/10.0
                    elif sensor['type'] == 'thermostat':
                        pass
                elif capability['type'] == 'occupancy' and use_occupancy:
                    occupval = 1 if capability['value'] == 'true' else 0
                    # readings.append((sensor_ts, sens_id + 'occup', val))
                    # if sensor['type'] == 'ecobee3_remote_sensor':
                        # occupval = val
                    # elif sensor['type'] == 'thermostat':
                        # occupval = val

            if sensor['type'] == 'ecobee3_remote_sensor':
                sensors.append([sensor_ts, sens_id, tempval, name, occupval])
            # we already gathered temperature for the main thermostat
            elif sensor['type'] == 'thermostat':
                thermostat_occup = occupval


        # Remote Sensor
        returnValue = ''
        for sensor in sensors:
            # sensor[0] # TS
            # sensor[1] # send_id
            # sensor[2] # temp
            # sensor[3] # name
            # sensor[4] # occupval
            returnValue += 'apidata,source=ecobee,location=Brossard,opt_format=' + self.opt_format + ',type=remotesensor,sensor_id=' + sensor[1] + ',mode=realtime,sensor_name=' + sensor[3] + ' ' + 'temperature=' + str(sensor[2]) + ',occupancy=' + str(sensor[4]) + ' ' + str(int(sensor[0])) + '000000000' + '\n'

        # Thermostat
        returnValue += 'apidata,source=ecobee,location=Brossard,opt_format=' + self.opt_format + ',type=thermostat,mode=realtime ' + 'occupancy=' + str(thermostat_occup) + ',hvacMode=' + str(self.hvacModeToInt(self.hvacMode)) + ',desiredHeat=' + str(self.desiredHeat) + ',desiredCool=' + str(self.desiredCool) + ',desiredTemperature=' + str(self.desiredTemperature) + ' ' + str(int(sensor_ts)) + '000000000' + '\n'


        return Response(returnValue, mimetype='text/xml')




    @staticmethod
    def ts_utc_from_datestr(utc_date_str):
        utc = datetime.strptime(utc_date_str, '%Y-%m-%d %H:%M:%S')

        pst = pytz.timezone('Etc/UTC')
        utc = pst.localize(utc)

        # return calendar.timegm(dt.utctimetuple())
        return utc.timestamp()



    @staticmethod
    def ts_from_datestr(utc_date_str):
        """Retunns a UNIX timestamp in seconds from a string in the format
        YYYY-MM-DD HH:MM:SS, where the string is a UTC date/time.
        """

        # UTC timestamp
        # Auto-detect zones:
        # from_zone = tz.tzutc()
        # to_zone = tz.tzlocal()
        from_zone = tz.tzlocal()
        to_zone = tz.tzutc()

        # utc = datetime.strptime('2011-01-21 02:37:21', '%Y-%m-%d %H:%M:%S')
        utc = datetime.strptime(utc_date_str, '%Y-%m-%d %H:%M:%S')
        # dt = datetime.strptime(utc_date_str, '%Y-%m-%d %H:%M:%S')

        # Tell the datetime object that it's in UTC time zone since 
        # datetime objects are 'naive' by default
        utc = utc.replace(tzinfo=from_zone)

        # Convert time zone
        local_dt = utc.astimezone(to_zone)

        # return calendar.timegm(dt.timetuple())
        return calendar.timegm(local_dt.timetuple())



    # Possible values: auto, auxHeatOnly, cool, heat, off.
    @staticmethod
    def hvacModeToInt(hvacMode):
        if hvacMode == 'auto':
            return 1
        elif hvacMode == 'auxHeatOnly':
            return 2
        elif hvacMode == 'cool':
            return 3
        elif hvacMode == 'heat':
            return 4
        elif hvacMode == 'off':
            return 5
        return -1

    @staticmethod
    def toFarenheit(celsius):
        return (9.0/5.0) * celsius + 32

    @staticmethod
    def toCelsius(farenheit):
        return (farenheit - 32) * (5.0 / 9.0)



class ExtendedRuntimeClass(Resource):
    def get(self):

        # return ecobeeThermostat.getExtendedRuntime
        thermostat = Ecobee('ecobee.conf')

        return thermostat.getExtendedRuntime(0)
        # return jsonify(thermostat.get_thermostat(0))


class RuntimeClass(Resource):
    def get(self):
        thermostat = Ecobee('ecobee.conf')

        return thermostat.getRuntimeAndRemoteSensors(0)


class EcobeeThermostatRequestTokens(Resource):
    def get(self):
        thermostat = Ecobee('ecobee.conf')
        thermostat.request_tokens()

class EcobeeThermostatRequestPin(Resource):
    def get(self):
        thermostat = Ecobee('ecobee.conf')
        thermostat.request_pin()

# thermostat = ecobee.get_thermostats()

# blbfbotAxTwKs7jBYSQIVEAovlrkJZeC
# http://localhost:5002/thermostat/ecobee/resource/extended-runtime?format=influx

# api.add_resource(OutsideTemp, '/conditions/<string:location>')
# api.add_resource(ecobeeThermostat, '/thermostat/ecobee/resource/extended-runtime')
api.add_resource(ExtendedRuntimeClass, '/thermostat/ecobee/resource/extended-runtime')
api.add_resource(RuntimeClass, '/thermostat/ecobee/resource/runtime')

api.add_resource(EcobeeThermostatRequestTokens, '/thermostat/ecobee/token/request')
api.add_resource(EcobeeThermostatRequestPin, '/thermostat/ecobee/pin/request')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
