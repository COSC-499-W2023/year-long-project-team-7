from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from .forms import TransformerForm
from .models import Conversion, File
from typing import List, Dict
import json
from .generator import *

def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def transform(request: HttpRequest) -> HttpResponse:

    if request.method == 'POST':

        form: TransformerForm = TransformerForm(request.POST)

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

            files: List[File] = []
        
            for uploaded_file in request.FILES.getlist('files'):
                new_file: File = File()
                new_file.user = request.user if request.user.is_authenticated else None
                new_file.conversion = conversion
                if uploaded_file.content_type is not None:  # Add this check
                    new_file.type = uploaded_file.content_type
                new_file.file = uploaded_file
                new_file.save()
                files.append(new_file)
            try:
                result: Dict = generate_output(files, conversion)
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