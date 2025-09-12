import os

# Ensure OpenAI key is set before importing settings
os.environ["OPENAI_API_KEY"] = "test-key"

import pytest
from unittest.mock import AsyncMock, Mock

from hermes.mcp.documentation_generator import DocumentationGenerator
from hermes.config import settings


@pytest.mark.asyncio
async def test_translate_to_american_english():
    settings.openai_api_key = "test-key"
    generator = DocumentationGenerator()
    mock_response = Mock()
    mock_response.output_text = "Hello world"

    generator._openai_client = Mock()
    generator._openai_client.responses.create = AsyncMock(return_value=mock_response)

    result = await generator._translate_to_american_english("Hola mundo")
    assert result == "Hello world"
    generator._openai_client.responses.create.assert_called_once()
