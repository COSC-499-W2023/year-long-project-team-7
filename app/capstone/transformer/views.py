import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout, get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.forms import formset_factory
from .presentationGenerator import SlideToBeUpdated
from .utils import error
import fitz  # type: ignore
from .presentationManager import MissingPlaceholderError
from .forms import (
    ExerciseRepromptForm,
    LoginForm,
    RegisterForm,
    RepromptForm,
    TransformerForm,
    UpdateEmailForm,
    UpdatePasswordForm,
    ProfileUpdateForm,
    AccountDeletionForm,
    SubscriptionDeletionForm,
    ExerciseForm,
    LoginForm,
    RegisterForm,
    TransformerForm,
)
from .models import (
    Conversion,
    File,
    ModelChoice,
    Product,
    Profile,
    Subscription,
    Exercise,
    SlideTypes,
)
from .tokens import account_activation_token
from .generator import generate_exercise
from .models import Conversion, File, ModelChoice, Product, Profile, Subscription
from .tokens import account_activation_token
from .generator import generate_presentation, reprompt_slides
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import stripe
from django.conf import settings
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .subscriptionManager import (
    has_valid_subscription,
    give_subscription_to_user,
    has_premium_subscription,
    delete_subscription,
)
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
            TForm = TransformerForm(request.POST)
            EForm = ExerciseForm(request.POST)
            input_files: list[File] = []

            if TForm.is_valid():
                try:
                    conversion = Conversion.objects.create(
                        prompt=TForm.cleaned_data["prompt"],
                        language=TForm.cleaned_data["language"],
                        tone=TForm.cleaned_data["tone"],
                        complexity=TForm.cleaned_data["complexity"],
                        num_slides=TForm.cleaned_data["num_slides"],
                        image_frequency=TForm.cleaned_data["image_frequency"],
                        model=TForm.cleaned_data["model"],
                        user=request.user,  # type: ignore
                    )

                    has_prompt = len(conversion.prompt) > 0
                    has_file = len(request.FILES.getlist("input_files"))

                    has_template_selection = TForm.cleaned_data["template"] != ""
                    has_template_file = len(request.FILES.getlist("template_file"))
                    if not has_template_selection and not has_template_file:
                        messages.error(request, "No template provided.")
                        return render(
                            request,
                            "transform.html",
                            {
                                "TForm": TransformerForm(),
                                "EForm": ExerciseForm(),
                            },
                        )

                    if conversion.model == ModelChoice.GPT_4:
                        if not has_premium_subscription(request.user.id):  # type: ignore
                            messages.error(
                                request,
                                "You must have a premium subscription to use the GPT-4 model.",
                            )
                            return render(
                                request,
                                "transform.html",
                                {
                                    "TForm": TransformerForm(),
                                    "EForm": ExerciseForm(),
                                },
                            )

                    if not has_prompt and not has_file:
                        messages.error(
                            request, "Input must include a prompt and/or a file."
                        )
                        return render(
                            request,
                            "transform.html",
                            {
                                "TForm": TransformerForm(),
                                "EForm": ExerciseForm(),
                            },
                        )

                    valid_extensions = [
                        ".doc",
                        ".docx",
                        ".ppt",
                        ".pptx",
                        ".pdf",
                        ".txt",
                        ".rtf",
                        ".odt",
                        ".odp",
                    ]
                    for uploaded_file in request.FILES.getlist("input_files"):
                        # Extract file extension and check if it's a valid extension
                        ext = os.path.splitext(uploaded_file.name)[1].lower()  # type: ignore
                        if ext in valid_extensions:
                            new_file = File.objects.create(
                                user=request.user,  # type: ignore
                                conversion=conversion,
                                is_output=False,
                                is_input=True,
                                file=uploaded_file,
                            )
                            if uploaded_file.content_type is not None:
                                new_file.type = uploaded_file.content_type
                            input_files.append(new_file)
                        else:
                            # Invalid extension, return an error message
                            messages.error(
                                request,
                                "Invalid file type. Please upload either MS Word, MS PowerPoint, OpenDocument, RTF, PDF, or TXT files.",
                            )
                            return render(
                                request, "transform.html", {"form": TransformerForm()}
                            )

                    if has_template_file:
                        uploaded_template_file = request.FILES.getlist("template_file")[
                            0
                        ]
                        template_file = File.objects.create(
                            user=request.user,  # type: ignore
                            conversion=conversion,
                            is_input=False,
                            is_output=False,
                            file=uploaded_template_file,
                            type=str(uploaded_template_file.content_type),
                        )
                    else:
                        temp = TForm.cleaned_data["template"]
                        template_file = File.objects.get(file=f"template_{temp}.pptx")

                    conversion.template = template_file

                    conversion.save()
                    template_file.save()
                    result = generate_presentation(input_files, conversion)

                    return redirect("results", conversion_id=conversion.id)

                except Exception as e:
                    error(e)

                    conversion.delete()
                    for file in input_files:
                        file.delete()

                    if has_template_file:
                        template_file.delete()

                    if type(e) is MissingPlaceholderError:
                        messages.error(request, e.message)
                    else:
                        messages.error(
                            request,
                            "We encountered an unexpected error while generating your content please try again.",
                        )

                    return render(
                        request,
                        "transform.html",
                        {
                            "TForm": TransformerForm(),
                            "EForm": ExerciseForm(),
                        },
                    )
            elif EForm.is_valid():
                try:
                    excercise = Exercise.objects.create(  # type: ignore
                        prompt=EForm.cleaned_data["prompt"],
                        language=EForm.cleaned_data["language"],
                        complexity=EForm.cleaned_data["complexity"],
                        num_true_false=EForm.cleaned_data["num_true_false"],
                        num_multiple_choice=EForm.cleaned_data["num_multiple_choice"],
                        num_short_ans=EForm.cleaned_data["num_short_ans"],
                        model=EForm.cleaned_data["model"],
                        user=request.user,
                    )

                    has_prompt = len(excercise.prompt) > 0
                    has_file = len(request.FILES.getlist("input_files"))

                    has_template_selection = EForm.cleaned_data["template"] != ""
                    has_template_file = len(request.FILES.getlist("template_file"))
                    if not has_template_selection and not has_template_file:
                        messages.error(request, "No template provided.")
                        return render(
                            request,
                            "transform.html",
                            {
                                "TForm": TransformerForm(),
                                "EForm": ExerciseForm(),
                            },
                        )

                    if excercise.model == ModelChoice.GPT_4:
                        if not has_premium_subscription(request.user.id):  # type: ignore
                            messages.error(
                                request,
                                "You must have a premium subscription to use the GPT-4 model.",
                            )
                            return render(
                                request,
                                "transform.html",
                                {"TForm": TransformerForm(), "EForm": ExerciseForm()},
                            )

                    if not has_prompt and not has_file:
                        messages.error(
                            request, "Input must include a prompt and/or a file."
                        )
                        return render(
                            request,
                            "transform.html",
                            {
                                "TForm": TransformerForm(),
                                "EForm": ExerciseForm(),
                            },
                        )

                    for uploaded_file in request.FILES.getlist("input_files"):
                        new_file = File.objects.create(
                            user=request.user,  # type: ignore
                            exercise=excercise,
                            is_output=False,
                            is_input=True,
                            file=uploaded_file,
                        )

                        if uploaded_file.content_type is not None:
                            new_file.type = uploaded_file.content_type

                        input_files.append(new_file)

                    if has_template_file:
                        uploaded_template_file = request.FILES.getlist("template_file")[
                            0
                        ]
                        template_file = File.objects.create(
                            user=request.user,  # type: ignore
                            excercise=excercise,
                            is_input=False,
                            is_output=False,
                            file=uploaded_template_file,
                            type=str(uploaded_template_file.content_type),
                        )
                    else:
                        temp = EForm.cleaned_data["template"]
                        template_file = File.objects.get(file=f"template_{temp}.pptx")

                    excercise.template = template_file

                    excercise.save()
                    template_file.save()
                    result = generate_exercise(input_files, excercise)

                    return redirect("exercise_results", exercise_id=excercise.id)

                except Exception as e:
                    error(e)

                    excercise.delete()
                    for file in input_files:
                        file.delete()

                    if has_template_file:
                        template_file.delete()

                    if type(e) is MissingPlaceholderError:
                        messages.error(request, e.message)
                    else:
                        messages.error(
                            request,
                            "We encountered an unexpected error while generating your content please try again.",
                        )

                    return render(
                        request,
                        "transform.html",
                        {"TForm": TransformerForm(), "EForm": ExerciseForm()},
                    )
            else:
                for field, errors in TForm.errors.items():
                    if field != "__all__":
                        field_name = (
                            TForm.fields[field].label
                            if TForm.fields[field].label
                            else field
                        )
                        error_messages = "; ".join(
                            [force_str(error) for error in errors]
                        )
                        error_message = f"{field_name}: {error_messages}"
                    else:
                        error_messages = "; ".join(
                            [force_str(error) for error in errors]
                        )
                        error_message = error_messages

                    messages.error(request, error_message)
                for field, errors in EForm.errors.items():
                    if field != "__all__":
                        field_name = (
                            EForm.fields[field].label
                            if EForm.fields[field].label
                            else field
                        )
                        error_messages = "; ".join(
                            [force_str(error) for error in errors]
                        )
                        error_message = f"{field_name}: {error_messages}"
                    else:
                        error_messages = "; ".join(
                            [force_str(error) for error in errors]
                        )
                        error_message = error_messages

                    messages.error(request, error_message)
                return redirect("transform")
        else:
            TForm = TransformerForm()
            EForm = ExerciseForm()
            return render(
                request,
                "transform.html",
                {"TForm": TransformerForm(), "EForm": ExerciseForm()},
            )
    else:
        messages.error(request, "You must have an active subscription to use Create.")
        return redirect("store")


