# homeStatus


## TODO: create a new password mosquitto_passwd

# docker Compose File
InfluxDB: Set a Username and password

# Ultrasonic
Incorporate Ultrasonic distance.

# MQTT
Configure the MQTT

mosquitto seems to take 100% of processor... desabled for now

# Explore .local hosts

# ~~API Wunderground~~ --> need to change

*Wunderground doesn't offer free API keys anymore*

We need to find an alternative.
--> Alternative openweathermap.org

Forecast:
http://api.openweathermap.org/data/2.5/forecast?id={CITY_CODE_ID}&APPID={APPID}

Current:
http://api.openweathermap.org/data/2.5/weather?id={CITY_CODE_ID}&APPID={APPID}&units=metric

Details on the api response
https://openweathermap.org/current

Weather sample:
https://samples.openweathermap.org/data/2.5/weather?id=2172797&appid=b6907d289e10d714a6e88b30761fae22

Weather Icons list:
https://openweathermap.org/weather-conditions





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

