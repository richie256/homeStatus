# homeStatus

# TODO List

- [x] Fix the temperature service
- [x] Fix the ecobee service
- [x] Adapt the code using the new python-ecobee-api
- [ ] Create a new password mosquitto_passwd
- [ ] Incorporate Ultrasonic distance
- [ ] Google Domain Service (free service)
- [ ] Explore .local hosts
- [ ] Recycling and garbage collect schedule.
- [ ] Perform NodeRed backup: $ docker cp  mynodered:/data  /your/backup/directory




# docker Compose File
InfluxDB: Set a Username and password

# Ultrasonic
Incorporate Ultrasonic distance.

# MQTT
Configure the MQTT

- Install the mosquitto on linux `apt-get install mosquitto`
- Configure the password file: https://mosquitto.org/man/mosquitto_passwd-1.html
- Add a new password: `mosquitto_passwd -c mosquitto_passwd <usrrname>`


# Outside temps from openweathermap.org

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

# Ecobee thermostat

- [x] Adapt the code using the new python-ecobee-api
- [x] Code optimisation
- [x] Fully test expired tokens
- [ ] Add equipmentStatus.
- [ ] Remove the `docker-compose.arm.yaml` file.
- [ ] Integrate desired temperature.
- [ ] Integrate Grafana iFrame: https://community.home-assistant.io/t/best-way-to-get-grafana-chart-into-lovelace-card/128857
- [ ] Create a "Plant Status": https://www.home-assistant.io/lovelace/plant-status/
- [ ] Ajouter uptime, batterie life , metric 


## How to update ecobee config
- Log into your Ecobee account and create a new API under Developer.
- Using the API Key, call the `curl http://localhost:5002/thermostat/ecobee/apiKey/<api_key>`
- Put the logs in Debug Mode.
- Request a new pin: `curl http://localhost:5002/thermostat/ecobee/pin/request` then retrieve the PIN from the Debug logs.
- Enter the PIN in your Ecobee Account, then request the token: `curl http://localhost:5002/thermostat/ecobee/token/request`

# NodeRed

http://192.168.68.120:1880

- [ ] Change the Encrypted key.

Your flow credentials file is encrypted using a system-generated key.

If the system-generated key is lost for any reason, your credentials
file will not be recoverable, you will have to delete it and re-enter
your credentials.

You should set your own key using the 'credentialSecret' option in
your settings file. Node-RED will then re-encrypt your credentials
file using your chosen key the next time you deploy a change.


# To execute:
docker-compose -f docker-compose.yaml up -d homeassistant

docker-compose -f docker-compose.yaml up -d outsidetemp-service

docker-compose -f docker-compose.yaml up -d redis-cache ecobee-service outsidetemp-service influxdb telegraf grafana homeassistant eclipse-mosquitto

docker-compose -f docker-compose.yaml up -d pyhydroquebec

docker-compose -f docker-compose.yaml up -d nodered



cd projects/homeStatus
docker-compose -f docker-compose.yaml up -d outsidetemp-service ecobee-service influxdb telegraf grafana


equipmentStatus
The status of all equipment controlled by this Thermostat. Only running equipment is listed in the CSV String.
Values: heatPump, heatPump2, heatPump3, compCool1, compCool2, auxHeat1, auxHeat2, auxHeat3, fan, humidifier, dehumidifier, ventilator, economizer, compHotWater, auxHotWater.





curl http://localhost:5002/thermostat/ecobee/resource/runtime?format=influx

curl http://localhost:5002/thermostat/ecobee/resource/extended-runtime?format=influx

curl http://localhost:5001/conditions/5909629?format=influx

curl http://localhost:5002/thermostat/ecobee/equipments/running?format=influx


If I want to test the vault outside a container: I do (for example): http://localhost:8200/v1/sys/seal-status

If I want to test inside a container: I do (for example): http://vault:8200/v1/sys/seal-status

