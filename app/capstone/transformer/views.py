from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from .forms import TransformerForm
from .forms import SignUpForm
from .forms import SignInForm
from .models import Conversion, File, Products
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
            conversion = Conversion()
            user_params = {
                "prompt": form.cleaned_data["prompt"],
                "language": form.cleaned_data["language"],
                "tone": form.cleaned_data["tone"],
                "complexity": form.cleaned_data["complexity"],
                "num_slides": form.cleaned_data["num_slides"],
                "image_frequency": form.cleaned_data["image_frequency"],
                "template": int(form.cleaned_data["template"]),
            }
            conversion.user_parameters = json.dumps(user_params)

            if request.user.is_authenticated:
                conversion.user = request.user
            else:
                conversion.user = None

            conversion.save()

            files = []

            has_prompt = len(user_params["prompt"]) > 0
            has_file = len(request.FILES.getlist("files"))

            if not has_prompt and not has_file:
                return render(request, "transform.html", {"form": TransformerForm()})

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
        else:
            return render(request, "transform.html", {"form": TransformerForm()})
    else:
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


def store(request: HttpRequest) -> HttpResponse:
    products = Products.objects.all()
    return render(request, "store.html", {"products": products})


def payments(request: HttpRequest) -> HttpResponse:
    return render(request, "payments.html")
