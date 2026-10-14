# SPDX-FileCopyrightText: 2026 Markus Trinler
# SPDX-License-Identifier: GPL-3.0-or-later
# Protocol constants from Markus Trinler's own TireMoni extension for
# OpenMQTTGateway 1.8.1, not from upstream. See NOTICE.md for provenance.

"""Constants for the TireMoni BLE integration."""

DOMAIN = "tiremoni_ble"
INTEGRATION_VERSION = "0.6.0"

BRAND_NAME = "TireMoni"
MANUFACTURER = "TireMoni / TireDog / TyreDog"

DEFAULT_POLL_INTERVAL_SECONDS = 30
DEFAULT_NOTIFICATION_HOLD_SECONDS = 15
DEFAULT_PRESSURE_SCALE = 0.9047
DEFAULT_PRESSURE_OFFSET_PSI = 0.0
DEFAULT_MAX_DATA_AGE_MINUTES = 60

CONF_MAX_DATA_AGE_MINUTES = "max_data_age_minutes"

TIREMONI_NUS_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
TIREMONI_NUS_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
TIREMONI_NUS_TX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
TIREMONI_START_COMMAND = b"$A0240138#"

GATEWAY_RSSI_KEY = "gateway_rssi"
PRESSURE_KEY = "pressure"
TEMPERATURE_KEY = "temperature"
BATTERY_PERCENT_KEY = "battery_percent"
STATUS_KEY = "status"
DATA_CURRENT_KEY = "data_current"
