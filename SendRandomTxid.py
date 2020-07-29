#!/usr/bin/env python3

# =============================================================================
#                          Sæunn Elín Ragnarsdóttir
#                               Summer of 2020
#                            University of Iceland
# =============================================================================

import json
import subprocess
import random 
from random import randrange
import binascii
import struct
import math
from ReadFromFile import Api

# The address of the DEX
DEX = "BH9DpL5P7xe87M6XTVQTk62Tjrv414XAQv"

# The Smileycoin-cli command
smlycmd = "/home/saeunnelin/smileyCoin/src/smileycoin-cli"

# The class Api from the API file
api = Api()

# Read info from the following database file
api.readfromDB("cmcdata.db")

# All the cryptocurrency symbols from the database
symbol = api.symbols

# =============================================================================
# The following class creates a random OP_RETURN for an offer that is sent 
# to the DEX. 
# =============================================================================

class OPRETURN:
    
    # A few dictionaries are defined
    def __init__(self): 
        self.amountsmly = dict()
        self.amountcrypto = dict()
        self.randsymbol = dict()
    
    # The following function creates random trading amounts for an OP_RETURN. 
    # See Excel file for further contemplations. 
    def randomamount(self, abbr):
        
        # The exchange rate of the two cryptocurrencies in USD
        smlyUSD = float(api.cryptoprice["SMLY"][0][0])
        cryptoUSD = float(api.cryptoprice[abbr][0][0])
        
        # The ratio SMLY/MYNT is defined
        smlycrypto = smlyUSD/cryptoUSD
        
        # Amounts defined
        smly = randrange(100,1100)
        crypto = smlycrypto*smly
        
        # Random percentages defined
        randpercentsmly = random.uniform(0.7,1.3)
        randpercentcrypto = random.uniform(0.7,1.3)
        
        # New amounts defined
        newsmly = smly*randpercentsmly
        newcrypto = crypto*randpercentcrypto
        
        # Inverse Satoshi
        satoshiinv = 10**8
        
        # Multiply the new trading amounts by the inverse Satoshi and change 
        # the type from FLOAT to INT
        self.amountsmly = math.floor(newsmly*satoshiinv)
        self.amountcrypto = math.floor(newcrypto*satoshiinv)

    # The following function creates a random OP_RETURN
    def randomopreturn(self):
        
        # The symbol of an offer
        send = 0
        
        # The symbol that tells whether the other cryptocurrency is being 
        # bought or sold chosen at random
        buyorsell = random.randint(0,1)
        
        # The abbreviation of the other cyptocurrency chosen randomly out 
        # of the CMC database
        randabbr = random.choice(list(symbol))
        
        # A new abbreviation is found if it has more than four letters
        while len(randabbr) > 4:
            randabbr = random.choice(list(symbol))
        
        # The abbreviation is chosen so that there are at least 75% chances 
        # that it's in the mycryptoaddress function
        randsymbol1 = [randabbr]*25 + ["BTC"]*25 + ["LTC"]*25 + ["SMLY"]*25
        randsymbol = random.choice(randsymbol1)

        # The abbreviation's hex string is filled with two zeros in the front 
        # if it has only three letters
        if len(randsymbol) == 3:
            hexsymb = ''.join([hex(ord(x))[2:] for x in randsymbol]).zfill(8)
        else:
            hexsymb = ''.join([hex(ord(x))[2:] for x in randsymbol])
        
        # Run the randomamount function on the cryptocurrency's abbreviation
        self.randomamount(randsymbol)
        
        # The random trading amounts of both currencies are determined
        amtcrypto = self.amountcrypto
        amtsmly = self.amountsmly
        
        # The trading amounts are then written in little endian format and the 
        # C type is changed to unsigned long long
        hexamtcrypto = struct.pack('<Q', amtcrypto)
        hexamtsmly = struct.pack('<Q', amtsmly)
        
        # The outcome above is changed to HEX format
        hexamtcrypto1 = binascii.hexlify(hexamtcrypto).decode("utf-8")
        hexamtsmly1 = binascii.hexlify(hexamtsmly).decode("utf-8")
        
        # The address on the other blockchain (this is a SMLY address for 
        # simplicity)
        cryptoaddr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        # The address is changed to HEX format
        hexaddr = ''.join([hex(ord(x))[2:] for x in cryptoaddr])
        
        # The OP_RETURN is defined
        opreturn = f"{send}{buyorsell}{hexsymb}{hexamtcrypto1}{hexamtsmly1}{hexaddr}"
        
        return(opreturn)

