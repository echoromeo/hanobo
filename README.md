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

If you tell hanobo the name of the "off" week profile and the name for the normal ("on") week profile for your zones, you can use this module to turn off (and on) your heaters. The week profiles must already exist in your Nobø system, and you need to list the "On" week profile for each zone in the Nobø Ecohub configuration. Use the Nobø app to create them and configure them correctly.

If you don't configure any "off" or "on" week profiles, then turning off heaters will not be supported (and this may be fine for your use).

## How to use / Installation

### Automatically using HACS (Home Assistant Community Store)

1. Go into HACS in the left menu
2. Click Integration
3. Click + (Explore and add repo) - Blue button in bottom right
4. Search for "Nobø"

Or watch gif at [https://hacs.xyz](https://hacs.xyz)

### Or manually
To get started with this superexperimental implementation:

1. Clone or download the project to [HA config path]/custom_components/nobo_hub:
2. Go to directory - `cd [HA config path]/custom_components/nobo_hub`
3. Move files - `mv custom_components/* .`

### Configuration
* Restart Home Assistant, you will get this warning:

      WARNING (MainThread) [homeassistant.loader] You are using a custom component for nobo_hub.climate which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you do experience issues with Home Assistant.

* You can now add "Nobø Ecohub" as an integration in the Home Assistant UI.
  * Week profiles for "off" and "on" settings are set as options in the UI using the "Configure" button on the integration.
  
* Play around and figure out what does not work..

* If you want some more logging info, add this to your Home Assistant configuration file:

      # Extra logging
      logger:
        default: warning
        logs:
          custom_components.nobo_hub.climate: debug
          pynobo: debug

#### Importing from `configuration.yaml`

If you have previously configured `nobo_hub` in `configuration.yaml` you will see the following warnings in the log:

    WARNING (MainThread) [custom_components.nobo_hub.climate] Loading Nobø Ecohub via platform setup is depreciated; Please remove it from your configuration
    WARNING (MainThread) [custom_components.nobo_hub.climate] Importing Nobø Ecohub configuration from configuration.yaml

Verify that the configuration is successfully imported by going to "Configuration" -> "Integrations" in the Home Assistant UI.
There you should see your Nobø Ecohub. Go to "Configure" to verify the off and on commands.
You may now remove the configuration from configuration.yaml. No restart is required.

[pypi]: https://pypi.org/project/pynobo/
