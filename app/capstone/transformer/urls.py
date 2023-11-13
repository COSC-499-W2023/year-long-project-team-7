from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("transform", views.transform, name="transform"),
    path("signup", views.signup, name="signup"),
    path("signin", views.signin, name="signin"),
    path("signout", views.signout, name="signout"),
    path("about", views.about, name="about"),
    path("results/<int:conversion_id>/", views.results, name="results"),
]