@login_required(login_url="login")
def results(request: HttpRequest, conversion_id: int) -> HttpResponse:
    conversion = get_object_or_404(Conversion, id=conversion_id)

    output_files = File.objects.filter(conversion=conversion, is_output=True)
    # output_files = File.objects.filter(conversion=conversion, is_output=True).order_by(
    #     "-id"
    # )[
    #     :2
    # ]  # This is very stupid but it works

    if request.user.is_authenticated:
        if conversion.user != request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )
    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )

    num_slides = 10

    for file in output_files:
        if file.type == "application/pdf":
            try:
                doc = fitz.open(file.file.path)
                num_slides = len(doc)
                doc.close()
                break
            except Exception as e:
                print(f"Failed to open PDF: {e}")

    repromptFormSet = formset_factory(RepromptForm)

    if request.method == "POST":
        formset = repromptFormSet(request.POST, form_kwargs={"num_slides": num_slides})
        if formset.is_valid():
            slides_to_update = []
            for form in formset:
                slide_number = form.cleaned_data.get("slide")
                prompt = str(form.cleaned_data.get("prompt"))
                is_image_slide = form.cleaned_data.get("image_slide")
                slide_type = SlideTypes.IMAGE if is_image_slide else SlideTypes.CONTENT

                if (
                    slide_number is not None
                    and prompt is not None
                    and slide_type is not None
                ):
                    slide_number = int(slide_number)
                    slides_to_update.append(
                        SlideToBeUpdated(slide_number, prompt, slide_type)
                    )

            new_conversion = reprompt_slides(slides_to_update, conversion)

            return redirect("results", conversion_id=new_conversion.id)
        else:
            return render(
                request,
                "results.html",
                {"output_files": output_files, "formset": formset},
            )
    else:
        formset = repromptFormSet(form_kwargs={"num_slides": num_slides})

    return render(
        request,
        "results.html",
        {"output_files": output_files, "formset": formset},
    )


