from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'index.html')

def transform(request):
    return render(request, 'transform.html')

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')