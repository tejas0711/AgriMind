from types import SimpleNamespace

import pytest

from app.services import llm_service


@pytest.mark.asyncio
async def test_uses_gemini_when_openai_request_fails(monkeypatch):
    calls = []
    client_retries = []

    class FakeCompletions:
        def __init__(self, api_key):
            self.api_key = api_key

        async def create(self, **kwargs):
            calls.append((self.api_key, kwargs["model"]))
            if self.api_key == "openai-key":
                raise RuntimeError("OpenAI unavailable")
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Gemini explanation"))]
            )

    class FakeClient:
        def __init__(self, api_key, base_url=None, timeout=None, max_retries=None):
            client_retries.append(max_retries)
            self.chat = SimpleNamespace(completions=FakeCompletions(api_key))

    monkeypatch.setattr("openai.AsyncOpenAI", FakeClient)
    monkeypatch.setattr(llm_service, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(llm_service, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm_service, "_build_context", lambda *args: "soil facts")

    result = await llm_service.generate_explanation(None, [], [], [], None, [])

    assert result == "Gemini explanation"
    assert calls == [
        ("openai-key", llm_service.OPENAI_MODEL),
        ("gemini-key", llm_service.GEMINI_MODEL),
    ]
    assert client_retries == [0, 0]


@pytest.mark.asyncio
async def test_uses_openrouter_when_openai_and_gemini_fail(monkeypatch):
    calls = []

    class FakeCompletions:
        def __init__(self, api_key):
            self.api_key = api_key

        async def create(self, **kwargs):
            calls.append((self.api_key, kwargs["model"]))
            if self.api_key != "openrouter-key":
                raise RuntimeError("provider unavailable")
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="OpenRouter explanation"))]
            )

    class FakeClient:
        def __init__(self, api_key, base_url=None, timeout=None, max_retries=None):
            calls.append((api_key, base_url))
            self.chat = SimpleNamespace(completions=FakeCompletions(api_key))

    monkeypatch.setattr("openai.AsyncOpenAI", FakeClient)
    monkeypatch.setattr(llm_service, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(llm_service, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm_service, "OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setattr(llm_service, "_build_context", lambda *args: "soil facts")

    result = await llm_service.generate_explanation(None, [], [], [], None, [])

    assert result == "OpenRouter explanation"
    assert ("openrouter-key", llm_service.OPENROUTER_BASE_URL) in calls
    assert ("openrouter-key", llm_service.OPENROUTER_MODEL) in calls


@pytest.mark.asyncio
async def test_retries_temporary_provider_unavailable_once(monkeypatch):
    calls = 0

    class FakeCompletions:
        async def create(self, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                error = RuntimeError("temporary outage")
                error.status_code = 503
                raise error
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Recovered explanation"))]
            )

    class FakeClient:
        def __init__(self, api_key, base_url=None, timeout=None, max_retries=None):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    async def no_wait(_):
        return None

    monkeypatch.setattr("openai.AsyncOpenAI", FakeClient)
    monkeypatch.setattr(llm_service.asyncio, "sleep", no_wait)
    monkeypatch.setattr(llm_service, "OPENAI_API_KEY", None)
    monkeypatch.setattr(llm_service, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm_service, "OPENROUTER_API_KEY", None)
    monkeypatch.setattr(llm_service, "_build_context", lambda *args: "soil facts")

    result = await llm_service.generate_explanation(None, [], [], [], None, [])

    assert result == "Recovered explanation"
    assert calls == 2


@pytest.mark.asyncio
async def test_provider_errors_are_not_shown_in_fallback(monkeypatch):
    class FakeCompletions:
        async def create(self, **kwargs):
            raise RuntimeError("private provider diagnostic")

    class FakeClient:
        def __init__(self, api_key, base_url=None, timeout=None, max_retries=None):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("openai.AsyncOpenAI", FakeClient)
    monkeypatch.setattr(llm_service, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(llm_service, "GEMINI_API_KEY", None)
    monkeypatch.setattr(llm_service, "OPENROUTER_API_KEY", None)
    monkeypatch.setattr(llm_service, "_build_context", lambda *args: "soil facts")

    result = await llm_service.generate_explanation(None, [], [], [], None, [])

    assert "private provider diagnostic" not in result
    assert "natural-language explanation is unavailable" in result
