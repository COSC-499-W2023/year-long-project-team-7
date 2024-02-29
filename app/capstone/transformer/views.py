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
from .forms import (
    UpdateEmailForm,
    UpdatePasswordForm,
    ProfileUpdateForm,
    AccountDeletionForm,
)
from .models import Conversion, File, Product
from .tokens import account_activation_token
from typing import List, Dict
import json
from .generator import generate_output
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import stripe
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .subscriptionManager import has_valid_subscription, give_subscription_to_user
from django.contrib.auth.models import User
from datetime import date, timedelta


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


def transform(request: HttpRequest) -> HttpResponse:
    if has_valid_subscription(request.user.id):  # type: ignore
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
                    return render(
                        request, "transform.html", {"form": TransformerForm()}
                    )

                for uploaded_file in request.FILES.getlist("files"):
                    new_file = File()
                    new_file.user = (
                        request.user if request.user.is_authenticated else None
                    )
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
    else:
        messages.error(request, "You must have an active subscription to use Create.")
        return redirect("store")


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
    products = Product.objects.all()
    return render(request, "store.html", {"products": products})


class CreateCheckoutSessionView(View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # type: ignore
        if request.user.is_authenticated:
            if has_valid_subscription(request.user.id):
                messages.error(request, "You already have an active subscription.")
                return redirect("store")
            else:
                product_id = self.kwargs["pk"]
                product = Product.objects.get(id=product_id)
                stripe.api_key = settings.STRIPE_SECRET_KEY  # type: ignore
                YOUR_DOMAIN = settings.DOMAIN  # type: ignore
                checkout_session = stripe.checkout.Session.create(
                    line_items=[
                        {
                            "price_data": {
                                "currency": "cad",
                                "unit_amount": product.get_display_price_cents,
                                "product_data": {"name": product.name},
                            },
                            "quantity": 1,
                        }
                    ],
                    metadata={"product_id": product.id, "user_id": request.user.id},
                    mode="payment",
                    success_url=YOUR_DOMAIN + "/success",
                    cancel_url=YOUR_DOMAIN + "/cancel",
                    automatic_tax={"enabled": True},
                )
                response = redirect(checkout_session.url)  # type: ignore
                return response
        else:
            messages.error(request, "You must be logged in to purchase a product.")
            return redirect("store")


def success(request: HttpRequest) -> HttpResponse:
    return render(request, "success.html")


def cancel(request: HttpRequest) -> HttpResponse:
    return render(request, "cancel.html")


@csrf_exempt
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None
    webhook_key = settings.STRIPE_WEBHOOK_SECRET  # type: ignore
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_key)
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:  # type: ignore
        # Invalid signature
        return HttpResponse(status=400)
    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        # Retrieve the session. If you require line items in the response, you may include them by expanding line_items.
        session = stripe.checkout.Session.retrieve(event["data"]["object"]["id"])
        user_id = session["metadata"]["user_id"]
        product_id = session["metadata"]["product_id"]
        subscription_user = User.objects.get(id=user_id)
        subscription_product = Product.objects.get(id=product_id)
        start_date = date.today()
        length_days = subscription_product.length_days
        end_date = start_date + timedelta(days=length_days)
        give_subscription_to_user(subscription_user, start_date, end_date)
    # Passed signature verification
    return HttpResponse(status=200)


def payments(request: HttpRequest) -> HttpResponse:
    return render(request, "payments.html")


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        if "profile_pic_submit" in request.POST:
            pic_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)  # type: ignore
            if pic_form.is_valid():
                pic_form.save()
                messages.success(request, "Your profile picture has been updated!")
            else:
                messages.error(
                    request,
                    "Invalid profile picture form data. Please check and try again.",
                )
        elif "email_submit" in request.POST:
            e_form = UpdateEmailForm(request.POST, instance=request.user)
            if e_form.is_valid():
                e_form.save()
                messages.success(request, "Your email has been updated!")
            else:
                messages.error(
                    request, "Invalid email form data. Please check and try again."
                )
        elif "password_submit" in request.POST:
            p_form = UpdatePasswordForm(user=request.user, data=request.POST)  # type: ignore
            if p_form.is_valid():
                p_form.save()
                messages.success(request, "Your password has been updated!")
                return redirect("profile")
            else:
                messages.error(
                    request, "Invalid password form data. Please check and try again."
                )
        elif "confirm_delete" in request.POST:

            delete_form = AccountDeletionForm(request.POST)
            if delete_form.is_valid() and delete_form.cleaned_data.get(
                "confirm_delete"
            ):
                request.user.delete()
                messages.success(request, "Your account has been deleted.")
                return redirect("login")
            else:
                messages.error(
                    request,
                    "Account could not be deleted. Please confirm your deletion request.",
                )
        return redirect("profile")
    else:
        pic_form = ProfileUpdateForm(instance=request.user.profile)  # type: ignore
        e_form = UpdateEmailForm(instance=request.user)
        p_form = UpdatePasswordForm(user=request.user)  # type: ignore
        delete_form = AccountDeletionForm()
    context = {
        "pic_form": pic_form,
        "e_form": e_form,
        "p_form": p_form,
        "delete_form": delete_form,
    }
    return render(request, "profile.html", context)
