import unittest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
from extract import extract_text_from_pdf_bytes, extract_text_from_docx_bytes, extract_text_from_txt_bytes, extract_text_from_image, analyze_with_llm

class TestExtractFunctions(unittest.TestCase):

    @patch('fitz.open')
    def test_extract_text_from_pdf_bytes_valid_pdf(self, mock_fitz_open):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc.__iter__.return_value = iter([mock_page])
        mock_fitz_open.return_value = mock_doc

        pdf_bytes = b'%PDF-1.4\n...'
        result = extract_text_from_pdf_bytes(pdf_bytes)
        self.assertEqual(result, "")

    @patch('fitz.open')
    def test_extract_text_from_pdf_bytes_invalid_pdf(self, mock_fitz_open):
        mock_fitz_open.side_effect = Exception("Invalid PDF")
        pdf_bytes = b'Invalid PDF content'
        try:
            extract_text_from_pdf_bytes(pdf_bytes)
        except Exception as e:
            self.assertEqual(str(e), "Invalid PDF")


    def test_extract_text_from_txt_bytes_valid_txt(self):
        txt_bytes = b'Sample TXT text'
        result = extract_text_from_txt_bytes(txt_bytes)
        self.assertEqual(result, "Sample TXT text")

    def test_extract_text_from_txt_bytes_empty_txt(self):
        txt_bytes = b''
        result = extract_text_from_txt_bytes(txt_bytes)
        self.assertEqual(result, "")

    @patch('pytesseract.image_to_string')
    @patch('PIL.Image.open')
    def test_extract_text_from_image_valid_image(self, mock_image_open, mock_image_to_string):
        mock_image = MagicMock()
        mock_image_open.return_value = mock_image
        mock_image_to_string.return_value = "Sample Image text"
        try:
            extract_text_from_image('sample_image.png')
        except FileNotFoundError as e:
            self.assertEqual(str(e), "[Errno 2] No such file or directory: 'sample_image.png'")

    @patch('pytesseract.image_to_string')
    @patch('PIL.Image.open')
    def test_extract_text_from_image_invalid_image(self, mock_image_open, mock_image_to_string):
        mock_image_open.side_effect = Exception("Invalid Image")
        try:
            extract_text_from_image('invalid_image.png')
        except Exception as e:
            self.assertEqual(str(e), "Invalid Image")

    @patch('extract.client.models.generate_content')
    def test_analyze_with_llm_valid_response(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.text = '{"request_type": "type1", "confidence_score": 95}'
        mock_generate_content.return_value = mock_response
        email_body = "Sample email body"
        request_types = ["type1", "type2"]
        result = analyze_with_llm(email_body, request_types)
        self.assertEqual(result, {"request_type": "type1", "confidence_score": 95})

    @patch('extract.client.models.generate_content')
    def test_analyze_with_llm_invalid_response(self, mock_generate_content):
        mock_response = MagicMock()
        mock_response.text = 'Invalid JSON'
        mock_generate_content.return_value = mock_response
        email_body = "Sample email body"
        request_types = ["type1", "type2"]
        result = analyze_with_llm(email_body, request_types)
        self.assertEqual(result, 'Invalid JSON')

if __name__ == '__main__':
    unittest.main()