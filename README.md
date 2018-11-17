# hanobo
Home Assistant implementation of pynobo as a climate component

To get started with this superexperimental implementation:

* Download/clone the repo as [your HA folder]/custom_components/climate
* Add the following to your Home Assistant configuration file:

      # Nobø Energy Control
      climate: 
      - platform: nobo_hub
          host: [your nobø serial]
          ip_address: [your nobø ip]

* Restart Home Assistant, you will get this warning:

      WARNING (MainThread) [homeassistant.loader] You are using a custom component for climate.nobo_hub which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you do experience issues with Home Assistant.

* Play around and figure out what does not work..