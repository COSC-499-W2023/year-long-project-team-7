from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from .forms import TransformerForm
from .forms import SignUpForm
from .forms import SignInForm
from .models import Conversion, File
from typing import List, Dict
import json
from .generator import generate_output
from django.shortcuts import render, get_object_or_404, redirect


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


def transform(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = TransformerForm(request.POST)

        if form.is_valid():
            conversion: Conversion = Conversion()
            user_params = {
                "text_input": form.cleaned_data["text_input"],
                "language": form.cleaned_data["language"],
                "complexity": form.cleaned_data["complexity"],
                "length": form.cleaned_data["length"],
            }
            conversion.user_parameters = json.dumps(user_params)
            conversion.save()

            files = []

            for uploaded_file in request.FILES.getlist("files"):
                new_file = File()
                new_file.user = request.user if request.user.is_authenticated else None
                new_file.conversion = conversion
                if uploaded_file.content_type is not None:
                    new_file.type = uploaded_file.content_type
                new_file.file = uploaded_file
                new_file.save()
                files.append(new_file)

            generate_output(files, conversion)

            return redirect("results", conversion_id=conversion.id)

    return render(request, "transform.html", {"form": TransformerForm()})


def results(request: HttpRequest, conversion_id: int) -> HttpResponse:
    conversion = get_object_or_404(Conversion, id=conversion_id)

    if request.user.is_authenticated:
        if conversion.user != request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )
    else:
        if conversion.user is not None:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )

    output_files = File.objects.filter(conversion=conversion, is_output=True)

    return render(request, "results.html", {"output_files": output_files})


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "about.html")


def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account successfully created.")
            return redirect("signin")
        else:
            messages.error(request, "Error in the form submission.")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def signin(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect("index")
            else:
                messages.error(request, "Incorrect Credentials.")
    else:
        form = SignInForm()
    return render(request, "signin.html", {"form": form})


def signout(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Logged Out Successfully.")
    return redirect("index")
