from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("transform", views.transform, name="transform"),
    path("register", views.register, name="register"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("about", views.about, name="about"),
    path("history", views.history, name="history"),
    path("store", views.store, name="store"),
    path("payments", views.payments, name="payments"),
    path("results/<int:conversion_id>/", views.results, name="results"),
]
