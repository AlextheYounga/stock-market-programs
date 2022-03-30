from app.lab.core.api.senatewatcher import SenateWatcher
from app.lab.core.api.housewatcher import HouseWatcher
import django
from dotenv import load_dotenv
load_dotenv()
django.setup()
from app.database.models import Congress

# sw = SenateWatcher()
# sens = Congress.objects.filter(house='Senate')[:10]
# sw.tweet(sens)

hw = HouseWatcher()
reps = Congress.objects.filter(house='Senate')[:30]
hw.tweet(reps)