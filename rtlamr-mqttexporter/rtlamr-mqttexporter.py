import json

import docker

#from prometheus_client import start_http_server, Gauge

import settings

import paho.mqtt.publish as publish

#reading = Gauge('rtlamr_meter_reading',
#                'Utility meter data',
#                ['message_type', 'meter_id'])

last_reading = {}

auth = None

if len(settings.MQTT_USER) and len(settings.MQTT_PASSWORD):
    auth = {'username':settings.MQTT_USER, 'password':settings.MQTT_PASSWORD}

def process(line):
    try:
        data = json.loads(line)
    except json.decoder.JSONDecodeError:
        return

    # get some required info: current meter reading, current interval id, most recent interval usage
    #read_cur = int(flds[15])
    #interval_cur = int(flds[10])
    #idm_read_cur = int(flds[16])

    if data['Type'] == 'SCM+':
        message_type = data['Type']
        consumption = data['Message']['Consumption']
        endpoint_id = data['Message']['EndpointID']

    # Other types unsupported for now
    else:
        return

    rate = idm_read_cur * settings.WH_MULTIPLIER * settings.READINGS_PER_HOUR

    current_reading_in_kwh = (read_cur * settings.WH_MULTIPLIER) / 1000

    reading_delta = get_delta(endpoint_id)

    if reading_delta is not None:
        send_mqtt(
            'readings/' + str(endpoint_id) + '/meter_reading',
            '%s' % (current_reading_in_kwh)
        )

    # store consumption info of the current reading
    set_last_interval(endpoint_id, consumption)







def get_last_interval(endpoint_id):
    return last_reading.get(endpoint_id, (None))

def set_last_interval(endpoint_id, consumption) -> None:
    last_reading[endpoint_id] = (consumption)

def get_delta(endpoint_id):
    return get_last_interval(endpoint_id=endpoint_id)



    last_reading[meter_id] = (interval_ID)

# send data to MQTT broker defined in settings
def send_mqtt(topic, payload):
    try:
        publish.single(topic, payload=payload, qos=1, hostname=settings.MQTT_HOST, port=settings.MQTT_PORT, auth=auth)
    except Exception as ex:
        print("MQTT Publish Failed: " + str(ex))

if __name__ == '__main__':
    #start_http_server(8000)


    client = docker.from_env()
    rtlamr = client.containers.list(filters={'name': '_rtlamr_'})[0]

    for line in rtlamr.logs(stream=True):
            process(line)