@login_required(login_url="login")
def exercise_results(request: HttpRequest, exercise_id: int) -> HttpResponse:
    exercise = get_object_or_404(Exercise, id=exercise_id)

    output_files = File.objects.filter(exercise=exercise, is_output=True)

    if request.user.is_authenticated:
        if exercise.user != request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )
    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )

    num_slides = 10

    for file in output_files:
        if file.type == "application/pdf":
            try:
                doc = fitz.open(file.file.path)
                num_slides = len(doc)
                doc.close()
                break
            except Exception as e:
                print(f"Failed to open PDF: {e}")

    repromptFormSet = formset_factory(ExerciseRepromptForm)

    if request.method == "POST":
        formset = repromptFormSet(request.POST, form_kwargs={"num_slides": num_slides})
        if formset.is_valid():
            slides_to_update = []
            for form in formset:
                slide_number = form.cleaned_data.get("slide")
                prompt = str(form.cleaned_data.get("prompt"))
                slide_type = getattr(
                    SlideTypes, str(form.cleaned_data.get("slide_type"))
                )

                if (
                    slide_number is not None
                    and prompt is not None
                    and slide_type is not None
                ):
                    slide_number = int(slide_number)
                    slides_to_update.append(
                        SlideToBeUpdated(slide_number, prompt, slide_type)
                    )

            new_exercise = reprompt_slides(slides_to_update, exercise)

            return redirect("exercise_results", exercise_id=new_exercise.id)
        else:
            return render(
                request,
                "results.html",
                {"output_files": output_files, "formset": formset},
            )
    else:
        formset = repromptFormSet(form_kwargs={"num_slides": num_slides})

    return render(
        request,
        "results.html",
        {"output_files": output_files, "formset": formset},
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


@login_required(login_url="login")
def serve_file(request: HttpRequest, file_id: int) -> HttpResponse:
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
    response["Content-Disposition"] = f'inline; filename="{file.file.name}"'

    response["X-Frame-Options"] = "ALLOWALL"

    return response


@login_required(login_url="login")
def download_profile_pic(request: HttpRequest, user_id: int) -> HttpResponse:
    user = get_object_or_404(User, id=user_id)

    profile = get_object_or_404(Profile, user=user)

    if request.user.is_authenticated:
        if profile.user != request.user:
            return HttpResponseForbidden(
                "You do not have permission to access this resource."
            )
    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )

    image = profile.image
    response = HttpResponse(image.file, content_type="image/jpeg")
    response["Content-Disposition"] = f'attachment; filename="{image.file.name}"'
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
        start_date = date.today()
        end_date = start_date + timedelta(days=3)
        give_subscription_to_user(user, start_date, end_date, None)
        messages.success(request, "Email verified. You can now log into your account.")
        messages.success(request, "Enjoy a complimentary 3 day trial!")
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
    email.content_subtype = "html"
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
        user_exercises = (
            Exercise.objects.filter(user=request.user).order_by("-date").all()
        )

        history = {}
        exercise_history = {}

        for conversion in user_conversions:
            input_files = File.objects.filter(conversion=conversion, is_input=True)
            output_files = File.objects.filter(conversion=conversion, is_output=True)
            history[conversion] = {
                "input_files": input_files,
                "output_files": output_files,
            }

        for exercise in user_exercises:
            input_file = File.objects.filter(exercise=exercise, is_input=True)
            output_file = File.objects.filter(exercise=exercise, is_output=True)
            exercise_history[exercise] = {
                "input_files": input_file,
                "output_files": output_file,
            }

    else:
        return HttpResponseForbidden(
            "You do not have permission to access this resource."
        )
    return render(
        request,
        "history.html",
        {"history": history, "exercise_history": exercise_history},
    )


