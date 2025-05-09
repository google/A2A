"""Tests for the Image Generation Agent."""

import base64
import os

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from PIL import Image
from agents.crewai.agent import (
    ImageGenerationAgent,
    Imagedata,
    generate_image_tool,
    get_api_key,
)
from common.utils.in_memory_cache import InMemoryCache


@pytest.fixture(autouse=True)
def mock_env_vars(mocker):
    """Mocks environment variables."""
    mocker.patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_api_key'})


@pytest.fixture
def mock_genai_client(mocker):
    """Mocks the google.genai client and its methods."""
    mock_client_instance = MagicMock()
    mock_models = MagicMock()
    mock_response = MagicMock()
    mock_candidate = MagicMock()
    mock_content = MagicMock()
    mock_part_text = MagicMock()
    mock_part_text.text = 'Generated text description.'
    mock_part_text.inline_data = None
    mock_part_image = MagicMock()
    mock_part_image.text = None
    mock_inline_data = MagicMock()
    mock_inline_data.mime_type = 'image/png'
    mock_inline_data.data = b'fake_image_bytes'
    mock_part_image.inline_data = mock_inline_data

    mock_content.parts = [mock_part_image]
    mock_candidate.content = mock_content
    mock_response.candidates = [mock_candidate]

    mock_models.generate_content.return_value = mock_response
    mock_client_instance.models = mock_models

    mock_genai_class = mocker.patch('agents.crewai.agent.genai.Client')
    mock_genai_class.return_value = mock_client_instance

    return {
        'client_class': mock_genai_class,
        'client_instance': mock_client_instance,
        'models': mock_models,
        'response': mock_response,
        'part_text': mock_part_text,
        'part_image': mock_part_image,
    }


@pytest.fixture
def mock_cache(mocker):
    """Mocks the InMemoryCache."""
    mock_cache_instance = MagicMock(spec=InMemoryCache)
    cache_storage = {}

    def mock_get(key, default=None):
        return cache_storage.get(key, default)

    def mock_set(key, value):
        cache_storage[key] = value

    mock_cache_instance.get.side_effect = mock_get
    mock_cache_instance.set.side_effect = mock_set

    mock_cache_class = mocker.patch('agents.crewai.agent.InMemoryCache')
    mock_cache_class.return_value = mock_cache_instance

    return {'instance': mock_cache_instance, 'storage': cache_storage}


@pytest.fixture
def mock_pil_image(mocker):
    """Mocks PIL Image operations."""
    mock_image_instance = MagicMock(spec=Image.Image)
    mock_image_open = mocker.patch('agents.crewai.agent.Image.open')
    mock_image_open.return_value = mock_image_instance
    return {'open': mock_image_open, 'instance': mock_image_instance}


@pytest.fixture
def image_agent_instance(mocker, mock_env_vars):
    """Provides a mocked instance of ImageGenerationAgent."""
    mocker.patch('agents.crewai.agent.LLM')
    mocker.patch('agents.crewai.agent.Agent')
    mocker.patch('agents.crewai.agent.Task')
    mock_crew = mocker.patch('agents.crewai.agent.Crew')
    mock_crew_instance = MagicMock()
    mock_crew.return_value = mock_crew_instance

    agent = ImageGenerationAgent()
    agent.mock_crew_instance = mock_crew_instance
    return agent


def test_get_api_key(mocker):
    """Tests if get_api_key reads the correct environment variable."""
    mock_loader = mocker.patch('agents.crewai.agent.load_dotenv')
    api_key = get_api_key()
    assert api_key == 'test_api_key'
    mock_loader.assert_called_once()


def test_generate_image_tool_success_new_image(
    mocker, mock_genai_client, mock_cache
):
    """Tests the tool generating a new image successfully."""
    mock_uuid = mocker.patch('agents.crewai.agent.uuid4')
    test_uuid = UUID('12345678123456781234567812345678')
    mock_uuid.return_value = test_uuid

    session_id = 'session_123'
    prompt = 'Generate a cat.'

    mock_cache['storage'].clear()

    result_id = generate_image_tool.func(prompt, session_id)

    assert result_id == test_uuid.hex
    mock_genai_client['client_class'].assert_called_once_with(
        api_key='test_api_key'
    )
    mock_genai_client['models'].generate_content.assert_called_once()
    call_args, call_kwargs = mock_genai_client[
        'models'
    ].generate_content.call_args
    assert call_kwargs['model'] == 'gemini-2.0-flash-exp-image-generation'
    expected_contents = (
        prompt,
        'Ignore any input images if they do not match the request.',
    )
    assert call_kwargs['contents'] == expected_contents

    assert session_id in mock_cache['storage']
    assert test_uuid.hex in mock_cache['storage'][session_id]
    cached_data = mock_cache['storage'][session_id][test_uuid.hex]
    assert isinstance(cached_data, Imagedata)
    assert cached_data.id == test_uuid.hex
    assert cached_data.mime_type == 'image/png'
    assert cached_data.bytes == base64.b64encode(b'fake_image_bytes').decode(
        'utf-8'
    )
    assert cached_data.name == 'generated_image.png'


