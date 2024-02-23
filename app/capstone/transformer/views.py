from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout, get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.core.files.storage import FileSystemStorage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .forms import TransformerForm
from .forms import RegisterForm
from .forms import LoginForm
from .models import Conversion, File, Products
from .tokens import account_activation_token
from typing import List, Dict
import json
from .generator import generate_output
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "about.html")


def register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            email = form.cleaned_data.get("email")
            if email:
                activateEmail(request, user, email)
                messages.success(request, "Account successfully created.")
                return redirect("login")
            else:
                messages.error(request, "Email is required.")
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
    return redirect("login")


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
                "template": form.cleaned_data["template"],
                "model": form.cleaned_data["model"],
            }
            conversion.user_parameters = json.dumps(user_params)
            conversion.user = request.user  # type: ignore

            conversion.save()

            input_files = []

            has_prompt = len(user_params["prompt"]) > 0
            has_file = len(request.FILES.getlist("input_files"))

            if not has_prompt and not has_file:
                return render(
                    request,
                    "transform.html",
                    {"form": TransformerForm(), "errors": ["No input provided"]},
                )

            for uploaded_file in request.FILES.getlist("input_files"):
                new_file = File()
                new_file.user = request.user  # type: ignore
                new_file.conversion = conversion
                if uploaded_file.content_type is not None:
                    new_file.type = uploaded_file.content_type
                new_file.file = uploaded_file
                new_file.is_input = True
                new_file.save()
                input_files.append(new_file)

            has_template_selection = user_params["template"] != ""
            has_template_file = len(request.FILES.getlist("template_file"))
            if not has_template_selection and not has_template_file:
                return render(
                    request,
                    "transform.html",
                    {"form": TransformerForm(), "errors": ["No template provided"]},
                )

            if has_template_file:
                uploaded_template_file = request.FILES.getlist("template_file")[0]
                template_file = File()
                template_file.user = request.user  # type: ignore
                template_file.conversion = conversion
                template_file.type = str(uploaded_template_file.content_type)
                template_file.file = template_file
                template_file.is_input = False
                template_file.save()
            else:
                template_file = File.objects.get(
                    file=f"template_{user_params['template']}.pptx"
                )

            result = generate_output(input_files, template_file, conversion)

            if "Error" in result:
                return render(
                    request,
                    "transform.html",
                    {"form": TransformerForm(), "errors": [result]},
                )

            return redirect("results", conversion_id=conversion.id)
        else:
            return render(
                request,
                "transform.html",
                {"form": TransformerForm(), "errors": form.errors},
            )
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

    return render(
        request,
        "results.html",
        {"output_files": output_files},
    )


@login_required(login_url="login")
def download_file(request: HttpRequest, file_id: int) -> HttpResponse:
    file = get_object_or_404(File, id=file_id)

    if request.user.is_authenticated:
        if file.user != request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )
    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )

    response = HttpResponse(file.file, content_type=file.type)
    response["Content-Disposition"] = f'attachment; filename="{file.file.name}"'
    return response


def activate(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified. You can now log into your account.")
        return redirect("login")
    else:
        messages.error(request, "Activation link is invalid!")
    return redirect("index")


def activateEmail(request: HttpRequest, user: User, to_email: str) -> None:
    mail_subject = "Activate your Platonix account"
    message = render_to_string(
        "template_activate_account.html",
        {
            "user": user.username,
            "domain": get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
            "protocol": "https" if request.is_secure() else "http",
        },
    )
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(
            request,
            f"Hi {user}, please go to your inbox at {to_email} \
                     and click on the activiation link to complete registration.",
        )
    else:
        messages.error(
            request,
            f"Problem sending email to {to_email}. Please verify \
                       spelling.",
        )
    return


@login_required(login_url="login")
def history(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        user_conversions = (
            Conversion.objects.filter(user=request.user).order_by("-date").all()
        )

        history = {}

        for conversion in user_conversions:
            input_files = File.objects.filter(conversion=conversion, is_input=True)
            output_files = File.objects.filter(conversion=conversion, is_output=True)
            history[conversion] = {
                "input_files": input_files,
                "output_files": output_files,
            }

    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )
    return render(request, "history.html", {"history": history})


def store(request: HttpRequest) -> HttpResponse:
    products = Products.objects.all()
    print(products)
    return render(request, "store.html", {"products": products})


def payments(request: HttpRequest) -> HttpResponse:
    return render(request, "payments.html")
