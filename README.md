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

* Play around and figure out what does not work..