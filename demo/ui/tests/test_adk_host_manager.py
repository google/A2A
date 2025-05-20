import unittest

from common.types import DataPart, FilePart, TextPart
from google.genai import types
from service.server.adk_host_manager import ADKHostManager


class ADKHostManagerTest(unittest.TestCase):
    """Tests for ADKHostManager class.

    This test suite verifies the conversion of ADK content to message format,
    handling various content types including text, files, data, and function responses.
    """

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.manager = ADKHostManager()
        self.conversation_id = 'test_conversation'

    def test_adk_content_to_message_text(self) -> None:
        """Test converting ADK content with text part to message."""
        part = types.Part()
        part.text = 'Hello'
        content = types.Content(parts=[part], role='user')
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(
            len(message.parts), 1, 'Message should have exactly one part'
        )
        self.assertIsInstance(
            message.parts[0], TextPart, 'Part should be a TextPart'
        )
        self.assertEqual(
            message.parts[0].text, 'Hello', 'Text content should match'
        )
        self.assertEqual(message.role, 'user', 'Role should be preserved')
        self.assertEqual(
            message.metadata['conversation_id'],
            self.conversation_id,
            'Conversation ID should be preserved',
        )

    def test_adk_content_to_message_file(self):
        """Test converting ADK content with file part to message."""
        part = types.Part()
        part.file_data = types.FileData(
            file_uri='gs://test-bucket/test.txt', mime_type='text/plain'
        )
        content = types.Content(parts=[part], role='user')
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(len(message.parts), 1)
        self.assertIsInstance(message.parts[0], FilePart)
        self.assertEqual(message.parts[0].type, 'file')
        self.assertEqual(message.parts[0].file.uri, 'gs://test-bucket/test.txt')
        self.assertEqual(message.parts[0].file.mimeType, 'text/plain')
        self.assertEqual(message.role, 'user')
        self.assertEqual(
            message.metadata['conversation_id'], self.conversation_id
        )

    def test_adk_content_to_message_data(self):
        """Test converting ADK content with data part to message."""
        part = types.Part()
        part.text = '{"key": "value"}'
        content = types.Content(parts=[part], role='user')
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(len(message.parts), 1)
        self.assertIsInstance(message.parts[0], DataPart)
        self.assertEqual(message.parts[0].data, {'key': 'value'})
        self.assertEqual(message.role, 'user')
        self.assertEqual(
            message.metadata['conversation_id'], self.conversation_id
        )

    def test_adk_content_to_message_function_response(self):
        """Test converting ADK content with function response to message."""
        part = types.Part()
        part.function_response = types.FunctionResponse(
            name='test_function',
            response={'result': [{'type': 'text', 'text': 'Hello'}]},
        )
        content = types.Content(parts=[part], role='user')
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(len(message.parts), 1)
        self.assertIsInstance(message.parts[0], DataPart)
        self.assertEqual(
            message.parts[0].data, {'type': 'text', 'text': 'Hello'}
        )
        self.assertEqual(message.role, 'user')
        self.assertEqual(
            message.metadata['conversation_id'], self.conversation_id
        )

    def test_adk_content_to_message_function_response_error(self):
        """Test error handling when converting function response to message."""
        part = types.Part()
        part.function_response = types.FunctionResponse(
            name='test_function', response={'result': None}
        )
        content = types.Content(parts=[part], role='user')
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(len(message.parts), 1)
        self.assertIsInstance(message.parts[0], DataPart)
        self.assertEqual(message.role, 'user')
        self.assertEqual(
            message.metadata['conversation_id'], self.conversation_id
        )

    def test_adk_content_to_message_empty_parts(self):
        """Test converting ADK content with empty parts to message."""
        content = types.Content(parts=[], role='user')
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(len(message.parts), 0)
        self.assertEqual(message.role, 'user')
        self.assertEqual(
            message.metadata['conversation_id'], self.conversation_id
        )

    def test_adk_content_to_message_unknown_type(self):
        """Test handling unknown content type in ADK content."""
        part = types.Part()
        content = types.Content(parts=[part], role='user')
        with self.assertRaisesRegex(
            ValueError, 'Unexpected content, unknown type'
        ):
            self.manager.adk_content_to_message(content, self.conversation_id)

    def test_adk_content_to_message_multiple_files(self) -> None:
        """Test converting ADK content with multiple file parts to message."""
        file1 = types.Part()
        file1.file_data = types.FileData(
            file_uri='gs://test-bucket/file1.txt', mime_type='text/plain'
        )

        file2 = types.Part()
        file2.file_data = types.FileData(
            file_uri='gs://test-bucket/file2.jpg', mime_type='image/jpeg'
        )

        content = types.Content(parts=[file1, file2], role='user')
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(len(message.parts), 2, 'Message should have two parts')
        self.assertIsInstance(
            message.parts[0], FilePart, 'First part should be a FilePart'
        )
        self.assertIsInstance(
            message.parts[1], FilePart, 'Second part should be a FilePart'
        )
        self.assertEqual(
            message.parts[0].file.uri, 'gs://test-bucket/file1.txt'
        )
        self.assertEqual(
            message.parts[1].file.uri, 'gs://test-bucket/file2.jpg'
        )

    def test_adk_content_to_message_mixed_content(self) -> None:
        """Test converting ADK content with mixed content types to message."""
        text_part = types.Part()
        text_part.text = 'Hello'

        file_part = types.Part()
        file_part.file_data = types.FileData(
            file_uri='gs://test-bucket/test.txt', mime_type='text/plain'
        )

        data_part = types.Part()
        data_part.text = '{"key": "value"}'

        content = types.Content(
            parts=[text_part, file_part, data_part], role='user'
        )
        message = self.manager.adk_content_to_message(
            content, self.conversation_id
        )
        self.assertEqual(
            len(message.parts), 3, 'Message should have three parts'
        )
        self.assertIsInstance(
            message.parts[0], TextPart, 'First part should be TextPart'
        )
        self.assertIsInstance(
            message.parts[1], FilePart, 'Second part should be FilePart'
        )
        self.assertIsInstance(
            message.parts[2], DataPart, 'Third part should be DataPart'
        )


if __name__ == '__main__':
    unittest.main()
