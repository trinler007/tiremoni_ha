<!--
SPDX-FileCopyrightText: 2026 Markus Trinler
SPDX-License-Identifier: GPL-3.0-or-later
-->

# TireMoni HA

Author: Markus Trinler
Version: 0.6.0

Custom Home Assistant integration for TireMoni / TireDog / TyreDog
RF-to-Bluetooth tyre monitoring gateways.

The TireMoni gateway exposes values through a connectable Nordic UART Service
(NUS). The integration connects to the gateway, subscribes to notifications,
writes the start command used by the TireMoni/TyreDog app, and decodes the
returned `$A0...#` tyre frames.

The TireMoni decoder was developed and extended by Markus Trinler for his
own adaptation of OpenMQTTGateway 1.8.1, then ported to Python for this
integration. It is not an original OpenMQTTGateway feature.

## Current status

This repository contains a native Home Assistant custom integration with:

- Config flow and Bluetooth discovery for TireMoni / TireDog / TyreDog gateways
- Active BLE polling of the NUS service using Markus Trinler's TireMoni decoder
- Dynamic sensor creation for tyre pressure, temperature, battery, status and
  gateway RSSI
- A `Data current` binary sensor that turns off when known tyre readings are
  older than the configured freshness limit
- A protocol parser module that is intentionally isolated from Home Assistant
  imports
- Parser tests for frame decoding and notification-fragment reassembly

## Installation

### HACS (recommended)

Prerequisite: [HACS is installed and configured](https://www.hacs.xyz/docs/use/).

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=trinler007&repository=tiremoni_ha&category=integration)

1. Click **Open in HACS** above and confirm adding the repository. This opens
   HACS in your Home Assistant instance.
2. Open **TireMoni HA**, select **Download**, and choose the latest stable release.
3. Restart Home Assistant.
4. Add the integration as described under **Set up the gateway** below.

Alternatively, add the repository manually in HACS:

1. Open **HACS**, then the three-dot menu and **Custom repositories**
   (**Benutzerdefinierte Repositories**).
2. Enter `https://github.com/trinler007/tiremoni_ha` and select type
   **Integration**.
3. Click **Add**, search for **TireMoni HA**, and download it.
4. Restart Home Assistant, then set up the gateway below.

This repository is available as a custom repository; it is not currently part
of the HACS default catalog. No MQTT broker or OpenMQTTGateway installation
is required. See the [official HACS custom repository instructions](https://www.hacs.xyz/docs/faq/custom_repositories/)
for more detail.

HACS uses the [published GitHub releases](https://github.com/trinler007/tiremoni_ha/releases)
to offer versioned downloads and updates. Install future updates through HACS,
then restart Home Assistant. When switching from a manual installation, keep
the existing integration entry: the domain remains `tiremoni_ble`, so the
configured gateway and entity IDs are preserved.

### Manual installation

Download the source archive from the [latest release](https://github.com/trinler007/tiremoni_ha/releases/latest).
Extract it and copy the complete `custom_components/tiremoni_ble` folder into
your Home Assistant `config/custom_components/` directory, including `LICENSE`,
`NOTICE.md`, translations and brand images. Restart Home Assistant.

### Set up the gateway

[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tiremoni_ble)

Click **Add integration** above, or open:

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

Markus Trinler's TireMoni extension established this flow:

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

The **Validate HACS** GitHub Actions workflow checks HACS compatibility on
pushes and pull requests. For a release, update the minor version consistently
in `manifest.json`, `const.py` and this README, then publish a GitHub release
whose tag matches the integration version (for example, `v0.6.0`). HACS
downloads the integration directory directly; no separate ZIP asset is needed.

## Copyright and license

Copyright (c) 2026 Markus Trinler for the project contributions.

TireMoni HA is free software, released under the GNU General Public License,
version 3 or, at your option, any later version (`GPL-3.0-or-later`). You may
use, modify and redistribute it under that license. Redistributed modified
versions must preserve the applicable notices and provide source code under
the GPL. The software comes WITHOUT ANY WARRANTY, including implied warranties
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See [LICENSE](LICENSE)
for the full terms.

The TireMoni decoder is Markus Trinler's own extension, originally developed
for his adaptation of OpenMQTTGateway 1.8.1 and then ported to this integration.
It was not supplied by the upstream OpenMQTTGateway project.
See the [copyright and third-party notices](
custom_components/tiremoni_ble/NOTICE.md) for the upstream attribution,
modification history, dependency licenses and trademark information. The
integration directory also includes a full license copy so these notices
remain available after installation.

This is an independent community integration. Product names identify
compatibility and do not imply endorsement by the manufacturers or by
Home Assistant.
