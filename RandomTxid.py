#!/usr/bin/env python3

import json
import subprocess
import random 
from random import randrange
import binascii
import struct
import math
from API import Api


# Sæki klasann úr Api úr API skjalinu
api = Api()

# CoinMarketCap skráin hlöðuð inn
api.readfromfile("verd.json")

# Veskisfang Kauphallarinnar
DEX = "BH9DpL5P7xe87M6XTVQTk62Tjrv414XAQv"

# Skipunin Smileycoin-cli 
smlycmd = "/home/saeunnelin/smileyCoin/src/smileycoin-cli"

# Öll rafmyntatáknin í API skránni sótt
symbol = api.symbols


# =============================================================================
# Föllin í eftirfarandi klasa útbúa handahófskennt OP_RETURN fyrir 
# tilboðsfærslu. 
# =============================================================================

class OPRETURN:
    
    # Tætitafla (e. dictionary) skilgreind
    def __init__(self): 
        self.amountsmly = dict()
        self.amountcrypto = dict()
        self.randsymbol = dict()
    
    # Fall sem býr til handahófskenndar upphæðir í OP_RETURN. 
    # Sjá Excel skjal.
    def randomamount(self, abbr):
        # Gengi rafmyntanna í dollurum
        smlyUSD = float(api.cryptoprice["SMLY"])
        cryptoUSD = float(api.cryptoprice[abbr])
        
        # Hlutfallið SMLY/MYNT skilgreint
        smlycrypto = smlyUSD/cryptoUSD
        
        # Handahófskenndar upphæðir skilgreindar
        smly = randrange(100,1100)
        crypto = smlycrypto*smly
        
        # Handahófskenndar prósentutölur skilgreindar
        randpercentsmly = random.uniform(0.7,1.3)
        randpercentcrypto = random.uniform(0.7,1.3)
        
        # Nýjar upphæðir skilgreindar
        newsmly = smly*randpercentsmly
        newcrypto = crypto*randpercentcrypto
        
        # Andhverfa Satoshi
        satoshiinv = 10**8
        
        # Margfalda með andhverfu Satoshi og breyti úr FLOAT í INT
        self.amountsmly = math.floor(newsmly*satoshiinv)
        self.amountcrypto = math.floor(newcrypto*satoshiinv)

    
    # Fall sem býr til handahófskennt OP_RETURN
    def randomopreturn(self):
        # Tákn tilboðsfærslu
        send = 0
        
        # Tákn kaup/sölutilboðsins valið af handahófi
        buyorsell = random.randint(0,1)
        
        # Skammstöfun rafmyntar valin af handahófi úr API skránni 
        randabbr = random.choice(list(symbol.values()))
        
        # Ný skammstöfun rafmyntar fundin ef bókstafir hennar eru 
        # fleiri en fjórir
        while len(randabbr) > 4:
            randabbr = random.choice(list(symbol.values()))
        
        # Skammstöfunin valin þannig að það séu a.m.k. 75% líkur á að 
        # hún sé í mycryptoaddress fallinu
        randsymbol1 = [randabbr]*25 + ["BTC"]*25 + ["LTC"]*25 + ["SMLY"]*25
        randsymbol = random.choice(randsymbol1)
        
        # Fyllt upp í hex streng skammst. með núllum þar sem á við
        if len(randsymbol) == 3:
            hexsymb = ''.join([hex(ord(x))[2:] for x in randsymbol]).zfill(8)
        else:
            hexsymb = ''.join([hex(ord(x))[2:] for x in randsymbol])
        
        # Randomamount fallið keyrt á skammstöfun rafmyntarinnar
        self.randomamount(randsymbol)
        
        # Handahófskenndar upphæðir rafmyntanna tveggja
        amtcrypto = self.amountcrypto
        amtsmly = self.amountsmly
        
        # Upphæðirnar skrifaðar á little endian sniði
        hexamtcrypto = struct.pack('<Q', amtcrypto)
        hexamtsmly = struct.pack('<Q', amtsmly)
        
        # Þeim síðan breytt á hex snið
        hexamtcrypto1 = binascii.hexlify(hexamtcrypto).decode("utf-8")
        hexamtsmly1 = binascii.hexlify(hexamtsmly).decode("utf-8")
        
        # Veskisfangið á hinni bálkakeðjunni
        cryptoaddr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        
        # Veskisfanginu breytt yfir á hex snið
        hexaddr = ''.join([hex(ord(x))[2:] for x in cryptoaddr])
        
        # OP_RETURN-ið skilgreint
        opreturn = f"{send}{buyorsell}{hexsymb}{hexamtcrypto1}{hexamtsmly1}{hexaddr}"
        
        return(opreturn)

