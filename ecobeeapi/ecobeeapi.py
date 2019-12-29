# Ecobee service

from pyecobee import Ecobee
from pyecobee.errors import ExpiredTokenError
from pyecobee.const import ECOBEE_ENDPOINT_THERMOSTAT

from flask import Flask, abort, Response, jsonify, request

import requests
import json
import time
import redis
from redis.exceptions import LockError

from requests.exceptions import RequestException

from io import StringIO
import csv

from flask_restful import Resource, Api

import logging

from const import (
    JSON,
    INFLUX,
    ECOBEE_DATETIME_FORMAT,
)

from util import toFarenheit, toCelsius, ts_utc_from_datestr, hvacModeToInt

# create logger with 'ecobee_application'
logger = logging.getLogger('pyecobee')

logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('ecobee.log')
fh.setLevel(logging.ERROR)
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

class EcobeeEnhanced(Ecobee):

    def __init__(self, config_filename: str = None, config: dict = None):
        """Override the __init___ and set the request format arg."""
        self.opt_format = request.args.get("format")
        if self.opt_format is None:
            self.opt_format = JSON

        if config_filename is None:
            Ecobee.__init__(self,config=config)
        else:
            Ecobee.__init__(self,config_filename=config_filename)


    def get_thermostats(self) -> bool:
        """Gets a json-list of thermostats from ecobee and caches in self.thermostats."""
        param_string = {
            "selection": {
                "selectionType": "registered",
                "includeRuntime": "true",
                "includeExtendedRuntime": "true",
                "includeSensors": "true",
                "includeProgram": "true",
                "includeEquipmentStatus": "true",
                "includeEvents": "true",
                "includeWeather": "true",
                "includeSettings": "true",
            }
        }
        params = {"json": json.dumps(param_string)}
        log_msg_action = "get thermostats"

        response = self._request(
            "GET", ECOBEE_ENDPOINT_THERMOSTAT, log_msg_action, params=params
        )

        try:
            self.thermostats = response["thermostatList"]
            return True
        except (KeyError, TypeError):
            return False

    def set_api_key(self, api_key):
        '''Set a new Api Key and write the config.'''
        self.api_key = api_key

        return self._write_config();

    def getExtendedRuntime(self, index):
        '''Class to get the Extended Runtime.'''

        # get the serial number for this thermostat (as a string)
        stat_id = str(self.thermostats[index]['identifier']) + '_'

        # extendedRuntimeList = self.thermostat.get('extendedRuntime')
        # extendedRuntimeList = self.thermostat['extendedRuntime']

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
        # If you do not specify a timestamp for your data point InfluxDB uses the server's local nanosecond timestamp in UTC.

        last_ts_str = self.thermostats[index]['extendedRuntime']['lastReadingTimestamp']
        last_ts = ts_utc_from_datestr(last_ts_str)

        tstamps = [last_ts - 600, last_ts - 300, last_ts]

        # get temperature values
        vals = self.thermostats[index]['extendedRuntime']['actualTemperature']
        actualTemperature = [round(toCelsius(val / 10.0),2) for val in vals]   # they are expressed in tenths, so convert

        # get Humidity values
        actualHumidity = self.thermostats[index]['extendedRuntime']['actualHumidity']

        # get heating setpoints
        vals = self.thermostats[index]['extendedRuntime']['desiredHeat']
        desiredHeat = [round(toCelsius(val / 10.0),2) for val in vals]  # they are expressed in tenths, so convert

        # get cooling setpoints
        vals = self.thermostats[index]['extendedRuntime']['desiredCool']
        desiredCool = [round(toCelsius(val / 10.0),2) for val in vals]  # they are expressed in tenths, so convert

        # get humidity setpoints
        # The last three 5 minute desired humidity readings.
        desiredHumidity = self.thermostats[index]['extendedRuntime']['desiredHumidity']
        # vals = [val / 10.0 for val in vals]  # they are expressed in tenths, so convert

        # get de-humidity setpoints
        # The last three 5 minute desired de-humidification readings.
        desiredDehumidity = self.thermostats[index]['extendedRuntime']['desiredDehumidity']
        # vals = [val / 10.0 for val in vals]  # they are expressed in tenths, so convert


        # get HVAC Runtime values in seconds (0-300 seconds) of heat pump stage 1 runtime values
        vals = self.thermostats[index]['extendedRuntime']['heatPump1']
        # convert to fractional runtime from seconds / 5 minute interval
        heatPump1 = [val / 300.0 for val in vals]

        # # get HVAC Runtime values in seconds (0-300 seconds) of heat pump stage 2 runtime values
        # vals = self.thermostats[index]['extendedRuntime']['heatPump2']
        # # convert to fractional runtime from seconds / 5 minute interval
        # vals = [val / 300.0 for val in vals]

        # get HVAC Runtime values in seconds (0-300 seconds) of auxiliary heat stage 1 values
        vals = self.thermostats[index]['extendedRuntime']['auxHeat1']
        # convert to fractional runtime from seconds / 5 minute interval
        auxHeat1 = [val / 300.0 for val in vals]

        # Runtime values (0-300 seconds) of cooling stage 1
        vals = self.thermostats[index]['extendedRuntime']['fan']
        # convert to fractional runtime from seconds / 5 minute interval
        fan = [val / 300.0 for val in vals]

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
        cool1 = [val / 300.0 for val in vals]

        # # Runtime values (0-300 seconds) of cooling stage 2
        # vals = self.thermostats[index]['extendedRuntime']['cool2']
        # # convert to fractional runtime from seconds / 5 minute interval
        # vals = [val / 300.0 for val in vals]

        returnValue = ''

        for x in range(0, 3):
            influxdb_measurement = 'apidata'
            influxdb_tag_set = 'source=ecobee,location=Brossard,opt_format=' + self.opt_format
            influxdb_field_set = 'actualTemperature=' + str(actualTemperature[x]) + ',actualHumidity=' + str(actualHumidity[x]) + ',desiredHeat=' + str(desiredHeat[x]) + ',desiredCool=' + str(desiredCool[x]) + ',desiredHumidity=' + str(desiredHumidity[x]) + ',desiredDehumidity=' + str(desiredDehumidity[x]) + ',heatPump1=' + str(heatPump1[x]) + ',auxHeat1=' + str(auxHeat1[x]) + ',cool1=' + str(cool1[x]) + ',fan=' + str(fan[x])
            influxdb_timestamp = str(int(tstamps[x])) + '000000000' 

            returnValue += ( influxdb_measurement + ',' + influxdb_tag_set + ' ' + influxdb_field_set + ' ' + influxdb_timestamp + '\n' )

        return Response(returnValue, mimetype='text/xml')



    def getRunningEquipments(self, index):
        '''Class to retrieve the running equipments.'''

        # Requires runtime, settings and equipmentStatus.

        equipmentList = ['heatPump', 'heatPump2', 'heatPump3', 'compCool1', 'compCool2', 'auxHeat1', 'auxHeat2', 'auxHeat3', 'fan', 'humidifier', 'dehumidifier', 'ventilator', 'economizer', 'compHotWater', 'auxHotWater']

        # Initialise the list of possible running Equipments as 0.
        runningEquipments = dict()

        for i in equipmentList:
            runningEquipments[i] = '0'

        sensor_ts_str = self.thermostats[index]['runtime']['lastStatusModified']
        # sensor_ts_str = '2019-12-26 02:32:04'
        sensor_ts = ts_utc_from_datestr(sensor_ts_str)

        equipmentStatus = self.thermostats[index]['equipmentStatus']
        # equipmentStatus = 'fan,heatPump'

        if (equipmentStatus is not None) and (equipmentStatus != ''):
            file_like_obj = StringIO(equipmentStatus)
            csv_reader = csv.reader(file_like_obj, delimiter=',')
            for row in csv_reader:
                rowSize = len(row)

                for x in range(0, len(row)):
                    runningEquipments.update({row[x]:'1'})

                break

        returnValue = None

        if len(runningEquipments) > 0:

            queue = StringIO()

            # We put them together in a single row (csv-style) without line terminator
            writer = csv.writer(queue, lineterminator='')

            #Concat the key Value
            concat = []
            for k,v in runningEquipments.items():
                concat.append(k + "=" + str(v))

            writer.writerow(concat)

            influxdb_measurement = 'running_equipments'
            influxdb_tag_set = 'source=ecobee,location=Brossard,opt_format=' + self.opt_format
            influxdb_field_set = queue.getvalue()
            influxdb_timestamp = str(int(sensor_ts)) + '000000000'

            returnValue = influxdb_measurement + ',' + influxdb_tag_set + ' ' + influxdb_field_set + ' ' + influxdb_timestamp + '\n'

        return Response(returnValue, mimetype='text/xml')


    def getRuntimeAndRemoteSensors(self, index):
        '''Class to extract the Runtime and Remote Sensors data.'''

        # occupval = 0

        stat_id = str(self.thermostats[index]['identifier']) + '_'

        # Loop through ther Remote Sensors collection, extracting data available there.
        # Use the lastStatusModified timestamp as the indicator of the time of these
        # readings.

        remoteSensors = self.thermostats[index]['remoteSensors']

        # Extract runtime and remoteSensors

        sensor_ts_str = self.thermostats[index]['runtime']['lastStatusModified']
        sensor_ts = ts_utc_from_datestr(sensor_ts_str)

        sensors = []

        # The current HVAC mode the thermostat is in. Values: auto, auxHeatOnly, cool, heat, off.
        self.hvacMode = self.thermostats[index]['settings']['hvacMode']


        val = self.thermostats[index]['runtime']['desiredHeat']
        self.desiredHeat = round(toCelsius(val / 10.0),2)

        val = self.thermostats[index]['runtime']['desiredCool']
        self.desiredCool = round(toCelsius(val / 10.0),2)

        # thermostat_actualTemperature = round(toCelsius(int(self.thermostats[index]['runtime']['actualTemperature']) / 10.0),2)
        # thermostat_actualHumidity = self.thermostats[index]['runtime']['actualHumidity']

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

            # use_temp = False
            # use_occupancy = False
            sens_id = ''        # the ID prefix to use for this sensor
            if sensor['type'] == 'ecobee3_remote_sensor':
                use_temp = True
                sens_id = '%s%s' % (stat_id, str(sensor['code']))
                name = sensor['name']

            elif sensor['type'] == 'thermostat':
                # use_temp = False    # we already gathered temperature for the main thermostat
                sens_id = stat_id

            # loop through reading types of this sensor and store the requested ones
            for capability in sensor['capability']:
                # if capability['type'] == 'temperature' and use_temp:
                if capability['type'] == 'temperature':

                    # readings.append((sensor_ts, sens_id + 'temp', float(capability['value'])/10.0))
                    if sensor['type'] == 'ecobee3_remote_sensor':
                        if capability['value'] == 'unknown':
                            tempval = -999
                        else:
                            tempval = round(toCelsius(int(capability['value']) / 10.0),2)

                        # remote_temp = float(capability['value'])/10.0
                    elif sensor['type'] == 'thermostat':
                        pass
                elif capability['type'] == 'occupancy':
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
            if sensor[2] != -999:
                influxdb_measurement = 'apidata'
                influxdb_tag_set = 'source=ecobee,location=Brossard,opt_format=' + self.opt_format + ',type=remotesensor,sensor_id=' + sensor[1] + ',mode=realtime,sensor_name=' + sensor[3].replace(' ', '\ ')
                influxdb_field_set = 'temperature=' + str(sensor[2]) + ',occupancy=' + str(sensor[4])
                influxdb_timestamp = str(int(sensor[0])) + '000000000'

                returnValue += ( influxdb_measurement + ',' + influxdb_tag_set + ' ' + influxdb_field_set + ' ' + influxdb_timestamp + '\n' )

        # Thermostat
        influxdb_measurement = 'apidata'
        influxdb_tag_set = 'source=ecobee,location=Brossard,opt_format=' + self.opt_format + ',type=thermostat,mode=realtime'
        influxdb_field_set = 'occupancy=' + str(thermostat_occup) + ',hvacMode=' + str(hvacModeToInt(self.hvacMode)) + ',desiredHeat=' + str(self.desiredHeat) + ',desiredCool=' + str(self.desiredCool) + ',desiredTemperature=' + str(self.desiredTemperature)
        influxdb_timestamp = str(int(sensor_ts)) + '000000000'

        returnValue += ( influxdb_measurement + ',' + influxdb_tag_set + ' ' + influxdb_field_set + ' ' + influxdb_timestamp + '\n' )

        return Response(returnValue, mimetype='text/xml')



