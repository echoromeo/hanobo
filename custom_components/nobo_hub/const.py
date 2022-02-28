from homeassistant.const import (
    Platform,
)
DOMAIN = "nobo_hub"
OBJECT_NAME = "Nobø Hub / Nobø Energy Control"
MIN_TEMPERATURE = 7
MAX_TEMPERATURE = 40


PLATFORMS = [
    Platform.CLIMATE,
]
