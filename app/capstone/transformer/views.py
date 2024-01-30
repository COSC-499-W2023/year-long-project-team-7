from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.core.files.storage import FileSystemStorage
from .forms import TransformerForm
from .forms import RegisterForm
from .forms import LoginForm
from .forms import (UpdateEmailForm, UpdatePasswordForm, ProfileUpdateForm, AccountDeletionForm)
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

    #! Might need later
    # pdf_previews = []
    # pdf_previews.append("example.pdf")
    # for file in output_files:
    #     file_name = file.file.name
    #     base_name, extension = file_name.rsplit(".", 1)
    #     if file_system.exists(f"{base_name}.pdf"):
    #         pdf_previews.append(f"{base_name}.pdf")

    return render(
        request,
        "results.html",
        {"output_files": output_files},
    )


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


def history(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        files = (
            File.objects.filter(user=request.user, is_output=True).order_by("id").all()
        )
        input_files = File.objects.filter(user=request.user, is_output=False).all()
        history = []
        for f in files:
            row = []
            row.append(f.date.strftime("%d/%m/%Y"))
            row.append(
                input_files.filter(conversion__id=f.conversion.id)
                .values("file")
                .get()["file"]
            )
            row.append(f.file.name)
            row.append(f.file.name.split("_")[2].split(".")[0])
            row.append(f.file.url)
            history.append(row)
    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )
    return render(request, "history.html", {"data": history})


def store(request: HttpRequest) -> HttpResponse:
    products = Products.objects.all()
    return render(request, "store.html", {"products": products})


def payments(request: HttpRequest) -> HttpResponse:
    return render(request, "payments.html")


@login_required(login_url="login")
def profile(request):
    if request.method == "POST":
        # User forms for changing username and password
        e_form = UpdateEmailForm(request.POST, instance=request.user)
        p_form = UpdatePasswordForm(user=request.user, data=request.POST)
        # Profile form for changing profile picture
        pic_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        # Delete profile form
        delete_form = AccountDeletionForm(request.POST)
        if e_form.is_valid():
            e_form.save()
            messages.success(request, f"Your email has been updated!")
        if p_form.is_valid():
            p_form.save()
            messages.success(request, f"Your password has been updated!")
        if pic_form.is_valid():
            pic_form.save()
            # messages.success(request, f'Your profile picture has been updated!')   #For some reason this message always sends even when the field is blank
        if delete_form.is_valid() and delete_form.cleaned_data["confirm_delete"]:
            request.user.delete()
            logout(request)  # Log out the user after account deletion
            messages.success(request, f"Your account has been deleted.")
            return redirect("login")
        return redirect("profile")
    else:
        e_form = UpdateEmailForm(instance=request.user)
        p_form = UpdatePasswordForm(user=request.user)
        pic_form = ProfileUpdateForm(instance=request.user.profile)
        delete_form = AccountDeletionForm()
    context = {
        "e_form": e_form,
        "p_form": p_form,
        "pic_form": pic_form,
        "delete_form": delete_form,
    }
    return render(request, "profile.html", context)
    