# Gef klasanum annað heiti svo hægt sé að vísa í hann
opr = OPRETURN()

# =============================================================================
# Samþykktarfærsla send á kauphöllina með nýja OP_RETURN-inu
# =============================================================================

def sendtransaction():
    
    # Heildarupphæðin í broskallaveskinu mínu
    bal = subprocess.run([smlycmd, "getbalance"], capture_output=True)
    balance = json.loads(bal.stdout.decode("utf-8"))
    
    # Upphæð ónotaðra úttaka (utxo) frumstillt
    amtutxo = 0
    
    # Handahófskennt OP_RETURN fundið
    opreturn = opr.randomopreturn()
    
    # Upphæð broskalla úr randomamount fallinu 
    amtsmly = opr.amountsmly
    
    # Satoshi
    satoshi = 10**-8
    
    # Ef það er nóg inn á veskinu fyrir færsluna og námugjald...
    if balance >= amtsmly*satoshi+1:
        
        # Bý til nýtt veskisfang 
        newaddr = subprocess.run([smlycmd, "getnewaddress"], capture_output=True)
        newaddress = newaddr.stdout.decode("utf-8").strip()
        
        # Öll ónotuðu úttökin upptalin
        listunsp = subprocess.run([smlycmd, "listunspent"], capture_output=True)
        listunspent = json.loads(listunsp.stdout.decode("utf-8"))
        
        # VIN skilgreint 
        VIN = "["
        for i in listunspent:
            txids = i["txid"]
            vouts = i["vout"]
            amtutxo += i["amount"]
            VIN += f'{{"txid":"{txids}","vout":{vouts}}}' 
            
            # Hætta að bæta við færsluauðkennum þegar upphæð
            # þeirra dekka upphæð tilboðsins
            if amtutxo >= amtsmly*satoshi:
                break
            else:
                VIN += ","  
        VIN += "]"
        
        # Handahófskennd upphæð sem er send á kauphöllina
        amttodex = randrange(1,4)
        
        # Upphæðin sem er send aftur til baka til mín
        amttome = balance-amttodex-1
        
        # VOUT skilgreint
        VOUT = f'{{"{DEX}":{amttodex},"{newaddress}":{amttome},"data":"{opreturn}:0"}}'
        
        # Rawtransaction búið til
        rawtx = subprocess.run([smlycmd, "createrawtransaction", VIN, VOUT], capture_output = True)
        rawtxid = rawtx.stdout.decode("utf-8").strip()

        # Undirskrift fyrir rawtransaction 
        sgnrawtx = subprocess.run([smlycmd, "signrawtransaction", rawtxid], capture_output = True)
        sgnrawtxid = json.loads(sgnrawtx.stdout.decode("utf-8"))
        
        # Nýtt hex sem inniheldur einnig OP_RETURN-ið
        newhex = sgnrawtxid["hex"]
        
        # Rawtransaction sent
        sendrawtx = subprocess.run([smlycmd, "sendrawtransaction", newhex], capture_output = True)
        sendrawtxid = sendrawtx.stdout.decode("utf-8").strip()
        print(sendrawtxid)
        
        
        print(f"Færsla send á kauphöllina. Færsluauðkennið er: {sendrawtxid}")
    else:
        print("Ekki næg upphæð í veskinu til þess að taka tilboði. ")
        return()
    return()
    
    
if __name__ == "__main__":
    sendtransaction()





