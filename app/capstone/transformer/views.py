from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .forms import TransformerForm
from .forms import SignUpForm
from .forms import SignInForm
from .models import Conversion, File
from .tokens import account_activation_token
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
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect("signin")
        else:
            messages.error(request, "Error in the form submission.")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})

def activate(request, uidb64, token):
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
        return redirect('signin')
    else:
        messages.error(request, "Activation link is invalid!")
    return redirect('index')

def activateEmail(request, user, to_email):
    mail_subject = "Activate your Platonix account"
    message = render_to_string("template_activate_account.html", {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        "protocol": 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f'Hi {user}, please go to your inbox at {to_email} \
                     and click on the activiation link to complete registration.')
    else:
        messages.error(request, f'Problem sending email to {to_email}. Please verify \
                       spelling.')


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
