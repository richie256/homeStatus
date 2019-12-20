




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



            # http://api.openweathermap.org/data/2.5/weather?id=5909629&appid=f4df49fe8112224e1cbc4818c810a73b&units=metric
 
            #Python 3.4:
            openweathermap = None
            openweathermap = urlopen('http://api.openweathermap.org/data/2.5/weather?id=' + FIXME_OPENWEATHERMAP_LOCATION_ID + '&appid=' + FIXME_OPENWEATHERMAP_API_KEY + '&units=metric' + FIXME_OPENWEATHERMAP_UNITS )


            json_string = openweathermap.read()
            parsed_json = json.loads(json_string)


			# Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
            self.tempVal = parsed_json['main']['temp']
            self.humidity = int(parsed_json['main']['humidity'])

            # Time of data calculation, unix, UTC
            observationDT = parsed_json['dt']


            #Wind
            # Unit Default: meter/sec, Metric: meter/sec, Imperial: miles/hour.
			self.windSpeed = parsed_json['wind']['speed']
			self.windDeg   = parsed_json['wind']['deg']



            self.wind_string = parsed_json['current_observation']['wind_string']
            self.wind_dir = parsed_json['current_observation']['wind_dir']
            self.wind_degrees =  parsed_json['current_observation']['wind_degrees']
            self.wind_kph =      parsed_json['current_observation']['wind_kph']
            self.wind_gust_kph = parsed_json['current_observation']['wind_gust_kph']




