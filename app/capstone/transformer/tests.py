from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from os import path, mkdir
from shutil import rmtree
from .models import Conversion, File
from .models import Conversion, File, Products
from .forms import TransformerForm
import json
from urllib.parse import urlencode
from unittest.mock import patch
import tempfile


class TransformViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("transform")
        self.user = User.objects.create_user(
            email="testuser@email.com", password="testpassword123", username="test"
        )

    def test_transform_view_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_transform_view_post_request_valid_form(self):
        self.client.login(username="test", password="testpassword123")
        with patch("transformer.views.generate_output") as mock_generate_output:
            file = SimpleUploadedFile("file.txt", b"file_content")
            data = {
                "prompt": "sample_text",
                "language": "English",
                "tone": "Fun",
                "complexity": 1,
                "num_slides": 1,
                "image_frequency": 0,
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
                "image_frequency": 0,
                "template": 1,
            }
            saved_files = list(File.objects.filter(conversion=conversion))

            self.assertEqual(response.url, reverse("results", args=[conversion.id]))
            expected_user_params = json.dumps(expected_user_params_dict)
            self.assertEqual(conversion.user_parameters, expected_user_params)
            self.assertEqual(File.objects.count(), 1)
            mock_generate_output.assert_called_once_with(saved_files, conversion)

    def test_transform_view_post_request_invalid_form(self):
        self.client.login(username="test", password="testpassword123")
        data = {
            "prompt": "",
            "language": "invalid_language",
            "tone": "invalid_tone",
            "complexity": 200,
            "length": -10,
            "num_slides": 1,
            "image_frequency": 0,
            "template": 1,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transform.html")
        self.assertContains(response, "form")


class RegisterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("register")

    def test_register_view_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")

    def test_user_registration(self):
        # Make a POST request to the sign-up view with valid data
        response = self.client.post(
            reverse("register"),
            {
                "email": "testuser@example.com",
                "password": "testpassword123",
            },
        )
        # Check if the user was created and logged in successfully
        self.assertEqual(
            response.status_code, 302
        )  # HTTP status code for a successful redirect
        self.assertRedirects(response, reverse("login"))
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().email, "testuser@example.com")

    def test_invalid_user_registration(self):
        # Make a POST request to the sign-up view with invalid data
        response = self.client.post(
            reverse("register"),
            {
                "email": "invalidemail",
                "password": "testpassword123",
            },
        )
        # Check if the form is not valid and no user was created
        self.assertEqual(
            response.status_code, 200
        )  # 200 is the HTTP status code for a successful GET request
        self.assertContains(response, "Error in the form submission.")
        self.assertEqual(User.objects.count(), 0)


class UserSignInTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.signin_url = reverse("login")
        self.user = User.objects.create_user(
            email="testuser@email.com",
            password="testpassword123",
            username="testuser@email.com",
        )

    def test_user_signin_valid_credentials(self):
        # Make a POST request to the sign-in view with valid credentials
        response = self.client.post(
            reverse("login"),
            {
                "email": "testuser@email.com",
                "password": "testpassword123",
            },
        )
        # Check if the user was authenticated and redirected to the index page
        self.assertEqual(
            response.status_code, 302
        )  # HTTP status code for a successful redirect
        self.assertRedirects(response, reverse("transform"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_signin_invalid_credentials(self):
        # Make a POST request to the sign-in view with invalid credentials
        response = self.client.post(
            reverse("login"),
            {
                "email": "testuser@email.com",
                "password": "wrongpassword",
            },
        )
        # Check if the user was not authenticated and an error message is present
        self.assertEqual(
            response.status_code, 200
        )  # 200 is the HTTP status code for a successful GET request
        self.assertContains(response, "Incorrect Credentials.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class HistoryTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        testuser = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary')
        testconversion = Conversion.objects.create(date="9999-12-31", user=testuser)
        with tempfile.TemporaryDirectory(dir=settings.BASE_DIR) as temp_dir:
            input_pdf = open(path.join(temp_dir, "test.pdf"), 'w+')
            output_pptx = open(path.join(temp_dir, "conversion_output_1.pptx"), 'w+')
            input_file = File.objects.create(date="9999-12-31", user=testuser, conversion=testconversion, is_output=False, type=".pdf", file=None)
            output_file = File.objects.create(date="9999-12-31", user=testuser, conversion=testconversion, is_output=True, type=".application/pptx", file=None)
            input_file.file.save("test.pdf", input_pdf)
            output_file.file.save("conversion_output_1.pptx", output_pptx)
            input_pdf.close()
            output_pptx.close()
        self.url = reverse("history")
        
    def test_history_view_get_request_invalid_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_history_view_get_request_valid_user(self):
        self.client.login(username='temporary', password='temporary')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
    def test_history_results(self):
        self.client.login(username='temporary', password='temporary')
        response = self.client.get(self.url)
        self.assertContains(response, "31/12/9999")
        self.assertContains(response, ".pdf")
        self.assertContains(response, ".pptx")

        
class StoreTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("store")

    def test_store_view_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store.html")

