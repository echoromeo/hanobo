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
from homeassistant.const import CONF_IP_ADDRESS, CONF_HOST, CONF_COMMAND_OFF, CONF_COMMAND_ON, TEMP_CELSIUS, PRECISION_TENTHS
import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_AUTO,
    HVAC_MODE_OFF,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TARGET_TEMP_HIGH,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
    SUPPORT_PRESET_MODE,
    PRESET_NONE,
    PRESET_ECO,
    PRESET_AWAY,
    PRESET_COMFORT
)

from homeassistant.components.climate import ClimateEntity
from pynobo import nobo

#REQUIREMENTS = ['time', 'warnings', 'logging', 'socket', 'threading']

SUPPORT_FLAGS = SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE_RANGE

PRESET_MODES = [
    PRESET_NONE, PRESET_COMFORT, PRESET_ECO, PRESET_AWAY
]

HVAC_MODES = [
    HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_AUTO
]
HVAC_MODES_WITHOUT_OFF = [
    HVAC_MODE_HEAT, HVAC_MODE_AUTO
]

MIN_TEMPERATURE = 7
MAX_TEMPERATURE = 40

_LOGGER = logging.getLogger(__name__)

_ZONE_NORMAL_WEEK_LIST_SCHEMA = vol.Schema({cv.string: cv.string})

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_IP_ADDRESS, default='discover'): cv.string,
    vol.Optional(CONF_COMMAND_OFF, default=''): cv.string,
    vol.Optional(CONF_COMMAND_ON, default={}): _ZONE_NORMAL_WEEK_LIST_SCHEMA,
})

def get_id_from_name(name, dictionary):
    for key in dictionary.keys():
        # Replace unicode non-breaking space (used in Nobø hub) with space
        if dictionary[key]['name'].replace(u'\xa0', u' ') == name:
            return key
    return None

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

    # Find OFF command (week profile) to use for all zones:
    command_off_name = config.get(CONF_COMMAND_OFF)
    command_on_by_id = {} # By default, nothing can be turned on
    if command_off_name == '':
        _LOGGER.info("Not possible to turn off (or on) any heater, because OFF week profile was not specified")
        command_off_id = None
    else:
        command_off_id = get_id_from_name(command_off_name, hub.week_profiles)
        if command_off_id == '' or command_off_id == None:
            _LOGGER.error("Can not turn off (or on) any heater, because week profile '%s' was not found", command_off_name)
        else:
            _LOGGER.info("To turn off any heater, week profile %s '%s' will be used", command_off_id, command_off_name)

            # Find ON command (week profile) for the different zones:
            command_on_dict = config.get(CONF_COMMAND_ON)
            command_on_by_id = {}
            if command_on_dict.keys().__len__ == 0:
                _LOGGER.info("Not possible to turn on any heater, because ON week profile was not specified")
            for room_name in command_on_dict.keys():
                command_on_name = command_on_dict[room_name]
                room_id = get_id_from_name(room_name, hub.zones)
                if room_id == '' or room_id == None:
                    _LOGGER.error("Can not turn on (or off) heater in zone '%s', because that zone (heater name) was not found", room_name)
                else:
                    command_on_id = get_id_from_name(command_on_name, hub.week_profiles)
                    if command_on_id == '' or command_on_id == None:
                        _LOGGER.error("Can not turn on (or off) heater in zone '%s', because week profile '%s' was not found", room_name, command_on_name)
                    else:
                        _LOGGER.info("To turn on heater %s '%s', week profile %s '%s' will be used", room_id, room_name, command_on_id, command_on_name)
                        command_on_by_id[room_id] = command_on_id


    # Add devices
    hub.socket_received_all_info.wait()
    add_devices(AwesomeHeater(zones, hub, command_off_id, command_on_by_id.get(zones) ) for zones in hub.zones)
    _LOGGER.info("component is up and running on %s:%s", hub.hub_ip, hub.hub_serial)

    return True

