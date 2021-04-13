from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.

def dashboard(request):
    context = {}
    return render(request, 'dashboard.html', context)

def vix(request):
    context = {}
    return render(request, 'pages/vix.html', context)

def correlations(request):    
    context = {}
    return render(request, 'pages/correlations.html', context)

def pricedingold(request):    
    context = {}
    return render(request, 'pages/gold.html', context)

def inflation(request):
    context = {}
    return render(request, 'pages/inflation.html', context)

def rescaledrange(request):
    context = {}
    return render(request, 'pages/rescaledrange.html', context)

