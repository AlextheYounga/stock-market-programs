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

def vix(request):
    template = loader.get_template("pages/vix.html")
    # context = {
    #     'latest_question_list': latest_question_list,
    # }
    return HttpResponse(template.render())

def correlations(request):
    template = loader.get_template("pages/correlations.html")
    # context = {
    #     'latest_question_list': latest_question_list,
    # }
    return HttpResponse(template.render())

def pricedingold(request):
    template = loader.get_template("pages/gold.html")
    # context = {
    #     'latest_question_list': latest_question_list,
    # }
    return HttpResponse(template.render())

def inflation(request):
    template = loader.get_template("pages/inflation.html")
    # context = {
    #     'latest_question_list': latest_question_list,
    # }
    return HttpResponse(template.render())

def rescaledrange(request):
    template = loader.get_template("pages/rescaledrange.html")
    # context = {
    #     'latest_question_list': latest_question_list,
    # }
    return HttpResponse(template.render())

