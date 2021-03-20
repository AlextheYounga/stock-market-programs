from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.

def dashboard(request):
    template = loader.get_template("layouts/base.html")
    # context = {
    #     'latest_question_list': latest_question_list,
    # }
    return HttpResponse(template.render())

