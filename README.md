# homeStatus


## TODO: create a new password mosquitto_passwd

# docker Compose File
InfluxDB: Set a Username and password

# Ultrasonic
Incorporate Ultrasonic distance.

# MQTT
Configure the MQTT

<<<<<<< HEAD
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


If I want to test the vault outside a container: I do (for example): http://localhost:8200/v1/sys/seal-status

If I want to test inside a container: I do (for example): http://vault:8200/v1/sys/seal-status

