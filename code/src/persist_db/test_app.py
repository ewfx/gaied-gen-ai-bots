import unittest
from unittest.mock import patch, MagicMock
from app import app


class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch("app.email_classification_model")
    def test_index(self, mock_model):
        mock_model.find_all.return_value = []
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<!DOCTYPE html>", response.data)

    @patch("app.email_classification_model")
    def test_get_email_api(self, mock_model):
        mock_model.get_email_classification.return_value = {
            "_id": "123",
            "data": "test",
        }
        response = self.app.get("/api/email?id=123")
        self.assertEqual(response.status_code, 200)

    @patch("app.email_classification_model")
    def test_post_email_api_no_file(self, mock_model):
        response = self.app.post("/api/email", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"No file part in the request", response.data)

    @patch("app.email_classification_model")
    def test_put_email_api(self, mock_model):
        mock_model.update_email_classification.return_value = None
        data = {"_id": "123", "data": "updated"}
        response = self.app.put("/api/email", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Email updated", response.data)

    @patch("app.email_classification_model")
    def test_delete_email_api(self, mock_model):
        mock_model.delete_email_classification.return_value = None
        response = self.app.delete("/api/email?id=123")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Email deleted", response.data)

    @patch("app.email_classification_model")
    def test_update_existing_email(self, mock_model):
        mock_model.get_all_request_types.return_value = []
        mock_model.update_email_classification.return_value = None
        data = {"duplicate_id": "123", "email_chain": ["email_chain"]}
        response = self.app.post("/api/email/update_existing", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Email updated", response.data)

    @patch("app.email_classification_model")
    def test_discard_email(self, mock_model):
        response = self.app.post("/api/email/discard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Email discarded", response.data)

    @patch("app.email_classification_model")
    def test_manage_requests_get(self, mock_model):
        mock_model.get_all_request_types.return_value = []
        response = self.app.get("/manage_requests")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<!DOCTYPE html>", response.data)

    @patch("app.email_classification_model")
    def test_manage_requests_post(self, mock_model):
        data = {"request_type": "type1", "sub_request_types": "sub1,sub2"}
        response = self.app.post("/manage_requests", data=data)
        self.assertEqual(response.status_code, 302)  # Redirect after POST


if __name__ == "__main__":
    unittest.main()
