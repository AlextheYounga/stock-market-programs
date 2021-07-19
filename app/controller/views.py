from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.template import RequestContext
from app.database.models import Vix
from app.lab.news.newsfeed import NewsFeed
from app.database.models import News
# Create your views here.

def dashboard(request):
    news = News()
    stocks_mentioned = news.latest_stocks_mentioned()
    for stock in stocks_mentioned:
        stock['vix'] = Vix().get(stock['ticker']) or 'NA'
        # TODO: Make color work
        stock['changeColor'] = 'green' if (stock.get('changePercent', False) and stock['changePercent'] > 0) else 'red'
        print(stock)

    context = {
        'news': news.latest_news(),
        'stocks_mentioned': stocks_mentioned
        }    
    return render(request, 'dashboard.html', context)


def vix(request, ticker=None):
    template = loader.get_template('pages/vix/index.html')
    context = {
        'ticker': ticker,
    }

    if (ticker): 
        # vix = vix_equation(ticker)
        if (vix):
            template = loader.get_template('pages/vix/show.html')
            # context['vix'] = vix
        else:
            handler404(request)

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


def handler404(request, *args, **argv):
    response = render('404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request, *args, **argv):
    response = render('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response



# def inflation(request, ticker):
#     context = {}
#     path = 'pages/inflation/'
#     page = 'index.html'

#     if (ticker):
#         page = 'show.html'

#     return render(request, path+page, context)