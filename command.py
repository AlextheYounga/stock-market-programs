import os
import sys
import colored
from colored import stylize
from app.lab.core.output import printTabs, printFullTable
from dotenv import load_dotenv
load_dotenv()


def list_commands():
    headers = ['Command', 'Description']
    print('\n')
    print('Available Subcommands')
    print('No quotes required on [<ticker>] arguments, may be typed directly into the terminal.')
    print('\n\n')

    commands = [
        ['donchian [<ticker>] [days=30] [tweet]', 'Runs a donchian range calculation on a ticker'],
        ['financials [<ticker>]', 'Returns financials data for ticker, including some custom indicators not provided by IEX.'],
        ['macro:trends [timeframe=1m] [gain=20]', 'Scans all ETFs and returns the ETFs with the performance above an int (gain) within a timerange (5d, 1m, 3m, 1y)'],
        ['macro:gainers', 'Scans all ETFs and returns ETFs with highest day change.'],
        ['news:scrape [query=insert+string]', 'Searches a query and searches first 10 articles for stocks mentioned in article'],
        ['hurst [<ticker>] [timeframe=1y]', 'Runs a rescaled range analysis on a ticker. Output defaults to table.'],
        ['range [<ticker>] [tweet]', 'Runs a volatility range analysis on a ticker.'],
        ['reddit:scrape', 'Scrapes r/wallstreetbets for most talked-about stocks.'],
        ['historicalprices:get [<ticker>]', 'Fetches historical prices for a ticker and saves them to db.'],
        ['inflation:calculate [update]', 'Inflation index using etfs'],
        ['inflation:graph [update]', 'Graph inflation index using etfs'],
        ['inflation:functions [refresh]', 'Grabs max historical prices for all etfs in sectors list, updates with fresh data.'],
        ['trend:chase [pennies]', 'Scans all stocks and returns todays gainers with above certain thresholds (weeds out the penny stocks).'],
        ['trend:search [string=]', 'Scans stocks with string in stock name and looks for gainers'],
        ['trend:earnings', 'Scans all stocks and returns todays gainers who have consistently good earnings.'],
        ['trend:streak [<ticker>]', 'Determines the current winning/losing streak for a ticker'],
        ['trend:gainers', 'Grabs todays gainers and checks their earnings.'],
        ['trend:google', 'Searches google trends for search query interest'],
        ['pricedingold [<ticker>][timespan=5y][test=False]', 'Graphs and assets price in gold.'],
        ['vol:graph [<ticker>] [ndays=30]', 'Graphs vol'],
        ['volume:chase', 'Scans all stocks and returns todays gainers with abnormally high volume.'],
        ['volume:anomaly', 'Scans all stocks and returns stocks who are accumulating extremely high volume over the last week. Finds market singularities.'],
        ['volume:graph [<ticker>][timeframe=3m][sandbox=false]', 'Scans all stocks and returns stocks who are accumulating extremely high volume over the last week. Finds market singularities.'],
        ['vix [<ticker>]', 'Runs the VIX volatility equation on a ticker'],
        ['output:last', 'Returns the last cached output, can resort by specific key.'],
        ['rdb:export', 'Exports redisdb to zipped json file'],
        ['rdb:import', 'Import redisdb from a zipped json file'],
    ]
    printTabs(commands, headers, 'simple')
    print('\n\n')


def command_error(required={}, opt=None):
    if(not (required or opt)):
        print(stylize('Error: your command did not match any known programs. Closing...', colored.fg('red')))
        print('\n')
        return

    if (required):
        print(stylize('FAILED: Requires arguments: ', colored.fg('red')))
        for var, rules in required.items():
            print(stylize('({}) [{}] in position {}'.format(rules['type'], var, rules['pos']), colored.fg('red')))
        print('\n')
    if (opt):
        print(stylize('Optional arguments: ', colored.fg('yellow')))
        if (isinstance(opt, dict)):
            for var, typ in opt.items():
                print(stylize('({}) [{}]'.format(var, typ), colored.fg('yellow')))
        if (isinstance(opt, list)):
            for var in opt.items():
                print(stylize('[{}]'.format(var), colored.fg('yellow')))
            print('\n')


