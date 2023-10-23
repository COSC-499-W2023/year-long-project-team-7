from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("transform", views.transform, name="transform"),
    path("home", views.home, name='home'),
    path("about", views.about, name='about'),
    path("results", views.results, name='results'),
    path('signup', views.signup, name="signup"),
    path('signin', views.signin, name="signin"),
    path('signout', views.signout, name="signout"),
]
