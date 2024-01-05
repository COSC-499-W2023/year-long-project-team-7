from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from .forms import TransformerForm
from .forms import RegisterForm
from .forms import LoginForm
from .models import Conversion, File, Products
from typing import List, Dict
import json
from .generator import generate_output
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


@login_required(login_url="login")
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
            conversion.user = request.user  # type: ignore
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


@login_required(login_url="login")
def results(request: HttpRequest, conversion_id: int) -> HttpResponse:
    conversion = get_object_or_404(Conversion, id=conversion_id)

    if request.user.is_authenticated:
        if conversion.user != request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )
    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )

    output_files = File.objects.filter(conversion=conversion, is_output=True)

    return render(request, "results.html", {"output_files": output_files})


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "about.html")


def register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account successfully created.")
            return redirect("login")
        else:
            messages.error(request, "Error in the form submission.")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def login(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                auth_login(request, user)
                return redirect("transform")
            else:
                messages.error(request, "Incorrect Credentials.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


@login_required(login_url="login")
def logout(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    messages.success(request, "Logged Out Successfully.")
    return redirect("index")


def store(request: HttpRequest) -> HttpResponse:
    products = Products.objects.all()
    return render(request, "store.html", {"products": products})


def payments(request: HttpRequest) -> HttpResponse:
    return render(request, "payments.html")
