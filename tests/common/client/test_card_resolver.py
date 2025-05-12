import pytest
import httpx
import json
from unittest.mock import Mock, patch

from pydantic import ValidationError

from common.client import A2ACardResolver
from common.types import A2AClientJSONError, AgentCard  # Replace with actual import path


class TestA2ACardResolver:
    def test_init_base_url_trailing_slash(self):
        """Test initialization with trailing slash in base URL"""
        resolver = A2ACardResolver('https://example.com/')
        assert resolver.base_url == 'https://example.com'
        assert resolver.agent_card_path == '.well-known/agent.json'

    def test_init_base_url_no_trailing_slash(self):
        """Test initialization without trailing slash in base URL"""
        resolver = A2ACardResolver('https://example.com')
        assert resolver.base_url == 'https://example.com'
        assert resolver.agent_card_path == '.well-known/agent.json'

    def test_init_custom_agent_card_path(self):
        """Test initialization with custom agent card path"""
        resolver = A2ACardResolver('https://example.com', agent_card_path='custom/path/agent.json')
        assert resolver.base_url == 'https://example.com'
        assert resolver.agent_card_path == 'custom/path/agent.json'

    def test_get_agent_card_success(self):
        """Test successful agent card retrieval"""
        # Prepare mock response data
        mock_agent_card_data = {
            "version": "0.0.1",
            "name": "Test Agent",
            "url": "https://example.com",
            "capabilities": {},
            "skills": []
        }

        # Create a mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_agent_card_data
        mock_response.raise_for_status = Mock()

        # Patch httpx.Client to return our mock response
        with patch('httpx.Client.get', return_value=mock_response) as mock_get:
            resolver = A2ACardResolver('https://example.com/')
            agent_card = resolver.get_agent_card()

            # Verify the method call
            mock_get.assert_called_once_with('https://example.com/.well-known/agent.json')

            # Verify the returned agent card
            assert isinstance(agent_card, AgentCard)
            assert agent_card.name == mock_agent_card_data['name']
            assert agent_card.version == mock_agent_card_data['version']
            assert agent_card.url == mock_agent_card_data['url']

    def test_get_agent_card_http_error(self):
        """Test HTTP error handling"""
        # Simulate an HTTP error
        with patch('httpx.Client.get') as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "HTTP error",
                request=Mock(),
                response=Mock(status_code=404)
            )

            resolver = A2ACardResolver('https://example.com')

            with pytest.raises(httpx.HTTPStatusError):
                resolver.get_agent_card()

    def test_get_agent_card_json_decode_error(self):
        """Test JSON decoding error handling"""
        # Create a mock response with invalid JSON
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Mocked error", doc="", pos=0)
        mock_response.raise_for_status = Mock()

        # Patch httpx.Client to return our mock response
        with patch('httpx.Client.get', return_value=mock_response):
            resolver = A2ACardResolver('https://example.com')

            with pytest.raises(A2AClientJSONError):
                resolver.get_agent_card()

    def test_get_agent_card_incomplete_data(self):
        """Test handling of incomplete agent card data"""
        # Prepare incomplete mock response data
        mock_agent_card_data = {
            # Missing required fields
        }

        # Create a mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_agent_card_data
        mock_response.raise_for_status = Mock()

        # Patch httpx.Client to return our mock response
        with patch('httpx.Client.get', return_value=mock_response):
            resolver = A2ACardResolver('https://example.com')

            with pytest.raises(ValidationError):
                resolver.get_agent_card()
