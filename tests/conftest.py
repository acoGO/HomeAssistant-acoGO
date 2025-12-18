import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.acogo.const import CONF_TOKEN, DOMAIN


@pytest.fixture
def config_entry(hass):
    """Provide a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TOKEN: "token-123", "devices": []},
        entry_id="test-entry",
    )
    entry.add_to_hass(hass)
    return entry
