# SPDX-FileCopyrightText: 2026 Markus Trinler
# SPDX-License-Identifier: GPL-3.0-or-later

"""The TireMoni BLE integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS = ["sensor", "binary_sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TireMoni BLE from a config entry."""
    from homeassistant.const import CONF_ADDRESS

    from .const import INTEGRATION_VERSION
    from .coordinator import TireMoniDataUpdateCoordinator

    _LOGGER.info("Setting up TireMoni HA %s", INTEGRATION_VERSION)

    address = entry.unique_id or entry.data[CONF_ADDRESS]
    entry.runtime_data = coordinator = TireMoniDataUpdateCoordinator(
        hass,
        _LOGGER,
        address,
        entry.title,
    )

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload TireMoni BLE when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
