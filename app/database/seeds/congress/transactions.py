from app.lab.core.api.senatewatcher import SenateWatcher
from app.lab.core.api.housewatcher import HouseWatcher

hw = HouseWatcher()
sw = SenateWatcher()

sw.scanAllReports()
# hw.scanAllReports()
