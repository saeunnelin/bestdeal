#!/usr/bin/env python3

# =============================================================================
#                          Sæunn Elín Ragnarsdóttir
#                               Summer of 2020
#                            University of Iceland
# =============================================================================

import sys
import json
import subprocess
import binascii
import struct
import math
from ReadFromFile import Api
import logging

# The address of the DEX
DEX = "BH9DpL5P7xe87M6XTVQTk62Tjrv414XAQv"

# The Smileycoin-cli command
smlycmd = "/home/saeunnelin/smileyCoin/src/smileycoin-cli"

# The class Api from the API file
api = Api()

# Info from the following database can now be obtained
api.readfromDB("cmcdata.db")

# =============================================================================
# In the following function the exchange rate crypto/USD is obtained for two 
# cryptocurrencies from CoinMarketCap's API. From these two exchange rates 
# the function calculates a specific 1-SMLY/crypto ratio. That ratio is useful 
# later on to determines whether an offer that is submitted to the DEX is 
# profitable for the bot or not. See Excel file for further contemplations. 
# =============================================================================
    
def profitorloss(abbr, amtcrypto, amtsmly):
    
    # The cryptocurrencies' exchange rate in US dollars
    cryptoUSD = float(api.cryptoprice[abbr][0][0])
    SMLYUSD = float(api.cryptoprice["SMLY"][0][0])
    
    # are multiplied by the amounts that are being exchange in the offer
    total_cryptoUSD = amtcrypto*cryptoUSD 
    total_SMLYUSD = amtsmly*SMLYUSD
    
    # and from there a 1-SMLY/crypto ratio is obtained.
    SMLYcryptoPercent = 1-total_SMLYUSD/total_cryptoUSD

    return (SMLYcryptoPercent)

# =============================================================================
# The following cryptocurrency abbreviations, symbol the cryptocurrencies the 
# bot is willing to trade for SmileyCoins. The function is supposed to create 
# a new address in the wallet of a chosen cryptocurrency. For simplicity 
# though, all of the following commands give new addresses from a SmileyCoin 
# wallet.
# =============================================================================

def mycryptoaddress(abbr):
    if abbr == "SMLY":
        newaddr = subprocess.run([smlycmd, "getnewaddress"], capture_output=True)
        mycryptoaddr = newaddr.stdout.decode("utf-8").strip()
    elif abbr == "BTC":
        newaddr = subprocess.run([smlycmd, "getnewaddress"], capture_output=True)
        mycryptoaddr = newaddr.stdout.decode("utf-8").strip()
    elif abbr == "LTC":
        newaddr = subprocess.run([smlycmd, "getnewaddress"], capture_output=True)
        mycryptoaddr = newaddr.stdout.decode("utf-8").strip()  
    else:
        mycryptoaddr = "None"
    return mycryptoaddr

# =============================================================================
# Similarly, the bot is supposed to find the balance in a wallet of a chosen 
# cryptocurrency. 
# =============================================================================

def mycryptobalance(abbr):
    if abbr == "BTC":
        balance = subprocess.run([smlycmd, "getbalance"], capture_output=True)
        balanceC = balance.stdout.decode("utf-8").strip()
        balanceCrypto = math.floor(float(balanceC))
    elif abbr == "LTC":
        balance = subprocess.run([smlycmd, "getbalance"], capture_output=True)
        balanceC = balance.stdout.decode("utf-8").strip()
        balanceCrypto = math.floor(float(balanceC))
    elif abbr == "SMLY":
        balance = subprocess.run([smlycmd, "getbalance"], capture_output=True)
        balanceC = balance.stdout.decode("utf-8").strip()
        balanceCrypto = math.floor(float(balanceC))
    else:
        balanceCrypto = "None"
    return (balanceCrypto)

# =============================================================================
# The following function takes in a HEX string, unhexlifies it, does a few 
# fomatting tricks and gives back a number. The number represents an amount
# of tokens an offeror is going to trade. 
# =============================================================================

def transformHEXtoNo(HEXamount):
    
    # The HEX string is changed to a string literal (byte format)        
    stringliteral = binascii.unhexlify(HEXamount)
    
    # The alignment of the bytes is changed from little endian. 
    # The C type is changed from unsigned long long.
    changedformat = struct.unpack('<Q', stringliteral)[0]
    
    # Satoshi
    satoshi = 10**-8
    
    # Finally the amount is multiplied by Satoshi
    amount = changedformat*satoshi
    
    return (amount)

# =============================================================================
# The smileycoin-cli command getrawtransction can be executed with Python by
# connecting Python to the SmileyCoin wallet. By executing the command it's 
# possible to find details of a transaction that has been sent on the 
# SmileyCoin blockchain. 
    
