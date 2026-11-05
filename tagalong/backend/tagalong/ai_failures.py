"""Bounded, payload-free assistant failure diagnostics."""
import logging
from uuid import uuid4
from openai import APIConnectionError, APITimeoutError, APIStatusError

logger=logging.getLogger(__name__)


def assistant_failure(error):
    status=getattr(error,'status_code',None)
    provider_code=getattr(error,'code',None)
    if isinstance(error,APITimeoutError):
        code,explanation='AI_TIMEOUT','The AI service timed out. Please try again shortly.'
    elif isinstance(error,APIConnectionError):
        code,explanation='AI_CONNECTION','The server could not reach the AI service. Please try again shortly.'
    elif isinstance(error,APIStatusError):
        if status in (401,403,404):
            code,explanation='AI_CONFIGURATION','The hosted AI configuration needs administrator attention.'
        elif status==429 and provider_code in ('insufficient_quota','credit_balance_exhausted','billing_hard_limit_reached'):
            code,explanation='AI_QUOTA','The AI service quota needs administrator attention.'
        elif status==429:
            code,explanation='AI_BUSY','The AI service is busy. Wait a minute before trying again.'
        elif status==400:
            code,explanation='AI_REQUEST','The AI service rejected the request. The administrator needs to check the hosted configuration.'
        else:
            code,explanation='AI_UNAVAILABLE','The AI service is unavailable. Please try again shortly.'
    elif isinstance(error,ValueError):
        code,explanation='AI_OUTPUT','The AI reply could not be validated. Please try again.'
    else:
        code,explanation='AI_INTERNAL','The assistant encountered an internal error. Please share this reference with the administrator.'
    incident=uuid4().hex[:12]
    # Never log exception text/body/traceback: SDK errors can contain keys and prompts.
    known_types={'AuthenticationError','PermissionDeniedError','NotFoundError','BadRequestError','RateLimitError','APITimeoutError','APIConnectionError','InternalServerError','APIStatusError','ValidationError','JSONDecodeError','ValueError','KeyError','TypeError','AttributeError','RuntimeError'}
    error_type=type(error).__name__ if type(error).__name__ in known_types else 'UnexpectedError'
    known_codes={'invalid_api_key','insufficient_quota','credit_balance_exhausted','billing_hard_limit_reached','rate_limit_exceeded','model_not_found','invalid_json_schema','unsupported_parameter','invalid_request_error'}
    upstream_code=provider_code if isinstance(provider_code,str) and provider_code in known_codes else 'unclassified'
    logger.warning('assistant_failure category=%s reference=%s error_type=%s upstream_code=%s',code,incident,error_type,upstream_code)
    return f'{explanation} Your existing plan is unchanged. [{code}; reference {incident}]'
