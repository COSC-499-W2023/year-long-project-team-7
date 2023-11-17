from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from .forms import TransformerForm
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
            conversion = Conversion()
            user_params = {
                "prompt": form.cleaned_data["prompt"],
                "language": form.cleaned_data["language"],
                "tone": form.cleaned_data["tone"],
                "complexity": form.cleaned_data["complexity"],
                "num_slides": form.cleaned_data["num_slides"],
                "num_images": form.cleaned_data["num_images"],
                "template": int(form.cleaned_data["template"]),
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
    # Create new user based on user input
    if request.method == "POST":
        username = request.POST.get("username")
        if username is not None:
            username = str(username)
        else:
            messages.error(request, "Cannot be blank.")
            return redirect("signup")

        fname = request.POST.get("fname")
        if fname is not None:
            fname = str(fname)
        else:
            messages.error(request, "First name cannot be blank.")
            return redirect("signup")

        lname = request.POST.get("lname")
        if lname is not None:
            lname = str(lname)
        else:
            messages.error(request, "Last name cannot be blank.")
            return redirect("signup")

        email = request.POST.get("email")
        if email is not None:
            email = str(email)
        else:
            messages.error(request, "Email cannot be blank.")
            return redirect("signup")

        pass1 = request.POST.get("pass1")
        if pass1 is not None:
            pass1 = str(pass1)
        else:
            messages.error(request, "Password cannot be blank.")
            return redirect("signup")

        pass2 = request.POST.get("pass2")
        if pass2 is not None:
            pass2 = str(pass2)
        else:
            messages.error(request, "Password cannot be blank.")
            return redirect("signup")

        myuser: User = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname

        myuser.save()

        messages.success(request, "Account successfully created.")

        return redirect("signin")

    return render(request, "signup.html")


def signin(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username")
        if username is not None:
            username = str(username)
        else:
            messages.error(request, "Username cannot be blank.")
            return redirect("signin")

        pass1 = request.POST.get("pass1")
        if pass1 is not None:
            pass1 = str(pass1)
        else:
            messages.error(request, "Password cannot be blank.")
            return redirect("signin")

        fname = request.POST.get("fname")
        if fname is not None:
            fname = str(fname)
        else:
            fname = ""

        user = authenticate(request, username=username, password=pass1)

        if user is not None:
            login(request, user)
            return redirect("index")

        else:
            messages.error(request, "Incorrect Credentials.")
            return redirect("signin")

    return render(request, "signin.html")


def signout(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Logged Out Successfully.")
    return redirect("index")
