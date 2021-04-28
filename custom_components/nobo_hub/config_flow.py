''"""Config flow for Nobø Ecohub platform."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_NAME)
from homeassistant.core import callback

#from pynobo import nobo
from .pynobo import nobo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_NOBO_HUB_IMPL = "nobo_hub_flow_implementation"
DEVICE_INPUT = "device_input"


@callback
def register_flow_implementation(hass, serial, ip):
    """Register a Nobø Ecohub implementation.

    host: Serial number of the hub. All 12 digits or last 3 digits.
    ip_address: IP address of the hub.
    """
    hass.data.setdefault(DATA_NOBO_HUB_IMPL, {})

    hass.data[DATA_NOBO_HUB_IMPL] = {
        CONF_HOST: serial,
        CONF_IP_ADDRESS: ip,
    }


class NoboHubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nobø Ecohub."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        self.discovered_hubs = None
        self.serial = None
        self.ip = None
        self.name = None
        self.off_command = None

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the initial step."""
        if self.discovered_hubs is None:
            self.discovered_hubs = await nobo.async_discover_hubs(loop=self.hass.loop)

        errors = {}
        if user_input is not None:
            self.serial = user_input.get(CONF_HOST)
            self.ip = user_input.get(CONF_IP_ADDRESS)
            # TODO: Validate user input

            test_ip = self.ip
            if test_ip is None:
                for (ip, serial) in self.discovered_hubs:
                    if self.serial.startswith(serial):
                        test_ip = ip
                        break
            if test_ip is None:
                errors["base"] = "no_devices_found"
            else:
                # Test connection
                hub = nobo(
                    serial=self.serial,
                    ip=test_ip,
                    discover=False,
                    loop=self.hass.loop)
                await hub.async_connect_hub(ip=test_ip, serial=self.serial)
                self.name = hub.hub_info['name']
                await hub.close()

                await self.async_set_unique_id(self.serial, raise_on_progress=False)
                return await self.async_step_confirm()

        default_suggestion = self._prefill_identifier()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_HOST, default=default_suggestion): str, vol.Optional(CONF_IP_ADDRESS): str}),
            errors=errors,
            description_placeholders={"devices": self._devices_str()}
        )

    async def async_step_confirm(self, user_input=None):
        """Handle user-confirmation of discovered hub."""
        if user_input is not None:
            data = {
                CONF_HOST: self.serial,
                CONF_IP_ADDRESS: self.ip,
                CONF_NAME: self.name
            }
            self._abort_if_unique_id_configured(reload_on_update=False, updates=data)
            return self.async_create_entry(title=self.name, data=data)

        return self.async_show_form(
            step_id="confirm", description_placeholders={"name": self.name, "serial": self.serial}
        )

    def _devices_str(self):
        return ", ".join(
            [
                f"`{serial}XXX ({ip})`"
                for (ip, serial) in self.discovered_hubs
            ]
        )

    def _prefill_identifier(self):
        for (ip, serial) in self.discovered_hubs:
            return serial + "XXX"
        return ""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""

        hub = self.hass.data[DOMAIN][self.config_entry.entry_id]

        if user_input is not None:
            off_command = "" \
                if user_input.get(CONF_COMMAND_OFF) == "Default" \
                else user_input.get(CONF_COMMAND_OFF)

            on_commands = {}
            for k, v in user_input.items():
                if k.startswith(CONF_COMMAND_ON + "_zone_") and v != "Default":
                    zone = k.removeprefix(CONF_COMMAND_ON + "_zone_")
                    on_commands[hub.zones[zone]["name"].replace(u'\xa0', u' ')] = v

            data = {
                CONF_COMMAND_OFF: off_command,
                CONF_COMMAND_ON: on_commands
            }

            return self.async_create_entry(title="", data=data)

        off_command = self.config_entry.options.get(CONF_COMMAND_OFF)
        on_commands = self.config_entry.options.get(CONF_COMMAND_ON)

        profileNames = [k["name"].replace(u'\xa0', ' ') for k in hub.week_profiles.values()]
        profileNames.insert(0, "")
        profiles = vol.Schema(vol.In(profileNames))

        schema = vol.Schema({
            vol.Optional(CONF_COMMAND_OFF, default=off_command): profiles,
        })

        placeholder = ""
        for zone in hub.zones:
            name = hub.zones[zone]["name"].replace(u'\xa0', u' ')
            on_command = on_commands[name] if name in on_commands else ""
            schema = schema.extend({vol.Optional(CONF_COMMAND_ON + "_zone_" + zone, default=on_command): profiles})
            placeholder += zone + ": " + name + "\r"

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={"zones": placeholder}
        )
