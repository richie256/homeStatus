    # OutsideTemp service

from flask import Flask
from flask import Response
from flask import jsonify
from flask import request

from flask_restful import Resource, Api

# import urllib2
from urllib.request import urlopen

import datetime, time
import pytz
import json

from dateutil import tz
import calendar
import sys

import logging

# create logger with 'ecobee_application'
logger = logging.getLogger('wunderground_application')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('wunderground.log')
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
 
            #Python 3.4:
            wunderground = None
            wunderground = urlopen('http://api.wunderground.com/api/' + FIXME_WUNDERGROUND_API_KEY + '/conditions/astronomy/hourly/q/Canada/Brossard.json')
            #charset = wunderground.info().get_param('charset', 'utf8')
            #data = wunderground.read()
            #parsed_json = json.loads(data.decode(charset))

            json_string = wunderground.read()
            parsed_json = json.loads(json_string)
 
            self.tempVal = parsed_json['current_observation']['temp_c']
            self.relativeHumidity = int(parsed_json['current_observation']['relative_humidity'].rstrip('%'))
            observationTS = parsed_json['current_observation']['observation_time_rfc822']
            self.wind_string = parsed_json['current_observation']['wind_string']
            self.wind_dir = parsed_json['current_observation']['wind_dir']
            self.wind_degrees =  parsed_json['current_observation']['wind_degrees']
            self.wind_kph =      parsed_json['current_observation']['wind_kph']
            self.wind_gust_kph = parsed_json['current_observation']['wind_gust_kph']


            self.sunrise_dict.update({"hour":int(parsed_json['sun_phase']['sunrise']['hour'])})
            self.sunrise_dict.update({"minute":int(parsed_json['sun_phase']['sunrise']['minute'])})
            hour = int(parsed_json['sun_phase']['sunrise']['hour'])
            minute = int(parsed_json['sun_phase']['sunrise']['minute'])
            self.sunrise = datetime.time(hour, minute, 0)

            self.sunset_dict.update({"hour":int(parsed_json['sun_phase']['sunset']['hour'])})
            self.sunset_dict.update({"minute":int(parsed_json['sun_phase']['sunset']['minute'])})
            hour   = int(parsed_json['sun_phase']['sunset']['hour'])
            minute = int(parsed_json['sun_phase']['sunset']['minute'])
            self.sunset = datetime.time(hour, minute, 0)

            # exemple: "Thu, 12 Jul 2012 04:00:00 +1000"
            # https://docs.python.org/3.3/library/datetime.html#datetime.datetime.timestamp

            # self.observationTS = datetime.datetime.timestamp.strptime(observationTS[:-6], '%a, %d %b %Y %H:%M:%S')
            observationDateTime = datetime.datetime.strptime(observationTS[:-6], '%a, %d %b %Y %H:%M:%S')


            utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
            utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
            self.observationISOTz = observationDateTime.replace(tzinfo=datetime.timezone(offset=utc_offset)).isoformat()


            # self.observation_epoch = parsed_json['current_observation']['observation_epoch']
            # self.observation_epoch = datetime.datetime.fromtimestamp(int(parsed_json['current_observation']['observation_epoch']))
            self.observation_epoch = parsed_json['current_observation']['observation_epoch']

            # pst = pytz.timezone('Etc/UTC')
            # self.observation_epoch = pst.localize(self.observation_epoch).timestamp()


            # from_zone = tz.tzutc()
            # to_zone = tz.tzstr(parsed_json['current_observation']['local_tz_long'])

            # Tell the datetime object that it's in UTC time zone since
            # datetime objects are 'naive' by default
            # observ_epoch = observ_epoch.replace(tzinfo=from_zone)

            # Convert time zone
            # local_dt = observ_epoch.astimezone(to_zone)

            # return calendar.timegm(dt.timetuple())
            # self.observation_epoch = calendar.timegm(local_dt.timetuple())

            # projected = parsed_json['hourly_forecast'][7]['temp']['metric']
            # projectedTS = observationTS +datetime.timedelta(hours=8)

        except:
            self.success_result = False
            if wunderground is not None:
                logger.error('Problem with getting outside infos in JSON. wunderground = '+str(wunderground) +' and json_string = '+str(json_string))
            else:
                logger.error('Problem with getting outside infos in JSON. wunderground is None.')


            logger.error(sys.exc_info()[0])
            return sys.exc_info()[0]

        finally:
            if wunderground is not None:
                wunderground.close()

    def get(self,location):

        self.getOutsideInfos(location)

        if (not self.success_result):
            return ''

        # JSON Format
        if self.opt_format == self.CONST_JSON:

            outsideTemp = { 'service': 'outsideTemp',
                            'location': self.location,
                            'opt_format': self.opt_format,
                            'tempVal': self.tempVal,
                            'relativeHumidity': self.relativeHumidity,
                            'observationTS': self.observationTS,
                            'sunrise': self.sunrise_dict,
                            'sunset': self.sunset_dict,
                            'wind_string': self.wind_string,
                            'wind_dir': self.wind_dir,
                            'wind_degrees': self.wind_degrees,
                            'wind_kph': self.wind_kph,
                            'wind_gust_kph': self.wind_gust_kph
                          }

            return jsonify(outsideTemp)

        # Infux format
        elif self.opt_format == self.CONST_INFLUX:
            # returnValue = {'cpu,atag=test1 idle=100,usertime=10,system=1','db':'DBNAME',204,'line'}
            # returnValue = {'cpu,atag=test1ss':'ss'}

            returnValue = ( 'apidata,source=wunderground,location=' + self.location + ',opt_format=' + self.opt_format + ' tempVal=' + str(self.tempVal) + ',relativeHumidity=' + str(self.relativeHumidity) + ' ' + self.observation_epoch + '000000000' + '\n' )

            return Response(returnValue, mimetype='text/xml')

        # dropwizard format
        elif self.opt_format == self.CONST_DROPWIZARD:
            returnValue = {
                        "time": self.observationISOTz,
                        "name": "dropwizard_outsideTemp",
                        "tags": {
                            "location": self.location,
                            "source": "wunderground",
                            "opt_format": self.opt_format
                        },
                        "metrics": {
                            'tempVal': self.tempVal,
                            'relativeHumidity': self.relativeHumidity,
                            'wind_string': self.wind_string,
                            'wind_dir': self.wind_dir,
                            'wind_degrees': self.wind_degrees,
                            'wind_kph': self.wind_kph,
                            'wind_gust_kph': self.wind_gust_kph
                        }
                    }
            return jsonify(returnValue)

    #GET /conditions/Brossard?format=influx

api.add_resource(OutsideTemp, '/conditions/<string:location>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
