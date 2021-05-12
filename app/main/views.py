from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from ..lab.vix.equation import vix_equation

# Create your views here.

def dashboard(request):
    context = {}
    return render(request, 'dashboard.html', context)


def vix(request, ticker=None):
    template = loader.get_template('pages/vix/index.html')
    context = {
        'ticker': ticker,
    }

    if (ticker): 
        template = loader.get_template('pages/vix/show.html')
        # context['vix'] = vix_equation(ticker)

    return HttpResponse(template.render(context, request))
    

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
  
def news(request):
    context = {}
    path = 'pages/inflation/'
    page = 'index.html'

    return render(request, path+page, context)

def hurst(request, ticker):
    context = {}
    path = 'pages/hurst/'
    page = 'index.html'

    if (ticker):
        page = 'show.html'

    return render(request, path+page, context)



# def inflation(request, ticker):
#     context = {}
#     path = 'pages/inflation/'
#     page = 'index.html'

#     if (ticker):
#         page = 'show.html'

#     return render(request, path+page, context)