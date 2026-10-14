# SPDX-FileCopyrightText: 2026 Markus Trinler
# SPDX-License-Identifier: GPL-3.0-or-later

"""Config flow for TireMoni BLE."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import CONF_MAX_DATA_AGE_MINUTES, DEFAULT_MAX_DATA_AGE_MINUTES, DOMAIN
from .parser import is_likely_tiremoni_service_info

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_MAX_DATA_AGE_MINUTES,
            default=DEFAULT_MAX_DATA_AGE_MINUTES,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440))
    }
)


def _normalize_address(address: str) -> str:
    """Normalize a Bluetooth address for use as a unique id."""
    return address.strip().upper()


def _title_from_service_info(service_info: BluetoothServiceInfoBleak) -> str:
    """Build a friendly title for a discovered gateway."""
    name = service_info.name or service_info.address
    return f"{name} ({service_info.address})"


class TireMoniConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TireMoni BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return TireMoniOptionsFlowHandler()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle Bluetooth discovery."""
        await self.async_set_unique_id(_normalize_address(discovery_info.address))
        self._abort_if_unique_id_configured()

        if not is_likely_tiremoni_service_info(discovery_info):
            return self.async_abort(reason="not_supported")

        self._discovery_info = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a Bluetooth discovered gateway."""
        assert self._discovery_info is not None

        title = _title_from_service_info(self._discovery_info)
        if user_input is not None:
            return self.async_create_entry(
                title=title,
                data={CONF_ADDRESS: _normalize_address(self._discovery_info.address)},
            )

        self._set_confirm_only()
        self.context["title_placeholders"] = {"name": title}
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": title},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup."""
        if user_input is not None:
            address = _normalize_address(user_input[CONF_ADDRESS])
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            if service_info := self._discovered_devices.get(address):
                title = _title_from_service_info(service_info)
            else:
                title = f"TireMoni BLE ({address})"

            return self.async_create_entry(
                title=title,
                data={CONF_ADDRESS: address},
            )

        current_addresses = self._async_current_ids(include_ignore=False)
        matched_devices: dict[str, BluetoothServiceInfoBleak] = {}
        fallback_devices: dict[str, BluetoothServiceInfoBleak] = {}

        for discovery_info in async_discovered_service_info(
            self.hass, connectable=True
        ):
            address = _normalize_address(discovery_info.address)
            if address in current_addresses or address in matched_devices:
                continue

            if is_likely_tiremoni_service_info(discovery_info):
                matched_devices[address] = discovery_info
            elif discovery_info.name:
                fallback_devices[address] = discovery_info

        self._discovered_devices = matched_devices or fallback_devices

        if self._discovered_devices:
            address_options = {
                address: _title_from_service_info(service_info)
                for address, service_info in self._discovered_devices.items()
            }
            schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(address_options)})
        else:
            schema = vol.Schema({vol.Required(CONF_ADDRESS): str})

        return self.async_show_form(step_id="user", data_schema=schema)


class TireMoniOptionsFlowHandler(OptionsFlow):
    """Handle TireMoni BLE options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage TireMoni BLE options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                self.config_entry.options,
            ),
        )