class ExtendedRuntimeClass(Resource):
    '''Class to get the Extended Runtime.'''
    def get(self):

        self.r = redis.Redis(host='redis-cache', port=6379, db=0)

        while True:
            try:

                with self.r.lock('ecobee-acquire-key', blocking_timeout=10) as lock:
                    # code you executed only after the lock has been acquired
                    thermostat = EcobeeEnhanced(config_filename='ecobee.conf')
                    thermostat.read_config_from_file()
                    thermostatFetch = False
                    count = 0

                    try:
                        thermostatFetch = thermostat.get_thermostats()
                    except (ExpiredTokenError) as err:
                        logger.error("Token was expired.")
                        returnValue = thermostat.refresh_tokens()
                        thermostat._write_config()
                        thermostatFetch = thermostat.get_thermostats()
                    count += 1
                    if (count >= 3) or (thermostatFetch == True):
                        break
                    else:
                        time.sleep(1)

            except LockError:
                # the lock wasn't acquired
                time.sleep(1)

        if thermostatFetch == False:
            abort(500)

        return thermostat.getExtendedRuntime(0)


class RuntimeClass(Resource):
    '''Class to extract the Runtime and Remote Sensors data.'''
    def get(self):

        self.r = redis.Redis(host='redis-cache', port=6379, db=0)

        while True:

            try:
                with self.r.lock('ecobee-acquire-key', blocking_timeout=10) as lock:
                    # code you executed only after the lock has been acquired
                    thermostat = EcobeeEnhanced(config_filename='ecobee.conf')
                    thermostat.read_config_from_file()
                    thermostatFetch = False
                    count = 0

                    # code you want executed only after the lock has been acquired
                    try:
                        thermostatFetch = thermostat.get_thermostats()
                    except (ExpiredTokenError) as err:
                        logger.error("Token was expired.")
                        returnValue = thermostat.refresh_tokens()
                        thermostat._write_config()
                        thermostatFetch = thermostat.get_thermostats()
                    count += 1
                    if (count >= 3) or (thermostatFetch == True):
                        break
                    else:
                        time.sleep(1)

            except LockError:
                logger.error("Ecobee acquire was locked.")
                # the lock wasn't acquired
                time.sleep(1)

        if thermostatFetch == False:
            abort(500)


        runtimeRsp = thermostat.getRuntimeAndRemoteSensors(0)
        runningEquipment = thermostat.getRunningEquipments(0)

        returnValue = ''

        if (isinstance(runtimeRsp, Response) and (runtimeRsp.get_data(as_text=True) != '')):
            returnValue += runtimeRsp.get_data(as_text=True)

        if ((type(runningEquipment) == Response) and (runningEquipment.get_data(as_text=True) != '')):
            returnValue += runningEquipment.get_data(as_text=True)


        if (returnValue != ''):
            return Response(returnValue, mimetype='text/xml')
        else:
            return None


