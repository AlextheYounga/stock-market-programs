from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
import datetime
import requests
import colored
from colored import stylize
import sys


class Scraper():
    def __init__(self):
        self.timeout = 5
        self.storage = 'app/lab/scrape/storage'
        # TODO: Figure out best headers
        self.headers = {            
            'authority': 'www.bing.com',
            # 'method': 'POST',
            # 'scheme': 'https',
            # 'accept-encoding': 'gzip, deflate, br',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            # 'accept-language': 'en-US,en;q=0.9',
            'content-length': '0',
            'content-type': 'text/plain;charset=UTF-8',
            'origin': 'https://www.bing.com',
            'referer': 'https://www.bing.com/news/search?q=site%3Abloomberg.com&qs=n&form=QBNT&sp=-1&pq=site%3Abloomberg.&sc=0-15&sk=&cvid=E89FF9CF027441C19A8B7138BA2A486A',            
            'sec-ch-ua-arch': "x86",
            'sec-ch-ua-full-version': "91.0.4472.124",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'sec-ch-ua-platform-version': "10.0",
            # 'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # 'sec-fetch-site': 'none',
            # 'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

    def search(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
        except:
            print(stylize("Unexpected error:", colored.fg("red")))
            print(stylize(sys.exc_info()[0], colored.fg("red")))
            return False

        if (response.status_code == 200):
            time.sleep(1.3)
            return response
        return response.status_code

    def parseHTML(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        return (soup if (soup) else False)

    def stripParams(self, link):
        if ('?' in link):
            link = link.split('?')[0]
        if ('&' in link):
            link = link.split('&')[0]
        return link


# :authority: www.bing.com
# :method: POST
# :path: /fd/ls/GLinkPingPost.aspx?IG=95DF7A4731E447198685121695712D89&ID=news,5158.2
# :scheme: https
# accept: */*
# accept-encoding: gzip, deflate, br
# accept-language: en-US,en;q=0.9
# content-length: 0
# content-type: text/plain;charset=UTF-8
# cookie: MUID=1749841DC48B6E81104E8BD6C5B66FE7; SRCHD=AF=NOFORM; SRCHUID=V=2&GUID=3DF1BBFD29824BD39772EB6B605935CB&dmnchg=1; MUIDB=1749841DC48B6E81104E8BD6C5B66FE7; ANON=A=0D75BB99C55776627F0A457BFFFFFFFF&E=1984&W=1; NAP=V=1.9&E=192a&C=mhlJu8g5cwuj2ualjpcxYgkEtrROmCBQcjlA-N6tb5_HtTLDRekSZg&W=1; PPLState=1; SRCHS=PC=U316; _EDGE_S=SID=05A398C2786D6C5A385C888079B46D4C&mkt=en-us&ui=en-us; MultiLang=CIB=1; imgv=flts=20210624; ASPSESSIONIDSCRSDTRR=OHIFLMOBJNOLKJNHLECOGNIF; _SS=SID=05AF228B6A92692B014D32CB6B4B6829&R=200&RB=0&GB=0&RG=200&RP=200&PC=U316&h5comp=0; KievRPSSecAuth=FAByBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACMZeVt5uOXAqMARB9HBTtk8jevZG2gRZU0BtHss4n9V9xtvonWYTrPNvzkEYlP9CZte/QSlROEFRcOrIN6aGWbUuTXQSC1HBot4xdarSY8z2HWIjMfJIn49/92fepstVsghDKv4vegPVxAml+oPsOcruO8fXzbeSIRl/hkKyFqnEAtgQBUnoPnSA2A25W/QUiIVpFz4eoU676GtwbiL771t3WaoSiGGSuwiUSaNhUVN0HDViEBIn4GOFeCrXDh04qK9BOfqKwsZbtRXSoojYii75/Lwh58ccux1l2sb81GThZ5Jd1sgv2QNSswnqBAPlt4UCqUiwGNcPcN/w0MQ3dHFvaICw8KOg+DQ4Xq1jBFFtLEHWjsi8j2P0VJtiyQSEteC4s19fwelksBSsGoP9IO/ShF3PQ4I4qeGs4IsujRuCPhs0kTu+yNBosAZKMwbZxll4cCHtrmI4/XENN7Dc2IZEmhgrMIR7Hyb9CS6xZhlAm14WDz7U3LJtqH+PYXUDXFSnOfF9M+hU9+TCfZuN0Yp0ymF3bB9XkqeHwUjcXZ89XYfxwVQQwxAe/PKm/ezXFYGJr6w17KwhP6/FT22QDW1acSfsJUY7IYrz6V8kCn5rPPBVWXZs0fWfz9zSo0RyDH/XlbbEDdJfYvVXZsezSE08xkkswDbYUDi6JHS0HOPVHgX93v6o5lYijf/pWKfo1EsAF1ahobnB8XsAfX/+o+hU1lyTv+jAxQJd2u89KUIFWN66ED7/g+Dbap3scy9AJoKvv9LMhTOcsBCyZzKWUlWJEoa0nLzKtubjm4OD01sliwXUoc6ogjwld/uXFc2AG1m8+Jm2cwZWq+5BSjLlcI6KTnM1fNV4P2bOhROT2UM+0rB9+z1cUFIJm4CLgBRy4IFzrPHVun6SqtK4Chox7trsHyQIoK95SBD0sy5MBl7tesqIXYQEb8eLplxzExS3tyL+02rjt6cuAyMXMyxj6sfjJxKG+3nCnlLW7/vHlJhS6ONzh9yvW6Ikcfh2XbORkRwrTiuHY70HQpyKDEsgRe0UiD/LjM6qMIrGa/opK3o8GKg2dnWJOeyCHkBvB59X4e/W8vvP9OfrVSXg2lvSfzUOhYviZ3YOj0+Noec9tf9DXKVUp0lHRG2XHJ4vQlpyPLXxsjZmIBVTyeZrP9/U3V+YxDANrFMn5HpAMK5S68VLYP4TOWpb9R89NSZfJIRxO7niCXQVp7qNYlvBx2yuPWhzEhyKaiFPJbVligZ+TtOtJ7O5PGfM0G0XtuhL07/F28YnqB7cvyK2JHTRA9z4vNeC6eupyrS/f8F8Ts6oEMM8kJsEJoSF82qAjskP4ueEJR5eCDcS+R6bWFf5gr3ArXrMjCQvp/9XAdf8yWnAYv9NtQrEpiA1PCcJpiLoqpqiAS8B9DOcWw/NoV5cMe5zq58jjl96L/lCICxNFABfI6uEyoOgq8XfbjVStEB1EznIEQ==; _U=1ArfV6z5-hmD7bKAam_agf1QPMoz8wFmxiqWUjy-CAu20himrRkf2X0j2Xcqv2gfT7dMM5TCkGLVbjQxY-C5l5p1t8LIee7tvletMFSqTzzZfarDHjk_xVnN4ENLz3Te85xD3s5412PlugS_OyvAYQ4Lhycso7hJNQht-D2HIWqgVxL1EQr1n5TlZDvZ8vAoj; WLS=C=ed1f3516a76cebdd&N=Alex; WLID=TlLlbz72XcPwimsn1FvIY9KEN8eKMxqkNep4zkEVF9jDcKbG7fZa/jG/hByI5tugxrGT5VM/yLNQAo5XAiawcYee4THO6itGuTj5JtFrcX0=; ASPSESSIONIDACSTSRAB=JDKMKBBBONDLECOCPBDDEPOM; MicrosoftApplicationsTelemetryDeviceId=d2c3b31a-9725-41e9-8007-9f4b9f0efc60; MSFPC=GUID=cc267c02846b4065ac769939ea9677c4&HASH=cc26&LV=202101&V=4&LU=1611633585110; taboola_session_id=v2_50c2525da4c8a164b0ac7520b4e46666_1749841DC48B6E81104E8BD6C5B66FE7_1625962088_1625962088_CIi3jgYQhpxRGIem_Lmy6Nb3CCABKAUw4QE4kaQOQPG-Dki2zNkDULEEWABg4AloqtT02YSY-IJs; ipv6=hit=1626095811651&t=4; SRCHUSR=DOB=20210210&T=1626091773000&TPC=1626093731000&POEX=W; _HPVN=CS=eyJQbiI6eyJDbiI6MzAsIlN0IjoyLCJRcyI6MCwiUHJvZCI6IlAifSwiU2MiOnsiQ24iOjMwLCJTdCI6MCwiUXMiOjAsIlByb2QiOiJIIn0sIlF6Ijp7IkNuIjozMCwiU3QiOjEsIlFzIjowLCJQcm9kIjoiVCJ9LCJBcCI6dHJ1ZSwiTXV0ZSI6dHJ1ZSwiTGFkIjoiMjAyMS0wNy0xMlQwMDowMDowMFoiLCJJb3RkIjowLCJEZnQiOm51bGwsIk12cyI6MCwiRmx0IjowLCJJbXAiOjExMzJ9; ABDEF=V=13&ABDV=11&MRNB=1626094447685&MRB=0; _BINGNEWS=SW=950&SH=740; _RwBf=mtu=0&g=0&cid=&o=2&p=&c=&t=0&s=0001-01-01T00:00:00.0000000+00:00&ts=2021-07-12T12:54:25.7164431+00:00&rwred=0; SRCHHPGUSR=SRCHLANGV2=en&BRW=HTP&BRH=M&CW=967&CH=740&DPR=1&UTC=-240&DM=1&HV=1626094466&WTS=63761088966&BLOCK=N&RL=0&DLOC=LAT=30.309309799999998|LON=-81.50476640000001|A=null|N=Arlington%2C%20Duval%20Co.|C=|S=|TS=210630133018|ETS=210630134018|&SRCHLANG=en
# origin: https://www.bing.com
# referer: https://www.bing.com/news/search?q=site%3Abloomberg.com&qs=n&form=QBNT&sp=-1&pq=site%3Abloomberg.&sc=0-15&sk=&cvid=E89FF9CF027441C19A8B7138BA2A486A
# sec-ch-ua: " Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"
# sec-ch-ua-arch: "x86"
# sec-ch-ua-full-version: "91.0.4472.124"
# sec-ch-ua-mobile: ?0
# sec-ch-ua-model
# sec-ch-ua-platform: "Windows"
# sec-ch-ua-platform-version: "10.0"
# sec-fetch-dest: empty
# sec-fetch-mode: no-cors
# sec-fetch-site: same-origin
# user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36