import pytest


@pytest.mark.parametrize('status,expected',[(401,'API key'),(403,'permission'),(404,'model'),(429,'quota'),(400,'request')])
def test_hosted_errors_explain_status_without_leaking_payload(status,expected):
    from campaign_hub.generation.providers import hosted_error_message
    error=RuntimeError('gsk_secret_key and private request text')
    error.status_code=status
    message=hosted_error_message(error)
    assert expected in message
    assert str(status) in message
    assert 'gsk_' not in message and 'private request' not in message
