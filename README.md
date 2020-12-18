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
* Changing Operation to Off will change Preset to Off? and change the week profile to the predefined "completely off" profile

## There is no override in Nobø for "completely off", but there is a workaround

Nobø heaters can normally not be set to override "off". This is not a limitation in [pynobo][pypi], but a safety-mechanism in the Nobø system (maybe they don't want you to accidentally turn off all your heaters and get frozen pipes). However, it is possible to create a week profile that makes the heaters "off" all the time. And then you can configure the system to switch a zone to this week profile to be able to turn the heater(s) off.

If you tell hanobo the name of the "Off" week profile and the name for the normal ("On") week profile for your zones, you can use this module to turn off (and on) your heaters. The week profiles must already exist in your Nobø system, and you need to list the "On" week profile for each zone in the nobo_hub configuration. Use the Nobø app to create them and configure them correctly.

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
      #    command_off: [your completely off week profile name] # Uncomment if you want to enable the completely off setting (bypassing the 7 degrees Away setting)
      #    command_on: # Uncomment these if you want to enable the completely off setting, one line for each zone you want to allow bypassing the 7 degrees Away setting
      #       [zone name:return week profile name] 
      #       [zone name:return week profile name]

* Restart Home Assistant, you will get this warning:

      WARNING (MainThread) [homeassistant.loader] You are using a custom component for nobo_hub.climate which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you do experience issues with Home Assistant.

* Play around and figure out what does not work..

* If you want some more logging info, add this to your Home Assistant configuration file:

      # Extra logging
      logger:
        default: warning
        logs:
          custom_components.nobo_hub.climate: debug

## Tips and Tricks

### Complete Control from Home Assistant

If you want to have Home Assistant control everything, you can just never use Auto and always override the zones with a preset. However, a hot tip is to create week profiles in the Nobø app with one setting used all the time. Configuring one of these profiles for a zone should make the HA automations more predictable, and if something goes wrong you know what the fallback is for each zone.

If you set the week profile for a zone to "Off" all the time you can use the Auto Operation as "Off", and then override it with the Away/Eco/Comfort presets, so that you have all the options. Just remember that if something goes wrong here you might end up with a frozen room/house. 

If you want to go all in on the automation and have thermostats that support configuring the temperature remotely you can just leave the override to Eco or Comfort all the time and only adjust the target temperature. A bit overkill, but that is part of the fun with HA?

### Hybrid Control via Home Assistant

If you have set up sensible week profiles for your zones and only want Home Assistant to override them on certain conditions, the best trick may be to change the override mode to "Now" instead of "Constant". At the moment this selection is not available from HA so you need to go into the code and change it, as described in issue [#14][issue-14].
In the "Constant" override mode you need to have the HA automations return the Operation back to Auto at some time, while the "Now" override mode will return back to Auto the next time the week profile changes preset.

This "hybrid" solution is the mode where you would want to use the "completely off" functionality described earlier in the readme. In this case the Off Operation is acting kind of like Auto, so you will need to have the automation change Operation back to Auto or Heat to switch back to the normal week profile. If not you might end up with a frozen room/house.

### Global Override

Using [groups][ha-groups] you should be able to group together all or some of the zones if you want an easy way to control more than one at the same time, similar to the main buttons in the Nobø App.

      group: 
        - nobo_global:
          name: Global Override
          entities:
            - climate.gang
            - climate.kontor
            - climate.stove
            - climate.soverom

[pypi]: https://pypi.org/project/pynobo/
[ha-groups]: https://www.home-assistant.io/integrations/group/
[issue-14]: https://github.com/echoromeo/hanobo/issues/14
