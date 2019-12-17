#Libraries
import RPi.GPIO as GPIO
import time
 
#GPIO Mode (BOARD / BCM)
 
#set GPIO Pins
# GPIO_TRIGGER = 18
# GPIO_ECHO = 24
 
#set GPIO direction (IN / OUT)
# GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
# GPIO.setup(GPIO_ECHO, GPIO.IN)
 

COLORGREEN = 'GREEN'
COLORAMBER = 'AMBER'
COLORRED = 'RED'

#preferences
# compensation=0
depth=75
levelamber = 30
levelred = 65


class ultrasonic(object):

    def __init__(self, gpio_trigger, gpio_echo, depth, compensation=0):
        self.distance = None
        self.startTime = None
        self.distance = None
        self.gpio_trigger = gpio_trigger
        self.gpio_echo = gpio_echo
        self.depth = depth
        self.compensation = compensation

        GPIO.setmode(GPIO.BCM)

        #set GPIO direction (IN / OUT)
        GPIO.setup(self.gpio_trigger, GPIO.OUT)
        GPIO.setup(self.gpio_echo, GPIO.IN)

    def retrieveDistance(self):
        # set Trigger to HIGH
        GPIO.output(self.gpio_trigger, True)
     
        # set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        GPIO.output(self.gpio_trigger, False)
     
        self.startTime = time.time()
        StopTime = time.time()
     
        # save StartTime
        while GPIO.input(self.gpio_echo) == 0:
            self.startTime = time.time()
     
        # save time of arrival
        while GPIO.input(self.gpio_echo) == 1:
            StopTime = time.time()
     
        # time difference between start and arrival
        TimeElapsed = StopTime - self.startTime
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        disdistance = (TimeElapsed * 34300) / 2 + self.compensation
        self.distance = round(disdistance, 0)

    def getDistance(self):
        if self.distance is None:
            self.retrieveDistance()

        return self.distance

    def waterLevel(self):
        if self.distance is None:
            self.retrieveDistance()

        return self.depth - self.distance

    def waterLevelPercent(self):
        """Return the water level in percentage."""
        if self.distance is None:
            self.retrieveDistance()

        return round((self.depth - self.distance) / self.depth * 100 ,0)

 
class ResourceClass(Resource):
    CONST_JSON = 'JSON'
    CONST_INFLUX = 'influx'
    CONST_DROPWIZARD = 'dropwizard'

    def __init__(self):
        self.opt_format = request.args.get("format")
        if self.opt_format is None:
            self.opt_format = self.CONST_JSON

    def get(self):

        gpio_trigger = 18
        gpio_echo = 24
        depth = 75          # Value in centimeters
        compensation = 0

        pump = ultrasonic(gpio_trigger, gpio_echo, depth, compensation)
        self.distance = pump.getDistance()

        self.niveaudo = pump.waterLevel()

        sizeofreeblock = self.distance * 5             #this will change the size of the table
        sizeofusedblock = (pump.waterLevel()) * 5    #this will change the size of the table

        if self.niveaudo >= levelred:
            self.levelcolor = COLORRED
        elif self.niveaudo >= levelamber:
            self.levelcolor = COLORAMBER
        else:
            self.levelcolor = COLORGREEN


        # JSON Format
        if self.opt_format == self.CONST_JSON:
            pass

        # Infux format
        elif self.opt_format == self.CONST_INFLUX:
            returnValue = ( 'apidata,source=ultrasonic_distance,location=Brossard,opt_format=' + self.opt_format + ' distance=' + str(self.distance) + ',niveaudo=' + self.niveaudo + ',levelcolor=' + self.levelcolor + '\n' )

            return Response(returnValue, mimetype='text/xml')

api.add_resource(ResourceClass, '/sumppump/ultrasonic_distance')


# http://localhost:5004/sumppump/ultrasonic_distance?format=influx


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
    # try:
    #     while True:
    #         dist = distance()
    #         print ("Measured Distance = %.1f cm" % dist)
    #         time.sleep(1)
 
    #     # Reset by pressing CTRL + C
    # except KeyboardInterrupt:
    #     print("Measurement stopped by User")
    #     GPIO.cleanup()
