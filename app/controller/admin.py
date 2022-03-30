from django.contrib import admin
from ..database.models import *

admin.site.register(Stock)
admin.site.register(Hurst)
admin.site.register(Gold)
admin.site.register(Vix)
admin.site.register(News)
admin.site.register(StockNews)
admin.site.register(Reddit)
admin.site.register(Congress)
admin.site.register(CongressPortfolio)
admin.site.register(CongressTransaction)