class AwesomeHeater(ClimateEntity):
    """Representation of a demo climate device."""

    def __init__(self, id, hub, command_off_id, command_on_id):
        """Initialize the climate device."""
        self._id = id
        self._nobo = hub
        self._name = self._nobo.zones[self._id]['name']
        self._current_mode = HVAC_MODE_AUTO
        self._command_off_id = command_off_id
        self._command_on_id = command_on_id

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
        # Only enable off-command if on- and off-command exists for this zone:
        if self.can_turn_off():
            return HVAC_MODES
        else:
            return HVAC_MODES_WITHOUT_OFF

    @property
    def hvac_mode(self):
        """Return current operation HVAC Mode."""
        return self._current_mode

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
        """Set HVAC mode to comfort(HEAT) or back to normal(AUTO)"""
        if hvac_mode == HVAC_MODE_AUTO:
            self.set_preset_mode(PRESET_NONE)
            self._current_mode = hvac_mode
        elif hvac_mode == HVAC_MODE_HEAT:
            self.set_preset_mode(PRESET_COMFORT)
            self._current_mode = hvac_mode
        
        if self.can_turn_off():
            if hvac_mode == HVAC_MODE_OFF:
                self.set_preset_mode(PRESET_NONE)
                self._current_mode = hvac_mode
                self._nobo.update_zone(self._id, week_profile_id=self._command_off_id) # Change week profile to OFF
                _LOGGER.debug("Turned off heater %s '%s' by switching to week profile %s", self._id, self._name, self._command_off_id)
            else:
                self._nobo.update_zone(self._id, week_profile_id=self._command_on_id) # # Change week profile to normal for this zone
                _LOGGER.debug("Turned on heater %s '%s' by switching to week profile %s", self._id, self._name, self._command_on_id)
            # When switching between AUTO and OFF an immediate update does not work (the nobø API seems to answer with old values), but it works if we add a short delay:
            time.sleep(0.5)
            self.schedule_update_ha_state()
        elif hvac_mode == HVAC_MODE_OFF:
            _LOGGER.error("User tried to turn off heater %s '%s', but this is not configured so this should be impossible.", self._id, self._name)

    def can_turn_off(self):
        """
        Returns true if heater can turn off and on
        """
        return self._command_on_id != None and self._command_off_id != None

    def set_preset_mode(self, operation_mode):
        """Set new zone override."""
        if self._nobo.zones[self._id]['override_allowed'] == '1':
            if operation_mode == PRESET_ECO:
                mode = self._nobo.API.OVERRIDE_MODE_ECO
            elif operation_mode == PRESET_AWAY:
                mode = self._nobo.API.OVERRIDE_MODE_AWAY
            elif operation_mode == PRESET_COMFORT:
                mode = self._nobo.API.OVERRIDE_MODE_COMFORT
            else: #PRESET_NONE
                mode = self._nobo.API.OVERRIDE_MODE_NORMAL
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
        self._current_mode = HVAC_MODE_AUTO
        self._current_operation = PRESET_NONE

        if state == self._nobo.API.NAME_OFF:
            self._current_mode = HVAC_MODE_OFF
        elif state == self._nobo.API.NAME_AWAY:
            self._current_operation = PRESET_AWAY
        elif state == self._nobo.API.NAME_ECO:
            self._current_operation = PRESET_ECO
        elif state == self._nobo.API.NAME_COMFORT:
            self._current_operation = PRESET_COMFORT

        if self._nobo.zones[self._id]['override_allowed'] == '1':
            for o in self._nobo.overrides:
                if self._nobo.overrides[o]['mode'] == '0':
                    continue  # "normal" overrides
                elif self._nobo.overrides[o]['target_type'] == self._nobo.API.OVERRIDE_TARGET_ZONE:
                    if self._nobo.overrides[o]['target_id'] == self._id:
                        self._current_mode = HVAC_MODE_HEAT

        self._current_temperature = self._nobo.get_current_zone_temperature(self._id)
        self._target_temperature_high = int(self._nobo.zones[self._id]['temp_comfort_c'])
        self._target_temperature_low = int(self._nobo.zones[self._id]['temp_eco_c'])
