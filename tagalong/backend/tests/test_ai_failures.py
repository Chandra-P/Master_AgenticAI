import json
import logging
import httpx
import pytest
from openai import AuthenticationError, RateLimitError, APITimeoutError, BadRequestError
from tagalong.ai_failures import assistant_failure


def response(status):
    return httpx.Response(status,request=httpx.Request('POST','https://api.openai.com/v1/responses'))


@pytest.mark.parametrize(('error','code'),[
    (AuthenticationError('SECRET',response=response(401),body={'code':'invalid_api_key'}),'AI_CONFIGURATION'),
    (RateLimitError('SECRET',response=response(429),body={'code':'insufficient_quota'}),'AI_QUOTA'),
    (RateLimitError('SECRET',response=response(429),body={'code':'rate_limit_exceeded'}),'AI_BUSY'),
    (APITimeoutError(request=httpx.Request('POST','https://api.openai.com')),'AI_TIMEOUT'),
    (BadRequestError('SECRET',response=response(400),body={'code':'invalid_json_schema'}),'AI_REQUEST'),
    (BadRequestError('SECRET',response=response(400),body={'code':'SECRET'}),'AI_REQUEST'),
    (json.JSONDecodeError('SECRET','SECRET',0),'AI_OUTPUT'),
    (RuntimeError('SECRET'),'AI_INTERNAL'),
])
def test_failure_identifies_category_without_logging_payload(error,code,caplog):
    with caplog.at_level(logging.WARNING):
        result=assistant_failure(error)
    assert code in result
    assert 'reference ' in result
    assert 'SECRET' not in result+caplog.text
    assert code in caplog.text
    assert 'Your existing plan is unchanged' in result
