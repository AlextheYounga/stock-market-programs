from app.lab.core.api.iex import IEX
from app.functions import dataSanityCheck
import colored
from colored import stylize
import json
import sys
from dotenv import load_dotenv
load_dotenv()


class StockFinancials():
    def lookup(self, ticker):
        iex = IEX()        
        cash_flow_json = iex.get('cash-flow', ticker)
        financials_json = iex.get('financials', ticker)
        stats = iex.get('stats', ticker, filters=['sharesOutstanding', 'peRatio'])
        advanced_stats = iex.get('advanced-stats', ticker, filters=['priceToSales', 'EBITDA', 'debtToEquity'])
        price = iex.get('price', ticker)
        if (None not in [cash_flow_json, financials_json, stats, advanced_stats, price]):
            financials = financials_json['financials'][0]
            cash_flow = cash_flow_json['cashflow'][0]

            capitalExpenditures = dataSanityCheck(cash_flow, 'capitalExpenditures')
            sharesOutstanding = dataSanityCheck(stats, 'sharesOutstanding')
            shareholderEquity = dataSanityCheck(financials, 'shareholderEquity')
            cashFlow = dataSanityCheck(cash_flow, 'cashFlow')
            longTermDebt = dataSanityCheck(financials, 'longTermDebt')
            totalAssets = dataSanityCheck(financials, 'totalAssets')
            totalLiabilities = dataSanityCheck(financials, 'totalLiabilities')

            freeCashFlow = capitalExpenditures - cashFlow if (capitalExpenditures and cashFlow) else 0
            freeCashFlowPerShare = freeCashFlow / sharesOutstanding if (freeCashFlow and sharesOutstanding) else 0
            freeCashFlowYield = freeCashFlowPerShare / price if (freeCashFlowPerShare and price) else 0
            longTermDebtToEquity = longTermDebt / shareholderEquity if (longTermDebt and shareholderEquity) else 0
            netWorth = totalAssets - totalLiabilities if (totalAssets and totalLiabilities) else 0


            data = {
                'price': price,
                'reportDate': financials.get('reportDate', None),
                'netIncome': financials.get('netIncome', None),
                'netWorth': netWorth,
                'shortTermDebt': financials.get('shortTermDebt', None),
                'longTermDebt': financials.get('longTermDebt', None),
                'totalCash': financials.get('totalCash', None),
                'totalDebt': financials.get('totalDebt', None),
                'debtToEquity': advanced_stats.get('debtToEquity', None),
                'priceToSales': advanced_stats.get('priceToSales', None),
                'EBITDA': advanced_stats.get('EBITDA', None),
                'freeCashFlow': freeCashFlow,
                'freeCashFlowPerShare': freeCashFlowPerShare,
                'freeCashFlowYield': freeCashFlowYield,
                'longTermDebtToEquity': longTermDebtToEquity,
            }

            for k, v in data.items():
                print(k +': '+str(v))
            
            return data
        else:
            print(stylize("Error: Could not fetch financials", colored.fg("red")))
