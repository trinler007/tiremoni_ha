<!--
SPDX-FileCopyrightText: 2026 Markus Trinler
SPDX-License-Identifier: GPL-3.0-or-later
-->

# TireMoni HA Copyright and Third-Party Notices

## Project contributions

Copyright (c) 2026 Markus Trinler.

The project contributions, including the Home Assistant integration, tests,
documentation, configuration, translations and project artwork contributions,
are licensed under the GNU General Public License, version 3 or, at your
option, any later version (SPDX: `GPL-3.0-or-later`). This statement applies
to the repository files unless a file carries a different notice. Existing
third-party rights and the license text's own copyright remain with their
respective holders.

TireMoni HA is distributed WITHOUT ANY WARRANTY, including implied warranties
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the accompanying
[LICENSE](LICENSE) for the complete terms.

Python and other comment-capable source files carry SPDX notices. JSON and PNG
files have adjacent `.license` files so the same information is available
without altering their formats. Keep those notices with redistributed copies.

## TireMoni decoder by Markus Trinler

Markus Trinler developed and extended the TireMoni decoder for his own local
adaptation of OpenMQTTGateway 1.8.1. The TireMoni notification reassembly,
frame decoding, protocol constants and BLE start-command sequence were his
additions, not original functions supplied by the OpenMQTTGateway project.
The reference implementation was `main/ZsensorBLETireMoniConnect.cpp` and its
header in that adaptation.

His TireMoni-specific implementation was subsequently ported to Python in
`parser.py`, `const.py` and `client.py` for this integration. The Python port
replaces the Arduino/NimBLE and MQTT interfaces with Home Assistant's
Bluetooth APIs and entities, and retains his TireMoni frame mapping and
pressure calibration. The initial Python integration was committed on
2026-07-04. On 2026-10-14 Markus Trinler added explicit licensing and copyright
notices in version 0.5.0; version 0.6.0 clarifies decoder authorship and adds
HACS installation support.

The local `reference/` source trees are not distributed in this repository.
All source needed for this Python integration is included in the repository.

## Original OpenMQTTGateway project

Upstream project: [OpenMQTTGateway](https://github.com/1technophile/OpenMQTTGateway/tree/v1.8.1).
The original release includes the [GNU GPL version 3 license text](https://github.com/1technophile/OpenMQTTGateway/blob/v1.8.1/LICENSE.txt).
Its [Bluetooth gateway source](https://github.com/1technophile/OpenMQTTGateway/blob/v1.8.1/main/ZgatewayBT.ino)
carries the following original attribution:

> Copyright: (c)Florian ROBERT

That source permits redistribution and modification under GPL version 3 or
any later version, without warranty. This attribution acknowledges the
upstream gateway project; it does not claim that its authors wrote the
TireMoni-specific additions or this Home Assistant integration.

## Runtime dependencies

These projects are imported at runtime, not vendored into this repository.
They retain their own copyrights and license terms; the TireMoni HA license
does not relicense them:

| Project | Upstream license |
| --- | --- |
| Home Assistant Core | [Apache-2.0](https://github.com/home-assistant/core/blob/dev/LICENSE.md) |
| Bleak | [MIT](https://github.com/hbldh/bleak/blob/develop/LICENSE) |
| bleak-retry-connector | [MIT](https://github.com/Bluetooth-Devices/bleak-retry-connector/blob/main/LICENSE) |
| Voluptuous | [BSD-3-Clause](https://github.com/alecthomas/voluptuous/blob/master/COPYING) |

## Artwork and trademarks

The current tyre-and-pressure-gauge integration icons were created for this
project with AI assistance. They contain no manufacturer or Bluetooth logos.
The original full-resolution PNG is included as `brand/icon-source.png`.

The previous icon, retained in the repository's commit history, contained a
Bluetooth symbol. The Bluetooth word mark and logos are registered trademarks
owned by Bluetooth SIG, Inc. The project license grants no rights to
third-party trademarks and does not assert ownership of that symbol.

TireMoni, TireDog, TyreDog, Home Assistant and other product or project names
belong to their respective owners. They are used to identify compatibility
or acknowledge upstream work. This is an independent community integration;
no manufacturer, Bluetooth SIG or Home Assistant endorsement is implied.