# =============================================================================
# The following function sends an offer to the DEX with a random OP_RETURN. 
# =============================================================================

# The OPRETURN class is defined so it can be refered to
opr = OPRETURN()

def sendtransaction():
    
    # The listunspent command is executed to find all utxo's in the wallet
    listunsp = subprocess.run([smlycmd, "listunspent"], capture_output=True)
    listunspent = json.loads(listunsp.stdout.decode("utf-8"))
    
    # A random amount is sent to the DEX
    amttodex = randrange(1,4)
    
    # Mining fee
    miningfee = 1
    
    # The utxos' balances are initialized 
    amtutxo = 0

    # VIN created: The following for-loop starts by listing the txid, VOUT 
    # and amount of the first utxo in the wallet
    VIN = "["
    for info in listunspent:
        txids = info["txid"]
        vouts = info["vout"]
        amtutxo += info["amount"]
        
        # The txid and VOUT are placed in a string that is used to create a 
        # rawtransaction later on
        VIN += f'{{"txid":"{txids}","vout":{vouts}}}' 
        
        # If the utxo covers the cost the loop is broken and the VIN string is ready
        if amtutxo >= amttodex + miningfee:
            break
        
        # If not, we continue adding utxos 'till there are enough to cover the cost.
        else:
            VIN += ","  
    VIN += "]"
        
    # A new SmileyCoin address is created
    newaddr = subprocess.run([smlycmd, "getnewaddress"], capture_output=True)
    newaddress = newaddr.stdout.decode("utf-8").strip()
    
    # A random OP_RETURN is found to send with the transaction
    opreturn = opr.randomopreturn()
    
    # If the VIN's utxos are exactly sufficient for the transaction and a 
    # mining fee...
    if amtutxo-amttodex == miningfee:
        
        # then the VOUT string is:
        VOUT = f'{{"{DEX}":{amttodex},"data":"{opreturn}:0"}}'
    
    # If not...     
    else:
        
        # the amount sent back to the bot is calculated
        amttome = amtutxo - miningfee - amttodex
        
        # and the VOUT string is:
        VOUT = f'{{"{DEX}":{amttodex},"{newaddress}":{amttome},"data":"{opreturn}:0"}}'

    # A raw transaction is created
    rawtx = subprocess.run([smlycmd, "createrawtransaction", VIN, VOUT], 
            capture_output = True)
    rawtxid = rawtx.stdout.decode("utf-8").strip()
    
    # The rawtransaction is signed
    sgnrawtx = subprocess.run([smlycmd, "signrawtransaction", rawtxid], 
            capture_output = True)
    sgnrawtxid = json.loads(sgnrawtx.stdout.decode("utf-8"))
    newhex = sgnrawtxid["hex"]

    # Finally an attempt is made to send the rawtransaction to the DEX
    sendrawtx = subprocess.run([smlycmd, "sendrawtransaction", newhex], 
        capture_output = True)
    
    # If an error appears, the error is saved in a string
    sendtxerror = sendrawtx.stderr.decode("utf-8").strip()
        
    # If there's no error the logger is notified of a successful transaction
    if not sendtxerror:
        sendrawtxid = sendrawtx.stdout.decode("utf-8").strip() 
        print(f"An offer was accepted. Txid: {sendrawtxid}")
        
    # Otherwise it's notified that a transaction could not be sent
    else:
        print("A transaction could not be sent due to the following {sendtxerror}. Txid: {txid}")
        return
    return
    
# =============================================================================
# The main function. 
# =============================================================================

if __name__ == "__main__":
    sendtransaction()
