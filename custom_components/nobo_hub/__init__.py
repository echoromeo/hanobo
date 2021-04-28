"""The Nobø Ecohub platform."""
from __future__ import annotations

import asyncio
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

#from pynobo import nobo
from .pynobo import nobo

from . import config_flow
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate"]

#CONFIG_SCHEMA = vol.Schema(
#    {
#        DOMAIN: vol.Schema(
#            {
#                vol.Required(CONF_HOST): cv.string,
#                vol.Optional(CONF_IP_ADDRESS): cv.string,
#            }
#        )
#    }
#)
#
#async def async_setup(hass, config):
#    """Set up Nobø Ecohub components."""
#    _LOGGER.info(config)
#    if DOMAIN not in config:
#        return True
#
#    conf = config[DOMAIN]
#
#    config_flow.register_flow_implementation(
#        hass, conf.get(CONF_HOST), conf.get(CONF_IP_ADDRESS)
#    )
#
#    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Nobø Ecohub from a config entry."""

    serial = config_entry.data.get(CONF_HOST)
    ip = config_entry.data.get(CONF_IP_ADDRESS)
    ip = None if ip == "discover" else ip
    discover = ip is None
    hub = nobo(serial=serial, ip=ip, discover=discover, loop=hass.loop)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = hub

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def options_update_listener(
        hass: HomeAssistant, config_entry: ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
