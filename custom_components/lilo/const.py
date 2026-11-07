"""Constants for the Lilo integration."""

from datetime import timedelta

DOMAIN = "lilo"

MANUFACTURER = "Prêt à Pousser"
MODEL = "Lilo"

# The daily refresh runs this long after the light turns on or off (option
# below), when the LED blink caused by the connection goes unnoticed.
DAILY_REFRESH_DELAY = timedelta(minutes=1)

CONF_REFRESH_AT = "refresh_at"
REFRESH_AT_START = "start"
REFRESH_AT_END = "end"
DEFAULT_REFRESH_AT = REFRESH_AT_END

# Default brightness used when the light is turned on without a brightness
# and no previous non-zero brightness is known.
DEFAULT_BRIGHTNESS = 100
