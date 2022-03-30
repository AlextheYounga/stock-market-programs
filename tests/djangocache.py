from django.core.cache import cache
from dotenv import load_dotenv
load_dotenv()

print(cache.get('senatewatch-api-data/transaction_report_for_05_26_2016.json'))