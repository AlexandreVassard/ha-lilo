"""Constants for the Lilo integration."""

from datetime import timedelta

DOMAIN = "lilo"

MANUFACTURER = "Prêt à Pousser"
MODEL = "Lilo"

UPDATE_INTERVAL = timedelta(minutes=5)

# Default brightness used when the light is turned on without a brightness
# and no previous non-zero brightness is known.
DEFAULT_BRIGHTNESS = 100
