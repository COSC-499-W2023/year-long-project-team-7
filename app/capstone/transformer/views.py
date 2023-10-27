from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import TransformerForm
from .models import Conversion, File
from typing import List, Dict
import json
from .generator import *

def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def transform(request: HttpRequest) -> HttpResponse:

    if request.method == 'POST':

        form = TransformerForm(request.POST)

        if form.is_valid():
            conversion: Conversion = Conversion()
            user_params = {
                'text_input': form.cleaned_data['text_input'],
                'language': form.cleaned_data['language'],
                'complexity': form.cleaned_data['complexity'],
                'length': form.cleaned_data['length'],
            }
            conversion.user_parameters = json.dumps(user_params)
            conversion.save()

            files = []
        
            for uploaded_file in request.FILES.getlist('files'):
                new_file = File()
                new_file.user = request.user if request.user.is_authenticated else None
                new_file.conversion = conversion
                if uploaded_file.content_type is not None:
                    new_file.type = uploaded_file.content_type
                new_file.file = uploaded_file
                new_file.save()
                files.append(new_file)
            try:
                result = generate_output(files, conversion)
            except:
                pass

            return redirect('results')        

    return render(request, 'transform.html', {'form': TransformerForm()})

def results(request: HttpRequest) -> HttpResponse:
    return render(request, 'results.html')

def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'home.html')

def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'about.html')

def signup(request: HttpRequest) -> HttpResponse:
    
    # Create new user based on user input
    if request.method == "POST":
        username: str = request.POST.get('username')
        fname: str = request.POST.get("fname")
        lname: str = request.POST.get("lname")
        email: str = request.POST.get("email")
        pass1: str = request.POST.get("pass1")
        pass2: str = request.POST.get("pass2")

        myuser: User = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname

        myuser.save()

        messages.success(request, "Account successfully created.")

        return redirect('signin')

    return render(request, 'signup.html')

def signin(request: HttpRequest) -> HttpResponse:
    
    if request.method == 'POST':
        username: str = request.POST.get("username")
        pass1: str = request.POST.get("pass1")

        user = authenticate(request, username=username, password=pass1)

        if user is not None:
            login(request, user)
            fname: str = user.first_name
            return render(request, "home.html", {'fname': fname})

        else:
            messages.error(request, "Incorrect Credentials.")
            return redirect('home')

    return render(request, 'signin.html')

def signout(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Logged Out Successfully.")
    return redirect('home')