def test_generate_image_tool_success_with_ref_image(
    mocker, mock_genai_client, mock_cache, mock_pil_image
):
    """Tests the tool using a reference image from cache."""
    mock_uuid = mocker.patch('agents.crewai.agent.uuid4')
    test_uuid_new = UUID('abcdefabcdefabcdefabcdefabcdefab')
    mock_uuid.return_value = test_uuid_new

    session_id = 'session_abc'
    prompt = 'Make the dog blue.'
    ref_image_id = 'ref_img_001'
    ref_image_bytes_b64 = base64.b64encode(b'previous_image_data').decode(
        'utf-8'
    )

    mock_cache['storage'].clear()
    mock_cache['storage'][session_id] = {
        ref_image_id: Imagedata(
            id=ref_image_id,
            name='dog.png',
            mimeType='image/png',
            bytes=ref_image_bytes_b64,
        )
    }

    mock_loader = mocker.patch(
        'agents.crewai.agent.base64.b64decode',
        return_value=b'previous_image_data',
    )

    result_id = generate_image_tool.func(prompt, session_id)

    assert result_id == test_uuid_new.hex
    mock_loader.assert_called_once_with(ref_image_bytes_b64)
    mock_pil_image['open'].assert_called_once()
    mock_genai_client['models'].generate_content.assert_called_once()

    call_args, call_kwargs = mock_genai_client[
        'models'
    ].generate_content.call_args
    expected_text_input = (
        prompt,
        'Ignore any input images if they do not match the request.',
    )
    expected_contents = [expected_text_input, mock_pil_image['instance']]
    assert call_kwargs['contents'] == expected_contents

    assert test_uuid_new.hex in mock_cache['storage'][session_id]
    assert len(mock_cache['storage'][session_id]) == 2


def test_generate_image_tool_empty_prompt(mocker):
    """Tests that an empty prompt raises ValueError."""
    with pytest.raises(ValueError, match='Prompt cannot be empty'):
        generate_image_tool.func('', 'session_empty')


def test_image_generation_agent_init(mocker):
    """Tests the agent's constructor."""
    mock_llm_class = mocker.patch('agents.crewai.agent.LLM')
    mock_agent_class = mocker.patch('agents.crewai.agent.Agent')
    mock_task_class = mocker.patch('agents.crewai.agent.Task')
    mock_crew_class = mocker.patch('agents.crewai.agent.Crew')
    mocker.patch(
        'agents.crewai.agent.get_api_key', return_value='fake_key_for_init'
    )

    agent = ImageGenerationAgent()

    mock_llm_class.assert_called_once_with(
        model='gemini/gemini-2.0-flash', api_key='fake_key_for_init'
    )
    mock_agent_class.assert_called_once()
    mock_task_class.assert_called_once()
    mock_crew_class.assert_called_once()
    agent_call_args, agent_call_kwargs = mock_agent_class.call_args
    assert agent_call_kwargs['role'] == 'Image Creation Expert'
    assert any(
        tool.name == 'ImageGenerationTool'
        for tool in agent_call_kwargs['tools']
    )


def test_image_generation_agent_invoke(image_agent_instance):
    """Tests the invoke method."""
    mock_crew_instance = image_agent_instance.mock_crew_instance
    mock_crew_instance.kickoff.return_value = 'mock_final_image_id'

    query = 'Create a picture of a sunset.'
    session_id = 'session_invoke_1'

    result = image_agent_instance.invoke(query, session_id)

    assert result == 'mock_final_image_id'
    expected_inputs = {
        'user_prompt': query,
        'session_id': session_id,
        'artifact_file_id': None,
    }
    mock_crew_instance.kickoff.assert_called_once_with(expected_inputs)


def test_image_generation_agent_get_image_data_found(
    image_agent_instance, mock_cache
):
    """Tests get_image_data when the image is found in the cache."""
    session_id = 'session_get_1'
    image_key = 'img_key_found'
    expected_data = Imagedata(
        id=image_key, name='found.png', mimeType='image/png', bytes='Zm91bmQ='
    )

    mock_cache['storage'][session_id] = {image_key: expected_data}

    result = image_agent_instance.get_image_data(session_id, image_key)

    assert result == expected_data
    mock_cache['instance'].get.assert_called_with(session_id)


def test_image_generation_agent_get_image_data_not_found_key_missing(
    image_agent_instance, mock_cache
):
    """Tests get_image_data when the session exists but the key is missing."""
    session_id = 'session_get_2'
    image_key = 'img_key_missing'

    mock_cache['storage'][session_id] = {'other_key': Imagedata(id='other')}

    result = image_agent_instance.get_image_data(session_id, image_key)

    assert isinstance(result, Imagedata)
    assert result.id is None
    assert result.error == 'Error generating image, please try again.'
    mock_cache['instance'].get.assert_called_with(session_id)
