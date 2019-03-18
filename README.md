# hanobo
Home Assistant implementation of pynobo as a climate component

As for now you can see and change state and set eco/comfort temperatures if you have a supported thermostat.

The possible states are as following:
* Normal (state) - Zone is following the configured calendar and currently in 'state'
* Locked (state) - Same as above, but overrides are not allowed
* state - Zone is overridden to 'state'

To get started with this superexperimental implementation:

* git clone the repo as [your HA folder]/custom_components/nobo_hub
  * you can download the zip as well, but then you have to download pynobo as well and unzip it to [your HA folder]/custom_components/nobo_hub/pynobo.
* Add the following to your Home Assistant configuration file:

      # Nobø Energy Control
      climate: 
      - platform: nobo_hub
          host: [your nobø serial] # You can use the 3 last digits if using discovery
      #    ip_address: [your nobø ip] # Uncomment if you do not want discovery

* Restart Home Assistant, you will get this warning:

      WARNING (MainThread) [homeassistant.loader] You are using a custom component for nobo_hub.climate which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you do experience issues with Home Assistant.

* Play around and figure out what does not work..

* If you want some more logging info, add this to your Home Assistant configuration file:

      # Extra logging
      logger:
        default: warning
        logs:
          custom_components.nobo_hub.climate: debug