from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Conversion, File
from .forms import TransformerForm
import json
from urllib.parse import urlencode
from unittest.mock import patch



class TransformViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("transform")

    def test_transform_view_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transform.html")

    def test_transform_view_post_request_valid_form(self):
        with patch('transformer.views.generate_output') as mock_generate_output:
            file = SimpleUploadedFile("file.txt", b"file_content")
            data = {
                "text_input": "sample_text",
                "language": "English",
                "complexity": 1,
                "length": 1,
                "files": file,
            }
            response = self.client.post(self.url, data, format="multipart")

            self.assertEqual(response.status_code, 302)

            self.assertEqual(Conversion.objects.count(), 1)
            conversion = Conversion.objects.first()

            expected_user_params_dict = {
                "text_input": "sample_text",
                "language": "English",
                "complexity": 1,
                "length": 1,
            }
            saved_files = list(File.objects.filter(conversion=conversion))

            self.assertEqual(response.url, reverse('results', args=[conversion.id]))
            expected_user_params = json.dumps(expected_user_params_dict)

            self.assertEqual(conversion.user_parameters, expected_user_params)
            self.assertEqual(File.objects.count(), 1)
            mock_generate_output.assert_called_once_with(saved_files, conversion)


    def test_transform_view_post_request_invalid_form(self):
        data = {
            "text_input": "",
            "language": "invalid_language",
            "complexity": 200,
            "length": -10,
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transform.html")
        self.assertContains(response, "form")
