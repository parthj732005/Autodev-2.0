from app.agents.base_agent import _extract_status_code, _non_retryable_reason


class FakeStatusError(Exception):
    """Mimics openai/anthropic SDK exceptions that expose .status_code directly."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeHttpxStyleError(Exception):
    """Mimics httpx.HTTPStatusError, which nests status_code under .response."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.response = FakeResponse(status_code)


def test_auth_error_detected_by_status_code():
    exc = FakeStatusError("nope", 401)
    assert _non_retryable_reason(exc) == "auth"


def test_auth_error_detected_by_message_when_no_status_code():
    exc = Exception("AuthenticationError: invalid api key provided")
    assert _non_retryable_reason(exc) == "auth"


def test_model_not_found_error_detected():
    # Real shape returned by Groq for a typo'd model name (verified live).
    exc = FakeStatusError(
        "The model `this-model-does-not-exist-xyz` does not exist or you do not have access to it.",
        404,
    )
    assert _non_retryable_reason(exc) == "model"


def test_decommissioned_model_error_detected():
    # Real shape returned by Groq for mixtral-8x7b-32768 (verified live).
    exc = FakeStatusError(
        "The model `mixtral-8x7b-32768` has been decommissioned and is no longer supported.",
        400,
    )
    assert _non_retryable_reason(exc) == "model"


def test_transient_error_is_retryable():
    exc = Exception("Connection reset by peer")
    assert _non_retryable_reason(exc) is None


def test_rate_limit_error_is_retryable():
    exc = FakeStatusError("Rate limit reached for model", 429)
    assert _non_retryable_reason(exc) is None


def test_extract_status_code_direct_attribute():
    exc = FakeStatusError("boom", 404)
    assert _extract_status_code(exc) == 404


def test_extract_status_code_nested_response_attribute():
    exc = FakeHttpxStyleError("boom", 404)
    assert _extract_status_code(exc) == 404


def test_extract_status_code_none_when_absent():
    assert _extract_status_code(Exception("plain error")) is None
