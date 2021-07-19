from app.lab.vix.vixvol import VixVol
from app.lab.news.newsfeed import NewsFeed

vixvol = VixVol()
nf = NewsFeed()
stocks = nf.mentionedStocks()

for stock in stocks:
    print(stock.ticker)
    vixvol.equation(stock.ticker)

