from django.shortcuts import render, redirect
from .forms import TransformerForm
from .models import *
import json
from .generator import *


def index(request):
    return render(request, 'index.html')


def transform(request):
    if request.method == 'POST':
        form = TransformerForm(request.POST)
        if form.is_valid():
            conversion = Conversion()
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
                new_file.type = uploaded_file.content_type
                new_file.file = uploaded_file
                new_file.save()
                files.append(new_file)
            try:
                result = generate_output(files, conversion)
            except:
                pass

            return redirect('results')
    else:
        form = TransformerForm()

    return render(request, 'transform.html', {'form': form})


def results(request):
    return render(request, 'results.html')


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')
