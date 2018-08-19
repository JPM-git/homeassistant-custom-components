"""Support for EDP re:dy plugs/switches."""
import logging

try:
    from homeassistant.components.edp_redy import EdpRedyDevice, EDP_REDY
except ImportError:
    from custom_components.edp_redy import EdpRedyDevice, EDP_REDY

from homeassistant.components.switch import SwitchDevice

_LOGGER = logging.getLogger(__name__)

# Load power in watts (W)
ATTR_ACTIVE_POWER = 'active_power'

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Xiaomi devices."""
    session = hass.data[EDP_REDY]
    devices = []
    for device_pkid, device_json in session.modules_dict.items():
        if "HA_SWITCH" not in device_json["Capabilities"]:
            continue
        devices.append(EdpRedySwitch(session, device_json))

    add_devices(devices)


class EdpRedySwitch(EdpRedyDevice, SwitchDevice):
    """Representation of a Edp re:dy plug."""

    def __init__(self, session, device_json):
        """Initialize the switch."""
        self._active_power = None
        self._supports_power_consumption = False

        EdpRedyDevice.__init__(self, session, device_json)

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return 'mdi:power-plug'

    @property
    def is_on(self):
        """Return true if it is on."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if self._supports_power_consumption:
            attrs = {ATTR_ACTIVE_POWER: self._active_power}
        else:
            attrs = {}
        attrs.update(super().device_state_attributes)
        return attrs

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if await self._async_send_state_cmd(True):
            self._state = True
            self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if await self._async_send_state_cmd(False):
            self._state = False
            self.schedule_update_ha_state()

    async def _async_send_state_cmd(self, state):
        state_json = {"devModuleId": self._id, "key": "RelayState",
                      "value": state}
        return await self._session.async_set_state_var(state_json)

    def _data_updated(self):
        device_json = self._session.modules_dict[self._id]
        self._parse_data(device_json)
        super()._data_updated()

    def _parse_data(self, data):
        """Parse data received from the server."""

        _LOGGER.debug("Switch data: " + str(data))

        # self._supports_power_consumption = any(
        #     key in data["Capabilities"] for key in
        #     ['HA_CONSUMPTION_METER', 'HA_ENERGY_METER', 'HA_POWER_METER'])

        for state_var in data["StateVars"]:
            if state_var["Name"] == "RelayState":
                self._state = True if state_var["Value"] == "true" \
                    else False
            elif state_var["Name"] == "ActivePower":
                self._active_power = state_var["Value"]
                self._supports_power_consumption = True