def parse_args(args, required=[], opt=[]):
    params = {}

    if (required):
        for req, rules in required.items():
            if ('=' in args[rules['pos']]):
                rv = args[rules['pos']].split('=')[1]
            else:
                rv = args[rules['pos']]

            params[req] = rv

    if (required and params == {}):
        command_error()
    if (opt):
        for var, rules in opt.items():
            in_args = [var == arg.split('=')[0] for arg in args]

            if (True in in_args):
                if (rules['type'] == bool):
                    if ('--' in var):
                        var = var.split('--')[1]
                    if ('=' in var):
                        argvalue = var.split('=')[1]
                    else:
                        argvalue = True

                    params[var] = argvalue
                    continue

                argvalue = args[in_args.index(True)].split('=')[1]

                if (rules['type'] == int):
                    if (isinstance(int(argvalue), int)):
                        params[var] = int(argvalue)
                        continue
                    else:
                        print(stylize(var+' must be of type '+str(rules['type']), colored.fg('red')))
                        sys.exit()

                params[var] = argvalue

    return params


def news_controller(subroutine, args=[]):
    if (subroutine == 'feed'):
        from app.lab.news.newsfeed import NewsFeed
        NewsFeed(aggregator='google').feed()

    command_error()

# def donchian_controller(args):
#     required = {'ticker': {'pos': 0, 'type': str}}
#     opt = {
#         'days': {'type': int, 'default': 30},
#         '--tweet': {'type': bool, 'default': False}
#     }

#     if (not args):
#         command_error(required, opt)
#         return

#     params = parse_args(args, required, opt)

#     from app.lab.donchian.range import calculate
#     print(calculate(
#         params['ticker'],
#         days=params['days'] if 'days' in params else opt['days']['default'],
#         sendtweet=True if ('tweet' in params) else opt['--tweet']['default']
#     ))


# def inflation_controller(subroutine, args=[]):
#     if (subroutine == 'graph'):
#         opt = {'--update': {'type': bool, 'default': False}}
#         params = parse_args(args, opt=opt)

#         from app.lab.inflation.measure import graph
#         print(graph(
#             update=params['update'] if ('update' in params) else opt['--update']['default']
#         ))
#         return

#     if (subroutine == 'calculate'):
#         opt = {'--update': {'type': bool, 'default': False}}
#         params = parse_args(args, opt=opt)

#         from app.lab.inflation.measure import annual

#         print(annual(
#             update=params['update'] if ('update' in params) else opt['--update']['default']
#         ))
#         return

#     command_error()


# def financials_controller(args):
#     required = {'string': 'ticker'}

#     if (not args):
#         command_error(required)
#         return

#     ticker = args[0]
#     from app.lab.financials.lookup import lookupFinancials
#     print(lookupFinancials(ticker))


# def macro_controller(subroutine, args=[]):
#     if (subroutine == 'trends'):
#         opt = {
#             'timeframe': {'type': str, 'default': '1m'},
#             'gain': {'type': int, 'default': 20}
#         }
#         params = parse_args(args, opt=opt)
#         from app.lab.macro.trends import calculate_trends

#         print(calculate_trends(
#             timeframe=params['timeframe'] if ('timeframe' in params) else opt['timeframe']['default'],
#             gain=params['gain'] if ('gain' in params) else opt['gain']['default'],
#         ))
#         return

#     if (subroutine == 'gainers'):
#         import app.lab.macro.gainers
#         return

#     command_error()


# def news_controller(subroutine, args=[]):
#     if (subroutine == 'feed'):
#         from app.lab.news.newsfeed import NewsFeed
#         nf = NewsFeed()
#         print(nf.feed())

#     command_error()


# def pricedingold_controller(args):
#     from app.lab.pricedingold.compare import price_in_gold
#     required = {'ticker': {'pos': 0, 'type': str}}
#     opt = {
#         'timeframe': {'type': str, 'default': '5y'},
#         'sandbox': {'type': bool, 'default': False}
#     }

#     if (not args):
#         command_error(required, opt)
#         return

#     params = parse_args(args, required, opt)

#     print(price_in_gold(
#         ticker=params['ticker'],
#         timeframe=params['timeframe'] if ('timeframe' in params) else opt['timeframe']['default'],
#         sandbox=params['sandbox'] if ('sandbox' in params) else opt['sandbox']['default'],
#     ))


# def hurst_controller(args):
#     required = {'ticker': {'pos': 0, 'type': str}}
#     opt = {
#         'timeframe': {'type': str, 'default': '1y'},
#         'output': {'type': str, 'default': 'table'},
#         '--tweet': {'type': bool, 'default': False}
#     }

#     if (not args):
#         command_error(required, opt)
#         return

#     from app.lab.hurst.fractal_calculator import fractal_calculator
#     params = parse_args(args, required, opt)

#     print(fractal_calculator(
#         ticker=params['ticker'],
#         output=params['output'] if ('output' in params) else opt['output']['default'],
#         timeframe=params['timeframe'] if ('timeframe' in params) else opt['timeframe']['default'],
#         sendtweet=params['tweet'] if ('tweet' in params) else opt['--tweet']['default'],
#     ))


