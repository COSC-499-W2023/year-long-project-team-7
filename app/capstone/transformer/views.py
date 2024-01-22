from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from .forms import TransformerForm
from .forms import RegisterForm
from .forms import LoginForm
from .models import Conversion, File, Product
from typing import List, Dict
import json
from .generator import generate_output
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import stripe
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt


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
    products = Product.objects.all()
    return render(request, "store.html", {"products": products})


class CreateCheckoutSessionView(View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse: # type: ignore
        product_id = self.kwargs["pk"]
        product = Product.objects.get(id=product_id)
        stripe.api_key = settings.STRIPE_SECRET_KEY # type: ignore
        YOUR_DOMAIN = "http://127.0.0.1:8000"
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                        'price_data': {
                            'currency': 'cad',
                            'unit_amount': product.get_display_price_cents,
                            'product_data': {
                                'name': product.name
                            },
                        },
                        'quantity': 1
                }
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
            automatic_tax={'enabled': True},
        )
        response = redirect(checkout_session.url) #type: ignore
        return response
    
def success(request: HttpRequest) -> HttpResponse:
    return render(request, "success.html")

def cancel(request: HttpRequest) -> HttpResponse:
    return render(request, "cancel.html")

@csrf_exempt
def stripe_webhook(request: HttpRequest) -> HttpResponse:   #this will be needed later to authenticate payments
  payload = request.body
  print(payload) 
  return HttpResponse(status=200)