import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('integration_setup', Path(__file__).resolve().parents[1] / 'scripts/check_integration_config.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def test_empty_configuration_does_not_enable_live_mode():
    status = setup.check({})
    assert not status['ready_for_account_validation']
    assert not status['live_dashboard_enabled']


def test_config_check_never_exposes_credentials():
    values = {key: 'sensitive-test-value' for key in setup.KEYS}
    values['LEADSQUARED_API_HOST'] = 'https://api-in21.leadsquared.com/v2/'
    status = setup.check(values)
    assert status['ready_for_account_validation']
    assert not status['credentials_verified']
    assert 'sensitive-test-value' not in json.dumps(status)


@pytest.mark.parametrize('host', ['http://api-in21.leadsquared.com', 'https://leadsquared.com.attacker.test',
                                  'https://key@api-in21.leadsquared.com', 'https://api-in21.leadsquared.com/?secret=key'])
def test_invalid_hosts_are_rejected(host):
    assert not setup.valid_host(host)


def test_file_is_parsed_without_shell_execution(tmp_path):
    path = tmp_path / 'config'
    path.write_text("ACEFONE_API_TOKEN='$(never-execute)'\nLEADSQUARED_ACCESS_KEY=abc # comment\n")
    values = setup.read_config(path)
    assert values['ACEFONE_API_TOKEN'] == '$(never-execute)'
    assert values['LEADSQUARED_ACCESS_KEY'] == 'abc'
