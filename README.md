# TireMoni HA

Author: Markus Trinler
Version: 0.4.0

Custom Home Assistant integration for TireMoni / TireDog / TyreDog
RF-to-Bluetooth tyre monitoring gateways.

The TireMoni gateway exposes values through a connectable Nordic UART Service
(NUS). The integration connects to the gateway, subscribes to notifications,
writes the start command used by the TireMoni/TyreDog app, and decodes the
returned `$A0...#` tyre frames.

## Current status

This repository contains a native Home Assistant custom component scaffold with:

- Config flow and Bluetooth discovery for TireMoni / TireDog / TyreDog gateways
- Active BLE polling of the NUS service used by the OpenMQTTGateway adaptation
- Dynamic sensor creation for tyre pressure, temperature, battery, status and
  gateway RSSI
- A `Data current` binary sensor that turns off when known tyre readings are
  older than the configured freshness limit
- A protocol parser module that is intentionally isolated from Home Assistant
  imports
- Parser tests for frame decoding and notification-fragment reassembly

## Installation

Copy the `custom_components/tiremoni_ble` folder into your Home Assistant
`config/custom_components/` directory and restart Home Assistant.

Then add the integration through:

`Settings -> Devices & services -> Add integration -> TireMoni HA`

If the gateway advertises as `TYREDOG`, TireMoni, TireDog or TyreDog, Home
Assistant should also offer it automatically via Bluetooth discovery.

## Bluetooth Proxy

The integration requires an active BLE connection. ESPHome Bluetooth Proxies can
be used when they support active connections and are in range of the
TireMoni/TyreDog gateway.

## Reading Freshness

The integration adds one gateway-level binary sensor named `Data current`.
It is on when at least one tyre reading is known and every known tyre reading is
younger than the configured maximum age. The default limit is 60 minutes.

Change the limit through:

`Settings -> Devices & services -> TireMoni HA -> Configure`

The entity attributes include the configured limit, known sensor count, stale
sensor ids, oldest reading age and per-sensor last-seen timestamps.

## Icon

Home Assistant 2026.3 and newer can load local brand images for custom
integrations from `custom_components/tiremoni_ble/brand/`. This integration
includes `icon.png` and `icon@2x.png`.

## Protocol

The decoded frame mapping lives in:

`custom_components/tiremoni_ble/parser.py`

The OpenMQTTGateway adaptation showed this flow:

- Subscribe to NUS TX characteristic `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- Write `$A0240138#` to NUS RX characteristic
  `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
- Reassemble ASCII notification fragments until `#`
- Decode 16-character `$A0...#` frames

Enable debug logging while testing the integration:

```yaml
logger:
  logs:
    custom_components.tiremoni_ble: debug
```

## Development checks

```powershell
python -m unittest discover -s tests
Get-ChildItem -Path custom_components\tiremoni_ble -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```