class EcobeeThermostatRequestTokens(Resource):
    '''Class to Request the Token.'''
    def get(self):
        thermostat = EcobeeEnhanced(config_filename='ecobee.conf')
        thermostat.read_config_from_file()

        returnValue = thermostat.request_tokens()
        if returnValue:
            message="Success"
            thermostat._write_config()
        else:
            message="Error"
        return message

class EcobeeRunningEquipmentsClass(Resource):
    '''Class to retrieve the list of running equipments.'''
    def get(self):

        self.r = redis.Redis(host='redis-cache', port=6379, db=0)

        while True:

            try:
                with self.r.lock('ecobee-acquire-key', blocking_timeout=10) as lock:
                    # code you executed only after the lock has been acquired
                    thermostat = EcobeeEnhanced(config_filename='ecobee.conf')
                    thermostat.read_config_from_file()
                    thermostatFetch = False
                    count = 0

                    # code you want executed only after the lock has been acquired
                    try:
                        thermostatFetch = thermostat.get_thermostats()
                    except (ExpiredTokenError) as err:
                        logger.error("Token was expired.")
                        returnValue = thermostat.refresh_tokens()
                        thermostat._write_config()
                        thermostatFetch = thermostat.get_thermostats()
                    count += 1
                    if (count >= 3) or (thermostatFetch == True):
                        break
                    else:
                        time.sleep(1)

            except LockError:
                logger.error("Ecobee acquire was locked.")
                # the lock wasn't acquired
                time.sleep(1)

        if thermostatFetch == False:
            abort(500)

        return thermostat.getRunningEquipments(0)


