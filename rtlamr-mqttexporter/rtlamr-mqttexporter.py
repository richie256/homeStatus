import json

import docker

import os

# from prometheus_client import start_http_server, Gauge

# import settings

import paho.mqtt.publish as publish

# reading = Gauge('rtlamr_meter_reading',
#                'Utility meter data',
#                ['message_type', 'meter_id'])

last_reading = {}

auth = None

if os.environ.get('MQTT_USER') is not None and os.environ.get('MQTT_PASSWORD') is not None:
    auth = {'username': os.environ.get('MQTT_USER'), 'password': os.environ.get('MQTT_PASSWORD')}

# class ParseRtlamrData:
#
#     def __init__(self):
#
#         if os.environ.get('MQTT_USER') is None:


def process(current_line):
    try:
        data = json.loads(current_line)
    except json.decoder.JSONDecodeError:
        return

    # get some required info: current meter reading, current interval id, most recent interval usage
    # read_cur = int(flds[15])
    # interval_cur = int(flds[10])
    # idm_read_cur = int(flds[16])

    if data['Type'] == 'SCM+':
        # message_type = data['Type']
        consumption = data['Message']['Consumption']
        endpoint_id = data['Message']['EndpointID']
        endpoint_type = data['Message']['EndpointType']

        # Other types unsupported for now
    else:
        return

    # rate = idm_read_cur * settings.WH_MULTIPLIER * settings.READINGS_PER_HOUR

    # current_reading_in_kwh = (read_cur * settings.WH_MULTIPLIER) / 1000

    reading_delta = get_delta(endpoint_id)

    # sensors/gas/1234567/total_consumption = 968922
    # sensors/gas/1234567/reading = 1

    if reading_delta is not None:
        # 156 mean gas
        # sensors/gas/1234567/total_consumption = 968922
        # sensors/gas/1234567/reading = 1
        if endpoint_type == 156:
            send_mqtt(
                'sensors/gas/' + str(endpoint_id) + '/total_consumption',
                '%s' % consumption
            )

            # Requires a JSON message.
            send_mqtt(
                'sensors/gas/' + str(endpoint_id) + '/reading',
                '%s' % reading_delta
            )

        else:
            return

    # store consumption info of the current reading
    set_last_interval(endpoint_id, consumption)


def get_last_interval(endpoint_id):
    return last_reading.get(endpoint_id, None)


def set_last_interval(endpoint_id, consumption) -> None:
    last_reading[endpoint_id] = consumption


def get_delta(endpoint_id):
    return get_last_interval(endpoint_id=endpoint_id)


# send data to MQTT broker defined in settings
def send_mqtt(topic, payload):
    try:
        publish.single(topic, payload=payload, qos=1, hostname=os.environ.get('MQTT_HOST'), port=os.environ.get('MQTT_PORT'), auth=auth)
    except Exception as ex:
        print("MQTT Publish Failed: " + str(ex))


if __name__ == '__main__':
    # start_http_server(8000)

    client = docker.from_env()
    rtlamr = client.containers.list(filters={'name': '_rtlamr_'})[0]

    for line in rtlamr.logs(stream=True):
        process(line)
