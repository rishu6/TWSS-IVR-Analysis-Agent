from unittest.mock import patch
from app.live_sync import LiveSync
from test_internal import internal


def worker(internal):
    return LiveSync(internal.app.state.settings,internal.app.state.sessions)


def test_paused_crm_workers_never_open_provider(internal):
    sync=worker(internal)
    with patch('app.live_sync.load_credentials',return_value={'LEADSQUARED_SYNC_PAUSED':'true'}), patch('app.live_sync.LiveLeadSquaredClient',side_effect=AssertionError('Provider must stay paused')), patch('app.owner_directory.refresh_owner_directory',side_effect=AssertionError('Directory must stay paused')):
        assert sync.run_crm()=={'status':'PAUSED'}
        assert sync.run_matches()=={'status':'PAUSED'}
        sync.crm({'LEADSQUARED_SYNC_PAUSED':'true'})


def test_pause_keeps_call_sync_running(internal):
    sync=worker(internal)
    with patch('app.live_sync.load_credentials',return_value={'LEADSQUARED_SYNC_PAUSED':'true'}), patch('app.history.process_history',return_value=False), patch.object(sync,'telephony') as calls, patch.object(sync,'crm') as crm, patch('app.owner_directory.refresh_owner_directory') as owners, patch('app.maintenance.maintain'):
        assert sync.run()=={'status':'FINISHED'}
        calls.assert_called_once()
        crm.assert_not_called()
        owners.assert_not_called()


def test_pause_can_be_resumed_without_deleting_data(internal):
    sync=worker(internal)
    assert sync.crm_paused({'LEADSQUARED_SYNC_PAUSED':'true'})
    assert not sync.crm_paused({'LEADSQUARED_SYNC_PAUSED':'false'})