# This code reads a transaction ID and tells if the transaction was sent to 
# the DEX address. Most importantly though it interprets the txid's OP_RETURN, 
# if any can be found, and finds out with the profitorloss function if the 
# offer that was sent to the DEX address is profitable or not. 
# =============================================================================

def interpretopreturn(txid):
    
    # The raw transaction of the txid found
    rawtx = subprocess.run([smlycmd, "getrawtransaction", txid], 
            capture_output = True)
    rawtxid = rawtx.stdout.decode("utf-8").strip()
    
    # The rawtransaction decoded
    dcrawtx = subprocess.run([smlycmd, "decoderawtransaction", rawtxid], 
            capture_output = True)
    dcrawtxid = json.loads(dcrawtx.stdout.decode("utf-8"))
    
    # The address the transaction was sent to
    receivingaddr = dcrawtxid["vout"][0]["scriptPubKey"]["addresses"][0]
    
    # The address the reamaining tokens were sent to 
    remainingtokenaddr = dcrawtxid["vout"][1]["scriptPubKey"]["addresses"][0]
    
    # Transactions that were not sent to the DEX address are returned
    if DEX != receivingaddr:  
        logger.debug("The following transaction was not sent to the DEX address: " + txid)
        return
    
    # The HEX format of the OP_RETURN is located if it exists
    try:
        HEX = dcrawtxid["vout"][2]["scriptPubKey"]["hex"][4:]
    except Exception:
        logger.debug("No OP_RETURN was sent with the following transaction: " 
            + txid)
        return

    # By definition, the length of the OP_RETURN must be 112 bytes
    if len(HEX) != 110:
        logger.debug("Length of OP_RETURN incorrect. Txid: " + txid)
        return
    
    # Symbol located: Is the offer sent or accepted
    sentoraccepted = HEX[0]
    
    # Symbol located: Does the offeror mean to buy or sell the token 
    buyorsell = HEX[1]
    
    # The first letter of the other token's abbreviation is located
    firstabbr = HEX[2:4]
    
    # If an offer is being made
    if sentoraccepted == "0":
        
        # the offeror needs to be either selling or buying a token
        if buyorsell != "0" and buyorsell != "1":
            logger.debug("A cryptocurrency is neither being bought nor sold. ")
            return
        
        # The abbreviation of the other token
        if firstabbr == "00":
            abbr = bytes.fromhex(HEX[4:10]).decode("utf-8")
        else:
            abbr = bytes.fromhex(HEX[2:10]).decode("utf-8")
        
        # If the abbreviation matches a wallet on the bot's device the 
        # function finds a new address from said wallet
        mycryptoaddr = mycryptoaddress(abbr)
        if mycryptoaddr == "None":
            logger.debug("An exchange was attempted with a cryptocurrency the bot doesn't accept: " 
                         + abbr + ". ")
            return
        
        # The trading amounts are located           
        amtcryptoHEX = HEX[10:26]
        amtSMLYHEX = HEX[26:42]
        
        # and with the following function they're transformed from a HEX 
        # string to numbers
        amtcrypto = transformHEXtoNo(amtcryptoHEX)
        amtSMLY = transformHEXtoNo(amtSMLYHEX) 
        
        # Commands executed to find balances in both wallets 
        balanceCrypto = mycryptobalance(abbr)
        balanceSMLY = mycryptobalance("SMLY")
        
        # Mining fees for both cryptocurrencies
        miningfeeSMLY = 1
        miningfeeCrypto = 1      # 1 For simplicity
        
        # If the bot is selling the other cryptocurrency
        if buyorsell == "0":
            
            # it must have enough crypto tokens to accept the offer. 
            if balanceCrypto < amtcrypto + miningfeeCrypto:  
                logger.debug("There is not enough balance in " + abbr + 
                    " wallet to accept offer.")
                return
        
        # If the bot is selling SmileyCoins 
        elif buyorsell == "1":
            
            # it must have enough SmileyCoins to accept the offer. 
            if balanceSMLY < amtSMLY + miningfeeSMLY:
                logger.debug("There is not enough balance in SmileyCoin " + 
                    "wallet to accept offer.")
                return
            
        # Finally the profitorloss function is executed
        profitloss = profitorloss(abbr, amtcrypto, amtSMLY)
        
        ## The offer is not profitable for the bot if it's...
        
        # ... selling a token and the ratio is a positive number.
        if buyorsell == "0" and profitloss > 0:
            logger.debug("Unprofitable offer where ratio is -" + str(abs(profitloss)) + 
                  " SMLY/" + abbr + ". Txid: " + txid)
            return
        
        # ... buying a token and the ratio is a negative number. 
        elif buyorsell == "1" and profitloss < 0:
            logger.debug("Unprofitable offer where ratio is -" + str(abs(profitloss)) + 
                  " SMLY/" + abbr + ". Txid: " + txid)
            return  
        
        # Offer is accepted and a transaction is sent to the DEX address
        acceptoffer(amtSMLY, amtcrypto, abbr, txid, dcrawtxid)
        
    # If the DEX receives an accepted offer
    elif sentoraccepted == "1":
        
        # then the following is the transaction ID
        acceptedTxid = bytes.fromhex(HEX[2:132]).decode("utf-8")
        
        # and this the offeree's address
        offereeaddress = bytes.fromhex(HEX[132:]).decode("utf-8")
        
        logger.debug("An accepted offer sent to the DEX was accepted by: " + 
            offereeaddress + ". Txid: " + acceptedTxid)

        return()    
    else:
        logger.debug("Neither an offer nor an accepted offer were made. ")
        return  
    return

