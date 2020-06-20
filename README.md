# homeStatus

# TODO List

- [x] Fix the temperature service
- [x] Fix the ecobee service
- [x] Adapt the code using the new python-ecobee-api
- [ ] Incorporate Ultrasonic distance
- [ ] Google Domain Service (free service)
- [ ] Explore .local hosts
- [ ] Recycling and garbage collect schedule.
- [ ] Perform NodeRed backup: $ `docker cp  mynodered:/data  /your/backup/directory`
- [ ] Create a "Plant Status": https://www.home-assistant.io/lovelace/plant-status/
- [ ] Ajouter uptime, batterie life , metric 
- [x] Ajouter collecte des ordures. https://www.reddit.com/r/homeassistant/comments/blf3wu/put_some_time_into_lovelace_again_tried_to_make/
- [x] Ajouter bignumber-card: https://github.com/custom-cards/bignumber-card
- [x] Suivre les instructions: https://community.home-assistant.io/t/lovelace-bignumber-card/59280
- [x] Ajouter custom:vertical-style-card: https://github.com/matisaul/vertical-style-card
- [x] RTL Bus schedule to MQTT.
- [x] Integrate RTL Bus schedule.
- [ ] Integrate Grafana iFrame: https://community.home-assistant.io/t/best-way-to-get-grafana-chart-into-lovelace-card/128857
- [ ] Remove the `docker-compose.arm.yaml` file.
- [ ] Incorporate ecobeeapi and outsidetemp as individual containers.
- [ ] raspberry CPU temp info and other?

utility_meter. https://www.home-assistant.io/integrations/utility_meter/
https://community.home-assistant.io/t/any-experience-with-utility-meter-functions/149904

graph:
integration https://www.home-assistant.io/integrations/integration/
mini-graph-card: https://github.com/kalkih/mini-graph-card


mqtt publish?  example: https://github.com/fliphess/esp8266_p1meter

example mqtt:
sensors/power/p1meter/consumption_low_tarif 2209397
sensors/power/p1meter/consumption_high_tarif 1964962
sensors/power/p1meter/actual_consumption 313
sensors/power/p1meter/instant_power_usage 313
sensors/power/p1meter/instant_power_current 1000
sensors/power/p1meter/gas_meter_m3 968922
sensors/power/p1meter/actual_tarif_group 2
sensors/power/p1meter/short_power_outages 3
sensors/power/p1meter/long_power_outages 1
sensors/power/p1meter/short_power_drops 0
sensors/power/p1meter/short_power_peaks 0

Time
Uptime



sensors/gas/1234567/total_consumption 968922
sensors/gas/1234567/reading 1

total_consumption




- [ ] Secheuse laveuse - https://www.reddit.com/r/homeassistant/comments/elybp8/tutorial_make_your_dryer_washing_machine_smart/


# Inspirations
- [ ] F1 Qualifications: https://www.reddit.com/r/homeassistant/comments/cerjse/big_thumbs_up_for_the_0960_sleek_sidebar_really/
- [ ] Environment Canada alerts: https://community.home-assistant.io/t/scrape-sensor-component-get-two-tags/83302
https://weather.gc.ca/rss/warning/qc-147_f.xml







Arrêt av. Malo et Montmartre Code d'arrêt: 32752

Ligne(s) à cet arrêt:
 44 Direction Terminus 
 Centre-ville/Terminus Panama  (horaire)
 144 Direction Terminus Centre-ville  
 (horaire)

Arrêt(s) à proximité
av. Malo et Montmartre:
 44 Direction Secteurs M-N-O de Brossard  
 (horaire)
 144 Direction Secteurs M-N-O de Brossard  
 (horaire)



Secteurs M-N-O







# docker Compose File
InfluxDB: Set a Username and password

# Ultrasonic
Incorporate Ultrasonic distance.

# MQTT
Configure the MQTT

- Install the mosquitto on linux `apt-get install mosquitto`
- Configure the password file: https://mosquitto.org/man/mosquitto_passwd-1.html
- Add a new password: `mosquitto_passwd -c mosquitto_passwd <usrrname>`

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

docker-compose -f docker-compose.yaml up -d redis-cache ecobee-service outsidetemp-service influxdb telegraf grafana homeassistant eclipse-mosquitto nodered



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

