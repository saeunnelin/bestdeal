#!/usr/bin/env python3

# =============================================================================
#                          Sæunn Elín Ragnarsdóttir
#                               Summer of 2020
#                            University of Iceland
# =============================================================================

import json
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import sqlite3

# =============================================================================
# For this code to work it's necessary to create an account on 
# CoinMarketCap.com. With a CMC account you get an API key that allows you 
# to run the second function of the Api class below. By running the code you 
# can find pricing information for all the cryptocurrencies listed on CMC. 

# The functions in the Api class allow you to get pricing information... 
# - directly from CoinMarketCap. 
# - from a CoinMarketCap JSON test file. 
# - from a database that stores selected info from the CoinMarketCap API. 
# =============================================================================

# First of all the class Api defined
class Api:
    
    # Then a few dictionaries are defined
    def __init__(self): 
        self.symbols = dict()
        self.cryptoprice = dict()
        self.change1h = dict()
        self.change24h = dict()
        self.change7d = dict()
        self.newestinfofromdb = dict()    
    
    # The following code can be found at 
    # https://coinmarketcap.com/api/documentation/v1/. 
    # Remember to insert the API key into the code. 
    def readfromCMC(self):
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
            
            # The first variable lists all the symbols in the API, the next 
            # all the prices and so on. 
            for info in data["data"]:
                symbol = info["symbol"]
                price = info["quote"]["USD"]["price"]
                h1 = info["quote"]["USD"]["percent_change_1h"]
                h24 = info["quote"]["USD"]["percent_change_24h"]
                d7 = info["quote"]["USD"]["percent_change_7d"]
                
                # By executing the following commands outside the class it's 
                # possible to get info about the price or price change of a 
                # cryptocurrency directly loaded from CMC
                self.cryptoprice[symbol] = price
                self.change1h[symbol] = h1
                self.change24h[symbol] = h24
                self.change7d[symbol] = d7
                self.symbols[symbol] = symbol
            
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
        return(symbol, price, h1, h24, d7)

    # The following function gets pricing information from a JSON test file.
    # FYI the JSON file cmc.json was created specifically for testing purposes. 
    def readfromfile(self, file):
        
        # The file is loaded into Python and saved as a variable
        with open(file) as f:
            data = json.load(f)
            
            # The first variable lists all the symbols in the file, the 
            # next all the prices and so on. 
            for info in data["data"]:
                symbol = info["symbol"]
                price = info["quote"]["USD"]["price"]
                h1 = info["quote"]["USD"]["percent_change_1h"]
                h24 = info["quote"]["USD"]["percent_change_24h"]
                d7 = info["quote"]["USD"]["percent_change_7d"]

                # By executing the following commands outside the class it's 
                # possible to get info about the price of a cryptocurrency 
                # from the JSON test file
                self.cryptoprice[symbol] = price
                self.change1h[symbol] = h1
                self.change24h[symbol] = h24
                self.change7d[symbol] = d7
                self.symbols[symbol] = symbol
    
    # The following function reads a database file that has info from CMC's API
    def readfromDB(self, file):
        
        # A connection is made to the following database file
        conn = sqlite3.connect(file)
        
        # Then a cursor is defined
        c = conn.cursor()
        
        # With the following SQLite command all the symbols in the database
        # are selected
        with conn:
            c.execute("SELECT symbol FROM CMCdata")
            
            # so the results can be used in the SQLite commands below.
            self.symbols = [x[0] for x in c.fetchall()]

        # The following SQLite commands select the prices and price changes 
        # for all the symbols. By fetching the results in this way the price
        # information for each cryptocurrency can be accessed outside the class
        for symbol in self.symbols:
            with conn:
                c.execute("SELECT price FROM CMCdata WHERE symbol=:symbol", 
                          {"symbol": symbol})
                self.cryptoprice[symbol] = c.fetchall()
        
            with conn:
                c.execute("SELECT hour FROM CMCdata WHERE symbol=:symbol", 
                          {"symbol": symbol})
                self.change1h[symbol] =  c.fetchall()
            
            with conn:
                c.execute("SELECT day FROM CMCdata WHERE symbol=:symbol", 
                          {"symbol": symbol})
                self.change24h[symbol] =  c.fetchall()
            
            with conn:
                c.execute("SELECT week FROM CMCdata WHERE symbol=:symbol", 
                          {"symbol": symbol})
                self.change7d[symbol] =  c.fetchall()
        
        # Both the connection and the cursor are then closed
        c.close()
        conn.close()
