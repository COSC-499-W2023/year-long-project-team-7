from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm

urlpatterns = [
    path("", views.index, name="index"),
    path("transform", views.transform, name="transform"),
    path("exercise", views.exercise, name="exercise"),
    path("register", views.register, name="register"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("about", views.about, name="about"),
    path("history", views.history, name="history"),
    path("store", views.store, name="store"),
    path("results/<int:conversion_id>/", views.results, name="results"),
    path("exercise_results/<int:exercise_id>/", views.exercise_results, name="exercise_results"),
    path("profile", views.profile, name="profile"),
    path(
        "create-checkout-session/<int:pk>/",
        views.CreateCheckoutSessionView.as_view(),
        name="create-checkout-session",
    ),
    path("success", views.success, name="success"),
    path("cancel", views.cancel, name="cancel"),
    path("webhook", views.stripe_webhook, name="webhook"),
    path("activate/<uidb64>/<token>", views.activate, name="activate"),
    path("download_file/<int:file_id>/<int:flag>/", views.download_file, name="download_file"),
    path(
        "download_profile_pic/<int:user_id>/",
        views.download_profile_pic,
        name="download_profile_pic",
    ),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset_form.html",
            email_template_name="password_reset_email.html",  # plain text template (fallback)
            html_email_template_name="password_reset_email.html",  # HTML template
            subject_template_name="password_reset_subject.txt",
            success_url="/password_reset/done/",
            form_class=CustomPasswordResetForm,  # custom form here
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html", success_url="/reset/done/"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
