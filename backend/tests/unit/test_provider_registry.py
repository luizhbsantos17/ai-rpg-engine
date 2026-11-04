import pytest

from app.config import ConfigError, load_settings
from app.providers import ModelNotFoundError
from app.providers.fake import FakeProvider
from app.providers.ollama import OllamaProvider
from app.providers.registry import build_provider, generation_options, resolve_model


def settings_with(**env):
    return load_settings(environ=env, env_file=None)


def test_default_provider_is_ollama():
    provider = build_provider(settings_with())
    assert isinstance(provider, OllamaProvider)
    assert provider.base_url == "http://localhost:11434"


def test_fake_provider_only_allowed_in_tests():
    assert isinstance(build_provider(settings_with(APP_ENV="test", AI_PROVIDER="fake")), FakeProvider)
    with pytest.raises(ConfigError, match="testes"):
        settings_with(APP_ENV="development", AI_PROVIDER="fake")


def test_unknown_provider_rejected():
    with pytest.raises(ConfigError, match="AI_PROVIDER"):
        settings_with(AI_PROVIDER="magia")


@pytest.mark.parametrize(
    "name,value",
    [("AI_TEMPERATURE", "quente"), ("AI_TEMPERATURE", "5"), ("AI_MAX_OUTPUT_TOKENS", "1.5"),
     ("AI_CONTEXT_WINDOW", "10"), ("AI_TIMEOUT_SECONDS", "nan")],
)
def test_invalid_ai_numbers_rejected(name, value):
    with pytest.raises(ConfigError, match=name):
        settings_with(**{name: value})


def test_resolve_model_prefers_configured_then_first_installed():
    provider = FakeProvider()
    assert resolve_model(provider, "escolhido") == "escolhido"
    assert resolve_model(provider, None) == "fake-model"


def test_resolve_model_without_installed_models():
    class Empty(FakeProvider):
        def list_models(self):
            return []

    with pytest.raises(ModelNotFoundError, match="ollama pull"):
        resolve_model(Empty(), None)


def test_generation_options_come_from_settings():
    options = generation_options(settings_with(AI_TEMPERATURE="0.3", AI_CONTEXT_WINDOW="4096"), "m")
    assert (options.model, options.temperature, options.context_window) == ("m", 0.3, 4096)
    assert options.max_output_tokens == 1024
