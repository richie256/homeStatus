from homeassistant.const import LENGTH_CENTIMETERS
from homeassistant.helpers.entity import Entity

"""Icon helper methods."""
from typing import Optional

CONF_DEPTH = 'depth'  # type: str

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""

    # Distance or depth
    depth = config.get(CONF_DEPTH)
    compensation = config.get(CONF_COMPENSATION)

    # Define GPIO to use on Pi
    trigger_pin = config.get(CONF_GPIO_TRIGGER_PIN)
    echo_pin = config.get(CONF_GPIO_ECHO_PIN)

    add_devices([UltrasonicSensor(depth, compensation, trigger_pin, echo_pin)])

class UltrasonicSensor(Entity):
    """Ultrasonic Measurement."""

    def __init__(self, depth, compensation=0, trigger_pin, echo_pin):
        """Initialize the sensor."""
        self._state = None
        self.depth = depth
        self.compensation = compensation

        self.pump = ultrasonic(trigger_pin, echo_pin, self.depth, self.compensation)
        # self.distance = pump.getDistance()
        self.pump.retrieveDistance()
        self._state = self.pump.getDistance()

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Sump pump level'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """
        'mdi:circle-outline'
        'mdi:circle-slice-1'
        'mdi:circle-slice-2'
        'mdi:circle-slice-3'
        'mdi:circle-slice-4'
        'mdi:circle-slice-5'
        'mdi:circle-slice-6'
        'mdi:circle-slice-7'
        'mdi:circle-slice-8'
        'mdi:alert-circle'
        """
        # return 'mdi:circle-slice-8'

        return self.icon_for_water_level(self.pump.waterLevelPercent())

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return LENGTH_CENTIMETERS

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.pump.retrieveDistance()
        self._state = self.pump.getDistance()

    def icon_for_water_level(water_level: Optional[int] = None) -> str:
        """
        return the icon representation of the water level progress
        """

        if water_level is None:
            return 'mdi:circle-outline'
        else:
            wperc = int(round((water_level / 10) - .01)) * 10
        
        if wperc >= 90:
            icon = 'mdi:alert-circle'
        elif wperc < 10:
            icon = 'mdi:circle-outline'
        else:
            # icon = x
            # icon = (wperc/10)
            icon = 'mdi:circle-slice'
            icon += '-{}'.format(wperc / 10)
        
        return icon 
