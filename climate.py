"""
Python Websocet Control of Nobø Hub - Nobø Energy Control
"""
import time
import datetime
import warnings
import logging
import collections
import socket
import threading
import voluptuous as vol
import homeassistant.util.dt as dt_util
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import CONF_IP_ADDRESS, CONF_HOST, TEMP_CELSIUS, PRECISION_WHOLE, PRECISION_TENTHS
import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate.const import (HVAC_MODE_AUTO, ATTR_TARGET_TEMP_LOW, ATTR_TARGET_TEMP_HIGH, SUPPORT_TARGET_TEMPERATURE_RANGE, SUPPORT_PRESET_MODE)
from homeassistant.components.climate import ClimateDevice
from .pynobo.nobo import nobo

#REQUIREMENTS = ['time', 'warnings', 'logging', 'socket', 'threading']

SUPPORT_FLAGS = SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE_RANGE

STATE_AWAY = 'Away'
STATE_COMFORT = 'Comfort'
STATE_NORMAL = 'Normal'
STATE_ECO = 'Eco'

PRESET_MODES = [
    STATE_NORMAL, STATE_COMFORT, STATE_ECO, STATE_AWAY
]

HVAC_MODES = [
    HVAC_MODE_AUTO
]

MIN_TEMPERATURE = 7
MAX_TEMPERATURE = 40

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_IP_ADDRESS, default='discover'): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Awesome heater platform."""

    # Assign configuration variables. The configuration check takes care they are
    # present. 
    host = config.get(CONF_HOST)
    ip = config.get(CONF_IP_ADDRESS)

    # Setup connection with devices/cloud
    if ip == 'discover':
        _LOGGER.info("discovering and connecting to %s", host)
        hub = nobo(serial=host)
    else:
        _LOGGER.info("connecting to %s:%s", ip, host)
        hub = nobo(serial=host, ip=ip, discover=False)

    # Verify that passed in configuration works
#    if not hub.is_valid_login():
#        _LOGGER.error("Could not connect to AwesomeHeater hub")
#        return False

    # Add devices
    hub.socket_received_all_info.wait()
    add_devices(AwesomeHeater(zones, hub) for zones in hub.zones)
    _LOGGER.info("component is up and running on %s:%s", hub.hub_ip, hub.hub_serial)

    return True

class AwesomeHeater(ClimateDevice):
    """Representation of a demo climate device."""

    def __init__(self, id, hub):
        """Initialize the climate device."""
        self._id = id
        self._nobo = hub
        self._name = self._nobo.zones[self._id]['name']

        self.update()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_TENTHS #PRECISION_WHOLE

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return MIN_TEMPERATURE

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return MAX_TEMPERATURE

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return self._target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return self._target_temperature_low

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return HVAC_MODES

    @property
    def hvac_mode(self):
        """Return current operation HVAC Mode."""
        return HVAC_MODE_AUTO

    @property
    def preset_mode(self):
        """Return current preset mode"""
        return self._current_operation

    @property
    def preset_modes(self):
        """Return the preset modes, comfort, away etc"""
        return PRESET_MODES
        
    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._current_temperature is not None:
            return float(self._current_temperature)
        return None

    def set_hvac_mode(self, hvac_mode):
        """Noop for the time being"""
        hvac_mode = hvac_mode.lower()

    def set_preset_mode(self, operation_mode):
        """Set new zone override."""
        if self._nobo.zones[self._id]['override_allowed'] == '1':
            operation_mode = operation_mode.lower()
            mode = self._nobo.API.DICT_NAME_TO_OVERRIDE_MODE[operation_mode]
            self._nobo.create_override(mode, self._nobo.API.OVERRIDE_TYPE_CONSTANT, self._nobo.API.OVERRIDE_TARGET_ZONE, self._id)
            #TODO: override to program if new operation mode == current week profile status
        self.schedule_update_ha_state()

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        low = int(kwargs.get(ATTR_TARGET_TEMP_LOW))
        high = int(kwargs.get(ATTR_TARGET_TEMP_HIGH))
        if low > int(self._nobo.zones[self._id]['temp_comfort_c']):
            low = int(self._nobo.zones[self._id]['temp_comfort_c'])
        if high < int(self._nobo.zones[self._id]['temp_eco_c']):
            high = int(self._nobo.zones[self._id]['temp_eco_c'])
        self._nobo.update_zone(self._id, temp_comfort_c=high, temp_eco_c=low)
        self.schedule_update_ha_state()

    def update(self):
        """Fetch new state data for this zone.

        This is the only method that should fetch new data for Home Assistant.
        """
        state = self._nobo.get_current_zone_mode(self._id, dt_util.as_local(dt_util.now()))
        if self._nobo.zones[self._id]['override_allowed'] == '1':
            self._current_operation = 'Normal (' + state + ')'
            for o in self._nobo.overrides:
                if self._nobo.overrides[o]['mode'] == '0':
                    continue  # "normal" overrides
                elif self._nobo.overrides[o]['target_type'] == self._nobo.API.OVERRIDE_TARGET_ZONE:
                    if self._nobo.overrides[o]['target_id'] == self._id:
                        self._current_operation = state
        else:
            self._current_operation = 'Locked (' + state + ')'
        self._current_temperature = self._nobo.get_current_zone_temperature(self._id)
        if self._current_temperature == 'N/A':
            self._current_temperature = None
        self._target_temperature_high = int(self._nobo.zones[self._id]['temp_comfort_c'])
        self._target_temperature_low = int(self._nobo.zones[self._id]['temp_eco_c'])        
