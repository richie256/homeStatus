# homeStatus


## TODO: create a new password mosquitto_passwd

# docker Compose File
InfluxDB: Set a Username and password

# Ultrasonic
Incorporate Ultrasonic distance.

# MQTT
Configure the MQTT

# Explore .local hosts

# ~~API Wunderground~~ --> need to change

*Wunderground doesn't offer free API keys anymore*

We need to find an alternative.
--> Alternative openweathermap.org

http://api.openweathermap.org/data/2.5/forecast?id={CITY_CODE_ID}&APPID={APPID}


Frequency: 
Calls per minute (no more than)	60
no more than one time every 10 minutes for one location (city / coordinates / zip-code).


If blocked:
{
"cod": 429,
"message": "Your account is temporary blocked due to exceeding of requests limitation of your subscription type. 
Please choose the proper subscription http://openweathermap.org/price"
}


# To execute:
docker-compose -f docker-compose.yaml -f docker-compose.arm.yaml -d up homeassistant


docker-compose -f docker-compose.yaml -f docker-compose.arm.yaml -d up outsidetemp



curl http://localhost:5002/thermostat/ecobee/resource/runtime?format=influx

curl http://localhost:5002/thermostat/ecobee/resource/extended-runtime?format=influx

curl http://localhost:5001/conditions/Brossard?format=dropwizard
curl http://localhost:5001/conditions/Brossard?format=influx


If I want to test the vault outside a container: I do (for example): http://localhost:8200/v1/sys/seal-status

If I want to test inside a container: I do (for example): http://vault:8200/v1/sys/seal-status

