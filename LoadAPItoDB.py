#!/usr/bin/env python3

# =============================================================================
#                          Sæunn Elín Ragnarsdóttir
#                               Summer of 2020
#                            University of Iceland
# =============================================================================

import sqlite3
from API import Api
import datetime

# =============================================================================
# This program saves data from CoinMarketCap to a database. 
# This program will be run every hour. 
# =============================================================================

# The class Api from the API file
api = Api()

# The Pricing information from CoinMarketCap is fetched directly         
api.readfromCMC()

# Connect to the following database file
conn = sqlite3.connect("cmcdata.db")
    
# A cursor is defined
c = conn.cursor()

# Date and time variable defined
datetime = datetime.datetime.now()

# The following function creates the SQLite table CMCdata
def createtable():
    c.execute("""DROP TABLE IF EXISTS CMCdata""")
    c.execute("""CREATE TABLE CMCdata 
              (date DATE, 
              symbol TEXT, 
              price REAL, 
              hour REAL, 
              day REAL, 
              week REAL)""")

# This function adds the following tuples to the table
def insertinfo(symbol):
    with conn:
        c.execute("INSERT INTO CMCdata VALUES (:date, :symbol, :price, :hour, :day, :week)", 
                  {"date": datetime, 
                   "symbol": api.symbols[symbol], 
                   "price": api.cryptoprice[symbol], 
                   "hour": api.change1h[symbol], 
                   "day": api.change24h[symbol], 
                   "week": api.change7d[symbol]})
    conn.commit()

# The table CMCdata is created and all the tuples are inserted
def main():
    createtable()
    for symbol in api.symbols:
        insertinfo(symbol)

if __name__ == "__main__":
    main()

# The connection and cursor are closed
c.close()
conn.close()

