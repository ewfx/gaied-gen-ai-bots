import unittest
from unittest.mock import patch, MagicMock
from emailgen import generate_financial_data, generate_email_content, create_attachment_from_content, build_email

class TestEmailGen(unittest.TestCase):

    @patch('emailgen.genai.Client')
    def test_generate_email_content(self, mock_client):
        mock_response = MagicMock()
        mock_response.text = '{"email_chain": "<html><body>Email content</body></html>", "attachments": ["Attachment 1", "Attachment 2"]}'
        mock_client.return_value.models.generate_content.return_value = mock_response
        result = generate_email_content("request_type", "sub_type", 2)
        self.assertIn("email_chain", result)
        self.assertIn("attachments", result)
        self.assertEqual(len(result["attachments"]), 2)

    @patch('emailgen.create_pdf_attachment')
    @patch('emailgen.create_docx_attachment')
    @patch('emailgen.create_image_attachment')
    def test_create_attachment_from_content(self, mock_image, mock_docx, mock_pdf):
        mock_image.return_value = b'image data'
        mock_docx.return_value = b'docx data'
        mock_pdf.return_value = b'pdf data'
        filename, data = create_attachment_from_content("Sample content", "suffix")
        self.assertTrue(filename.endswith(('.pdf', '.docx', '.png')))
        self.assertIn(data, [b'image data', b'docx data', b'pdf data'])

    @patch('emailgen.generate_email_content')
    @patch('emailgen.create_attachment_from_content')
    def test_build_email(self, mock_create_attachment, mock_generate_content):
        mock_generate_content.return_value = {
            "email_chain": "<html><body>Email content</body></html>",
            "attachments": ["Attachment 1"]
        }
        mock_create_attachment.return_value = ("report.pdf", b'pdf data')
        email_msg = build_email("request_type", "sub_type")
        self.assertIn("Email content", email_msg.as_string())
        self.assertIn("report.pdf", email_msg.as_string())

if __name__ == '__main__':
    unittest.main()