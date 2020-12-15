# hanobo

## Introduction
Home Assistant implementation of [pynobo][pypi] as a climate component

As for now you can see and change Operation and Preset for Zones and set eco/comfort temperatures if you have a supported thermostat.

The possible Operation modes are as following:
* Auto - In this mode the Zone is in the Normal setting and Preset shows which state the Zone is in right now (according to calendar setup)
* Heat - In this mode the Zone in in the Override setting and in the state selected by Preset (Away, Eco, Comfort)
* Off - In this mode the Zone is in the Normal setting and will get a specially configured week program that turns off the heater (more info below) 

This can be utilized the following ways:
* Changing Preset to [Away, Eco, Comfort] will automatically change Operation to Heat
* Changing Preset to None will automatically change Operation to Auto and update Preset
* Changing Operation to Auto will automatically update Preset
* Changing Operation to Heat will set Preset to Comfort

## There is no override in Nobø for "completely off", but there is a workaround

Nobø heaters can normally not be set to override "off". This is not a limitation in [pynobo][pypi], but a safety-mechanism in the Nobø system (maybe they don't want you to accidentally turn off all your heaters and get frozen pipes). However, it is possible to create a week profile that makes the heater "off" all the time. And then you can configure the system to switch a heater to this week profile to be able to turn the heater off.

If you tell hanobo the name of the "Off" week profile and the name for the normal ("On") week profile for your zones, you can use this module to turn off (and on) your heaters. The week profiles must already exist in your Nobø system. Use the Nobø app to create them and configure them correctly.

If you don't configure any `command_off` or `command_on` then turning off heaters will not be supported (and this may be fine for your use).

## How to use

To get started with this superexperimental implementation:

* Clone or download the project to [HA config path]/custom_components/nobo_hub:
* Add the following to your Home Assistant configuration file:

      # Nobø Energy Control
      climate: 
        - platform: nobo_hub
          host: [your nobø serial] # You can use the 3 last digits if using discovery
      #    ip_address: [your nobø ip] # Uncomment if you do not want discovery
          # command_off is the name of a week profile (that must exist in the Nobø system) that shall be used to turn off a heater in any zone:
          command_off: Off all the time
          # command_on is a dictionary (a list) on the form "zone name:week profile name" that shall be used to turn on a heater in different zones:
          command_on:
            Bedroom: Cold at night
            Living room: Normal daily comfort


* Restart Home Assistant, you will get this warning:

      WARNING (MainThread) [homeassistant.loader] You are using a custom component for nobo_hub.climate which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you do experience issues with Home Assistant.

* Play around and figure out what does not work..

* If you want some more logging info, add this to your Home Assistant configuration file:

      # Extra logging
      logger:
        default: warning
        logs:
          custom_components.nobo_hub.climate: debug

[pypi]: https://pypi.org/project/pynobo/