def store(request: HttpRequest) -> HttpResponse:
    products = Product.objects.all()
    return render(request, "store.html", {"products": products})


class CreateCheckoutSessionView(View):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # type: ignore
        if request.user.is_authenticated:
            product_id = self.kwargs["pk"]
            product = Product.objects.get(id=product_id)
            if (
                has_valid_subscription(request.user.id)
                and has_premium_subscription(request.user.id)
                and product.name != "Premium Subscription"
            ):
                messages.error(
                    request,
                    "Please purchase another premium subscription or cancel your existing subscription.",
                )
                return redirect("store")
            elif (
                has_valid_subscription(request.user.id)
                and has_premium_subscription(request.user.id) is False
                and product.name == "Premium Subscription"
            ):
                messages.error(
                    request,
                    "Please cancel your existing subscription before purchasing a premium subscription.",
                )
                return redirect("store")
            else:
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
        give_subscription_to_user(
            subscription_user, start_date, end_date, subscription_product
        )
    # Passed signature verification
    return HttpResponse(status=200)


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
        elif "delete" in request.POST:
            subscription_form = SubscriptionDeletionForm(request.POST)
            if subscription_form.is_valid() and subscription_form.cleaned_data.get(
                "delete"
            ):
                user = User.objects.get(id=request.user.id)  # type: ignore
                delete_subscription(user)
                messages.success(request, f"Your subscription has been deleted.")
        return redirect("profile")
    else:
        pic_form = ProfileUpdateForm(instance=request.user.profile)  # type: ignore
        e_form = UpdateEmailForm(instance=request.user)
        p_form = UpdatePasswordForm(user=request.user)  # type: ignore
        delete_form = AccountDeletionForm()
        subscription_form = SubscriptionDeletionForm()
        try:
            user = User.objects.get(id=request.user.id)  # type: ignore
            subscription = Subscription.objects.get(user=user)
            has_subscription = subscription.has_subscription
            premium = "Premium Subscription" if subscription.is_premium else None
            subscription_start = subscription.start_date
            subscription_expiry = subscription.end_date
        except:
            has_subscription = False
            premium = "No active subscription"
            subscription_start = "N/A"  # type: ignore
            subscription_expiry = "N/A"  # type: ignore
    context = {
        "pic_form": pic_form,
        "e_form": e_form,
        "p_form": p_form,
        "delete_form": delete_form,
        "subscription_form": subscription_form,
        "has_subscription": has_subscription,
        "premium": premium,
        "subscription_start": subscription_start,
        "subscription_expiry": subscription_expiry,
    }
    return render(request, "profile.html", context)
