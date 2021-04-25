from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from ..lab.vix.equation import vix_equation

# Create your views here.

def dashboard(request):
    context = {}
    return render(request, 'dashboard.html', context)

def vix(request, ticker):
    context = {
        ticker: ticker,
    }
    page = 'pages/vix/index.html'
    # TODO: Figure out how to get context to show on view.
    if (ticker): 
        page = 'pages/vix/show.html'
        # context[vix] = vix_equation(ticker)

    return render(request, page, context)

def correlations(request, ticker):    
    context = {}
    path = 'pages/correlations/'
    page = 'index.html'

    if (ticker):
        page = 'show.html'

    return render(request, path+page, context)

def pricedingold(request, ticker):    
    context = {}
    path = 'pages/pricedingold/'
    page = 'index.html'

    if (ticker):
        page = 'show.html'

    return render(request, path+page, context)

def inflation(request, ticker):
    context = {}
    path = 'pages/inflation/'
    page = 'index.html'

    if (ticker):
        page = 'show.html'

    return render(request, path+page, context)

def rescaledrange(request, ticker):
    context = {}
    path = 'pages/rescaledrange/'
    page = 'index.html'

    if (ticker):
        page = 'show.html'

    return render(request, path+page, context)

