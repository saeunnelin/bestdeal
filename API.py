#!/usr/bin/env python3

import json
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import sqlite3


# Klasinn API skilgreindur svo hægt sé að nota föllin hér í öðrum skjölum
class Api:
    
    # Nokkrar tætitöflur (e. dictionary) skilgreindar
    def __init__(self): 
        self.symbols = dict()
        self.cryptoprice = dict()
        self.change1h = dict()
        self.change24h = dict()
        self.change7d = dict()
    
    # Fall sem les inn JSON skjal frá CMC og finnur úr því upplýsingar
    def readfromfile(self, file):
        
        # JSON skránni hlaðið inn í Python og hún vistuð sem breyta
        with open(file) as f:
            data = json.load(f)
            
            # Les inn eftirfarandi upplýsingar úr skjalinu f. allar myntirnar
            for info in data["data"]:
                symbol = info["symbol"]
                price = info["quote"]["USD"]["price"]
                h1 = info["quote"]["USD"]["percent_change_1h"]
                h24 = info["quote"]["USD"]["percent_change_24h"]
                d7 = info["quote"]["USD"]["percent_change_7d"]

                # Í gegnum klasann er hægt að nálgast eftirfarandi upplýsingar 
                # úr skjalinu fyrir hverja mynt
                self.cryptoprice[symbol] = price
                self.change1h[symbol] = h1
                self.change24h[symbol] = h24
                self.change7d[symbol] = d7
                self.symbols[symbol] = symbol
    
    ## Á eftir að skilgreina ##
    def readfromDB(self, file):
        
        #with Database() as db:
        #    db.create_table()
    
        pass

    # Eftirfarandi kóða má finna á slóðinni https://coinmarketcap.com/api/documentation/v1/. 
    # Nauðsynlegt er að hafa aðgang að CMC og sækja API lykil til þess að 
    # hann virki. Í hvert skipti sem kóðinn er keyrður sækir hann gengis- 
    # upplýsingar um allar rafmyntirnar sem skráðar eru á CMC. 
    def datafromCMC(self):
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        parameters = {
                'start':'1',
                'limit':'5000',
                'convert':'USD'
                }
        headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': '49813649-79e6-4416-a97b-1141fb4b205c',
                }
        
        session = Session()
        session.headers.update(headers)
            
        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            print(data)
            
            # Eftirfarandi gögn eru eingöngu sótt
            for info in data["data"]:
                symbol = info["symbol"]
                price = info["quote"]["USD"]["price"]
                h1 = info["quote"]["USD"]["percent_change_1h"]
                h24 = info["quote"]["USD"]["percent_change_24h"]
                d7 = info["quote"]["USD"]["percent_change_7d"]
                
                self.cryptoprice[symbol] = price
                self.change1h[symbol] = h1
                self.change24h[symbol] = h24
                self.change7d[symbol] = d7
                self.symbols[symbol] = symbol
            
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
        return(symbol, price, h1, h24, d7)
                    










