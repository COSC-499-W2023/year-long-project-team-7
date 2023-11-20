from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
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
        with patch("transformer.views.generate_output") as mock_generate_output:
            file = SimpleUploadedFile("file.txt", b"file_content")
            data = {
                "prompt": "sample_text",
                "language": "English",
                "tone": "Fun",
                "complexity": 1,
                "num_slides": 1,
                "num_images": 0,
                "template": 1,
                "files": file,
            }
            response = self.client.post(self.url, data, format="multipart")

            self.assertEqual(response.status_code, 302)

            self.assertEqual(Conversion.objects.count(), 1)
            conversion = Conversion.objects.first()

            expected_user_params_dict = {
                "prompt": "sample_text",
                "language": "English",
                "tone": "Fun",
                "complexity": 1,
                "num_slides": 1,
                "num_images": 0,
                "template": 1,
            }
            saved_files = list(File.objects.filter(conversion=conversion))

            self.assertEqual(response.url, reverse("results", args=[conversion.id]))
            expected_user_params = json.dumps(expected_user_params_dict)
            self.assertEqual(conversion.user_parameters, expected_user_params)
            self.assertEqual(File.objects.count(), 1)
            mock_generate_output.assert_called_once_with(saved_files, conversion)

    def test_transform_view_post_request_invalid_form(self):
        data = {
            "text_input": "",
            "language": "invalid_language",
            "tone": "invalid_tone",
            "complexity": 200,
            "length": -10,
            "num_slides": 1,
            "num_images": 0,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transform.html")
        self.assertContains(response, "form")


class RegisterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("signup")

    def test_register_view_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")

    def test_user_registration(self):
        registration_data = {
            "username": "testuser",
            "fname": "John",
            "lname": "Doe",
            "email": "testuser@example.com",
            "pass1": "testpassword",
            "pass2": "testpassword",
        }

        response = self.client.post(self.url, data=registration_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Check for user created in the database
        self.assertTrue(User.objects.filter(username="testuser").exists())
        self.assertContains(response, "Account successfully created.")
        self.assertRedirects(response, reverse("signin"))


class UserSignInTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.signin_url = reverse("signin")

        self.test_user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

    def test_user_signin_valid_credentials(self):
        signin_data = {
            "username": "testuser",
            "pass1": "testpassword",
        }

        response = self.client.post(self.signin_url, data=signin_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("index"))

    def test_user_signin_invalid_credentials(self):
        # Data with invalid credentials
        signin_data = {
            "username": "testuser",
            "pass1": "wrongpassword",
        }

        response = self.client.post(self.signin_url, data=signin_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect Credentials.")
        self.assertRedirects(response, reverse("signin"))