class EcobeeThermostatRequestPin(Resource):
    '''Class to request a new PIN. Check the Debug log for the PIN.'''
    def get(self):
        thermostat = EcobeeEnhanced(config_filename='ecobee.conf')
        thermostat.read_config_from_file()

        returnValuePin = False
        returnValueToken = False
        message="Error"

        returnValuePin = thermostat.request_pin()
        if returnValuePin:
            returnValueToken = thermostat.request_tokens()

        if returnValuePin or returnValueToken:
            thermostat._write_config()

        if returnValuePin and returnValueToken:
            message="Success"

        return message


class EcobeeThermostatApiKey(Resource):
    '''Class to enter a new API Key'''

    def get(self,api_key):
        thermostat = EcobeeEnhanced(config_filename='ecobee.conf')

        returnValue = thermostat.set_api_key(api_key)

        return Response(returnValue, mimetype='text/xml')


api.add_resource(EcobeeThermostatApiKey, '/thermostat/ecobee/apiKey/<api_key>')

api.add_resource(ExtendedRuntimeClass, '/thermostat/ecobee/resource/extended-runtime')
api.add_resource(RuntimeClass, '/thermostat/ecobee/resource/runtime')

api.add_resource(EcobeeRunningEquipmentsClass, '/thermostat/ecobee/equipments/running')

api.add_resource(EcobeeThermostatRequestTokens, '/thermostat/ecobee/token/request')
api.add_resource(EcobeeThermostatRequestPin, '/thermostat/ecobee/pin/request')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