# def rdb_controller(subroutine, args=[]):
#     if (subroutine == 'export'):
#         from app.lab.redisdb.export import export_rdb
#         export_rdb()
#     if (subroutine == 'import'):
#         from app.lab.redisdb.imports import import_rdb
#         import_rdb()


# def range_controller(args):

#     required = {'ticker': {'pos': 0, 'type': str}}
#     opt = {'--tweet': {'type': bool, 'default': False}}

#     if (not args):
#         command_error(required, opt)
#         return

#     from app.lab.riskrange.lookup import rangeLookup

#     params = parse_args(args, required, opt)

#     print(rangeLookup(
#         ticker=params['ticker'],
#         sendtweet=params['tweet'] if ('tweet' in params) else opt['--tweet']['default'],
#     ))


# def reddit_controller(subroutine, args):
#     if (subroutine == 'scrape'):
#         opt = {'--tweet': {'type': bool, 'default': False}}

#         from app.lab.reddit.api_scraper import scrapeWSB

#         params = parse_args(args, required=[], opt=opt)

#         print(scrapeWSB(
#             sendtweet=params['tweet'] if ('tweet' in params) else opt['--tweet']['default'],
#         ))


# def trend_controller(subroutine, args):

#     if (subroutine == 'streak'):
#         required = {'ticker': {'pos': 0, 'type': str}}
#         if (not args):
#             command_error(required)
#             return

#         from app.lab.trend.streak.count import count_streak
#         print(count_streak(args[0]))
#         return

#     if (subroutine == 'search'):
#         required = {'query': {'pos': 0, 'type': str}}

#         if (not args):
#             command_error(required)
#             return

#         from app.lab.trend.chase.search import search
#         params = parse_args(args, required)

#         print(search(params['query']))
#         return

#     if (subroutine == 'chase'):
#         from app.lab.trend.chaser import chase_trends
#         opt = {'pennies': {'type': bool, 'default': False}}
#         params = parse_args(args, opt=opt)
#         print(chase_trends(
#             pennies=params['pennies'] if ('pennies' in params) else opt['pennies']['default']
#         ))
#         return

#     if (subroutine == 'earnings'):
#         import app.lab.trend.chase.earnings
#         return

#     if (subroutine == 'gainers'):
#         import app.lab.trend.gainers
#         return
#     if (subroutine == 'google'):
#         from app.lab.trend.googletrends.request import stock_search_trends
#         print(stock_search_trends())
#         return

#     command_error()


# def vol_controller(subroutine, args):
#     required = {'ticker': {'pos': 0, 'type': str}}
#     opt = {'ndays': {'type': int, 'default': 30}}

#     if (not args):
#         command_error(required, opt)
#         return

#     if (subroutine == 'graph'):
#         from app.lab.vol.calculator import graphVol

#         params = parse_args(args, required, opt=opt)

#         print(graphVol(
#             params['ticker'],
#             ndays=params['ndays'] if ('ndays' in params) else opt['ndays']['default']
#         ))


# def volume_controller(subroutine, args):
#     if (subroutine == 'graph'):
#         required = {'ticker': {'pos': 0, 'type': str}}

#         if (not args):
#             command_error(required)
#             return

#         from app.lab.volume.graph import graph_volume
#         print(graph_volume(args[0]))

#     if (subroutine == 'chase'):
#         import app.lab.volume.chase

#     if (subroutine == 'anomaly'):
#         import app.lab.volume.anomaly


# def vix_controller(args):
#     required = {'ticker': {'pos': 0, 'type': str}}
#     opt = {
#         '--debug': {'type': bool, 'default': False},
#         '--dummy-data': {'type': bool, 'default': False},
#         '--tweet': {'type': bool, 'default': False},
#     }

#     if (not args):
#         command_error(required, opt)
#         return

#     from app.lab.vix.vix import vix_equation

#     params = parse_args(args, required, opt)

#     print(vix_equation(
#         params['ticker'],
#         sendtweet=params['tweet'] if ('tweet' in params) else opt['--tweet']['default'],
#         debug=params['debug'] if ('debug' in params) else opt['--debug']['default']
#     ))


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    sys.argv.pop(0)

    args = [arg.strip() for arg in sys.argv]

    if (args[0] == 'list'):
        list_commands()
        return

    if (':' in args[0]):
        command = args.pop(0)
        program = command.split(':')[0] + '_controller'
        subroutine = command.split(':')[1]

        globals()[program](subroutine, args)
        return
    else:
        program = args.pop(0) + '_controller'

        globals()[program](args)
        return


if __name__ == '__main__':
    main()
