"""Constants for the Lilo integration."""

from datetime import timedelta

DOMAIN = "lilo"

MANUFACTURER = "Prêt à Pousser"
MODEL = "Lilo"

# The daily refresh runs this long after the light turns off, so the LED blink
# caused by the connection goes unnoticed.
DAILY_REFRESH_DELAY = timedelta(minutes=1)

# Default brightness used when the light is turned on without a brightness
# and no previous non-zero brightness is known.
DEFAULT_BRIGHTNESS = 100