# =============================================================================
# By definition of the DEX all transactions that the DEX receives must have 
# an OP_RETURN in order for a smart contract to go through. The following 
# function creates the OP_RETURN of an accepted offer. 
# =============================================================================

def OP_RETURN(abbr, txid):
    
    # The txid converted to HEX format
    transid = ''.join([hex(ord(x))[2:] for x in txid])
    
    # The bot's address on the other blockchain
    mycryptoa = mycryptoaddress(abbr)
    
    # The address converted to HEX format 
    mycryptoaddr = ''.join([hex(ord(x))[2:] for x in mycryptoa])
    
    # The OP_RETURN on HEX format 
    opreturn = "02" + transid + mycryptoaddr
    
    return(opreturn)

# =============================================================================
# When it's been determined that an offer that the DEX receives is profitable 
# for the bot it needs to send a transaction to the DEX where it accepts the
# offer. The following function implements that transaction. 

# (When this code was created a transaction on the SMLY blockchain could not
# be sent with an OP_RETURN this long. Therefore, any transactions sent with 
# this function did not go through.)
# =============================================================================

def acceptoffer(amtSMLY, amtcrypto, abbr, txid, dcrawtxid):
    
    # The listunspent command is executed to find all utxo's in the wallet
    listunsp = subprocess.run([smlycmd, "listunspent"], capture_output=True)
    listunspent = json.loads(listunsp.stdout.decode("utf-8"))
    
    # In order to accept the offer the bot needs to send to the DEX the same 
    # fee the offeror originally sent to the DEX. 
    amttodex1 = dcrawtxid["vout"][0]["value"]
    amttodex = math.floor(float(amttodex1))
    
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
    newaddress = mycryptoaddress("SMLY")
    
    # The HEX formatted OP_RETURN is obtained with the following function
    opreturn = OP_RETURN(abbr, txid)
    
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
        logger.info("An offer was accepted. Txid: " + sendrawtxid)
        
    # Otherwise it's notified that a transaction could not be sent
    else:
        logger.error("A transaction could not be sent due to the following " 
            + sendtxerror + " Txid: " + txid)
        return
    return

# =============================================================================
# The following logger is defined in order to debug the program and save the 
# debugging to a log file. 
# =============================================================================

# Logger defined
logger = logging.getLogger(__name__)

# All levels from debug and above (info, warning, error and critical) allowed
logger.setLevel(logging.DEBUG)

# A stream handler defined
stream_handler = logging.StreamHandler()

# A file handler defined
file_handler = logging.FileHandler("bestdeal.log")

# The format of the handlers is chosen
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Finally the handlers are added to the logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# =============================================================================
# Main function
# =============================================================================

def main():
    
    # A few txids to test the code
    txid5 = "1a760c0cb4b5bbeeeceeaf5f58f6869ddf1fd41c0139a15ead27323a0da2efb5"
    txid6 = "e7262c8f83b34230567a63c9d569f83de904d17ff9b3ff6b48d7ef8dab8cbe02"
    txid7 = "3e1a138869dde8171f88fd6a76a8844310b573b082942aec4fb70733a7823b85"
    txid8 = "9987926e9139dfac46bd116caab5b51e507d9ef6b069ef53363b76f306bdef15"
    txid9 = "2882cfa50340561864765a2d4430dc36c4a2272a3eaa8b11c7e7b6768438e59e"
    txid10 = "900e0fca2fe5071fdb9f28b3a614fc5f0213dd4fd255be5eb1b12b2f37829d92"
    txid11 = "e23ccdbada43cbc99b68b98a5aae5d9cd7957ccb44cc1c8873a3d7529d243b86"
    txid12 = "d87d82536c7bb324788c6b048a73883615075631fbe50817fa7fdb7cf559394f"
    txid13 = "812d8541982cd91149ac3813ddcc169b1e6ba1990f633312eb70a67ccaf0acdd"
    
    # The function interpretopreturn is run on a selected txid
    interpretopreturn(txid13)
    
    # With WalletNotify the code runs on each txid that is sent on the blockchain
    #interpretopreturn(sys.argv[1])

if __name__ == "__main__":
    main()
