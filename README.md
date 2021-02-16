# hanobo

## Introduction
Home Assistant implementation of [pynobo][pypi] as a climate component

As for now you can see and change Operation and Preset for Zones and set eco/comfort temperatures if you have a supported thermostat.

The possible Operation modes are as following:
* Auto - In this mode the Zone is in the Normal setting and Preset shows which state the Zone is in right now (according to calendar setup)
* Heat - In this mode the Zone in in the Override setting and in the state selected by Preset (Away, Eco, Comfort)
* Off - In this optional mode the Zone is in the Normal setting and will configure it to use a week profile that turns the heater(s) in the Zone completely off (more info below)

This can be utilized the following ways:
* Changing Preset to [Away, Eco, Comfort] will automatically change Operation to Heat
* Changing Preset to None will automatically change Operation to Auto and update Preset
* Changing Operation to Auto will automatically update Preset
* Changing Operation to Heat will set Preset to Comfort
* Changing Operation to Off will change Operation to Auto and change the week profile to the predefined "completely off" profile

## There is no override in Nobø for "completely off", but there is a workaround

Nobø heaters can normally not be set to override "off". This is not a limitation in [pynobo][pypi], but a safety-mechanism in the Nobø system (maybe they don't want you to accidentally turn off all your heaters and get frozen pipes). However, it is possible to create a week profile that makes the heaters "off" all the time. And then you can configure the system to switch a zone to this week profile to be able to turn the heater(s) off.

If you tell hanobo the name of the "Off" week profile and the name for the normal ("On") week profile for your zones, you can use this module to turn off (and on) your heaters. The week profiles must already exist in your Nobø system, and you need to list the "On" week profile for each zone in the nobo_hub configuration. Use the Nobø app to create them and configure them correctly.

If you don't configure any `command_off` or `command_on` then turning off heaters will not be supported (and this may be fine for your use).

## How to use / Installation

### Automaticly using HACS (Home Assistant Community Store)

1. Go into HACS in the left menu
2. Click Integration
3. Click + (Explore and add repo) - Blue button in bottom right
4. Search for "Nobø"
5. [Update configuration.yaml](#update-configuration)

Or watch gif at [https://hacs.xyz](https://hacs.xyz)

### Or manually
To get started with this superexperimental implementation:

1. Clone or download the project to [HA config path]/custom_components/nobo_hub:
2. [Update configuration.yaml](#update-configuration)

### Update configuration
* Add the following to your Home Assistant configuration file:

      # Nobø Energy Control
      climate: 
        - platform: nobo_hub
          host: [your nobø serial] # You can use the 3 last digits if using discovery
      #    ip_address: [your nobø ip] # Uncomment if you do not want discovery
          # command_off: [your completely off week profile name] # Uncomment if you want to enable the completely off setting (bypassing the 7 degrees Away setting)
          # command_on: # Uncomment these if you want to enable the completely off setting, one line for each zone you want to allow bypassing the 7 degrees Away setting
          #   [zone name:return week profile name] 
          #   [zone name:return week profile name]

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
