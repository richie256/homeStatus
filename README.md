# homeStatus


## TODO: create a new password mosquitto_passwd

# docker Compose File
InfluxDB: Set a Username and password

# Ultrasonic
Incorporate Ultrasonic distance.

# MQTT
Configure the MQTT

# Explore .local hosts

# API Wunderground
Keep the key secure
http://api.wunderground.com/api/


# To execute:
docker-compose -f docker-compose.yaml -f docker-compose.arm.yaml -d up homeassistant


docker-compose -f docker-compose.yaml -f docker-compose.arm.yaml -d up outsidetemp



curl http://localhost:5002/thermostat/ecobee/resource/runtime?format=influx

curl http://localhost:5002/thermostat/ecobee/resource/extended-runtime?format=influx

curl http://localhost:5001/conditions/Brossard?format=dropwizard
curl http://localhost:5001/conditions/Brossard?format=influx




