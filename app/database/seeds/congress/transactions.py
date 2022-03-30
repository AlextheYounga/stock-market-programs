from app.lab.core.api.congresswatcher import CongressWatcher

hw = CongressWatcher(branch='house')
sw = CongressWatcher(branch='senate')

sw.scanAllReports()
hw.scanAllReports()
