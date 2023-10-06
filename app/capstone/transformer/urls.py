from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("transform", views.transform, name="transform")
]