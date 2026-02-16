# tests/unit/test_settings.py
import os, pytest
from unittest.mock import patch

def test_settings_loads_defaults():
    """Settings loads with environment variables."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}):
        from importlib import reload
        import src.config.settings as settings_module
        reload(settings_module)
        s = settings_module.Settings()
        assert s.llm_provider == "gemini"
        assert s.qa_confidence_threshold == 0.85
        assert s.max_judge_iterations == 3
        assert s.team_id == "local_team"

def test_settings_rejects_invalid_provider():
    """Invalid LLM_PROVIDER raises a clear error."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}):
        with pytest.raises(Exception):  # pydantic ValidationError
            from src.config.settings import Settings
            Settings()

def test_settings_bedrock_defaults():
    """Bedrock model defaults are correct."""
    with patch.dict(os.environ, {"LLM_PROVIDER": "bedrock"}):
        from src.config.settings import Settings
        s = Settings()
        assert s.bedrock_model_id == "eu.anthropic.claude-3-5-sonnet-20240620-v1:0"
        assert s.aws_default_region == "eu-west-1"