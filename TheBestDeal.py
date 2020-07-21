#!/usr/bin/env python3

import sys
import json
import subprocess
import binascii
import struct
import math
import sqlite3
from API import Api
import logging


# Veskisfang kauphallarinnar
DEX = "BH9DpL5P7xe87M6XTVQTk62Tjrv414XAQv"

# Skipunin Smileycoin-cli
smlycmd = "/home/saeunnelin/smileyCoin/src/smileycoin-cli"

# Sæki klasann Api úr API skjalinu
api = Api()

# CoinMarketCap skráin hlöðuð inn
api.readfromfile("verd.json")

# =============================================================================
# Eftirfarandi fall segir til um hvort hlutfall af upphæðum tveggja 
# rafmynta sem verið er að skipta á sé á undirvirði eða yfirvirði 
# (SMLY/MYNT). Sjá Excel skjal. 
# =============================================================================
    
def profit_loss(abbr, amtcrypto, amtsmly):
        
    # Gengi rafmyntanna í dollurum
    cryptoUSD = float(api.cryptoprice[abbr])
    SMLYUSD = float(api.cryptoprice["SMLY"])
    
    # Heildarverð rafmyntanna í dollurum
    total_cryptoUSD = amtcrypto*cryptoUSD 
    total_SMLYUSD = amtsmly*SMLYUSD
    
    # Undirvirði eða yfirvirði (SMLY/MYNT)
    SMLYcryptoPercent = 1-total_SMLYUSD/total_cryptoUSD

    return (SMLYcryptoPercent)


# =============================================================================
# Í eftirfarandi falli sést hvaða veski tilheyra mér á öðrum bálkakeðjum
# ásamt þeim veskisföngum sem tilheyra samsvarandi bálkakeðju. 
# =============================================================================

# Framtíðarverkefni er að sækja t.d. Bitcoin veski og framkvæma 
# skipunina bitcoin-cli getnewaddress í hvert skipti sem kóðinn minn vill 
# samþykkja tilboð. Til einföldunar eru þetta veskisföng sem ég bjó til á 
# broskallakeðjunni. 

def mycryptoaddress(abbr):
    if abbr == "BTC":
        mycryptoaddr = "BLZcBPvapVpY9A22bk4xWHAjEnAc6th7qd"
    elif abbr == "LTC":
        mycryptoaddr = "BGdbdDN2pt2e2UrBX3oqNWQKcBVeqkUqj6"
    elif abbr == "SMLY":
        mycryptoaddr = "B8PknxpWgoHUiTCBTGCsEBBQEavqS54iyq"
    else:
        mycryptoaddr = "None"
    return (mycryptoaddr)

# =============================================================================
# Eftirfarandi fall túlkar OP_RETURN færslu sem send er á Kauphöllina. Ef 
# tilboðfærsla er hagstæð og öll skilyrði eru uppfyllt er samþykktarfærsla 
# að lokum send á Kauphöllina. 
# =============================================================================

def interpretopreturn(txid):
    sendorreceive = ""
    buyorsell = ""
    abbr = ""
    amtcrypto = ""
    amtSMLY = ""
    address = ""
    acceptedofferTxid = ""
    cryptoaddr = ""
    
    # Rawtransaction af færsluauðkenninu (txid)
    rawtx = subprocess.run([smlycmd, "getrawtransaction", txid], 
            capture_output = True)
    rawtxid = rawtx.stdout.decode("utf-8").strip()
    
    # Rawtransaction'ið afkóðað
    dcrawtx = subprocess.run([smlycmd, "decoderawtransaction", rawtxid], 
            capture_output = True)
    dcrawtxid = json.loads(dcrawtx.stdout.decode("utf-8"))
    
    # Veskisfangið sem færslan sendist á
    addr1 = dcrawtxid["vout"][0]["scriptPubKey"]["addresses"][0]
    
    # Veskisfangið sem afgangurinn sendist á
    addr2 = dcrawtxid["vout"][1]["scriptPubKey"]["addresses"][0]
    
    # Tek aðeins þær færslur sem berast veskisfangi kauphallarinnar
    if DEX == addr1:  
        
        # HEX-ið sem inniheldur OP_RETURN-ið skilgreint
        HEX = dcrawtxid["vout"][2]["scriptPubKey"]["hex"][4:]
        
        # Tákn tilboðs/samþykktarfærslunnar skilgreint
        sendorreceive = HEX[0]
        
        # Tákn kauptilboðs/sölutilboðs skilgreint
        buyorsell = HEX[1]
        
        # Fyrsti stafur skammstöfun hinnar rafmyntarinnar
        firstabbr = HEX[2:4]
        
        # Ef um tilboðsfærslu er að ræða
        if sendorreceive == "0":
            
            # Ef um annað hvort kaup eða sölu á mynt er að ræða
            if buyorsell == "0" or "1":
                
                # Ætti skammstöfun hinnar rafmyntarinnar að vera: 
                if firstabbr == "00":
                    abbr = bytes.fromhex(HEX[4:10]).decode("utf-8")
                else:
                    abbr = bytes.fromhex(HEX[2:10]).decode("utf-8")
                
                # Vil aðeins taka tilboðum á ákveðnum bálkakeðjum
                mycryptoaddr = mycryptoaddress(abbr)
                if mycryptoaddr == "None":
                    logger.debug("Skipti við rafmynt sem ég tek ekki við: " + 
                        abbr + ". ")
                    return()
            
            # Satoshi
            satoshi = 10**-8
            
            # Upphæðirnar tvær á HEX sniði            
            amtcrypto1 = HEX[10:26]
            amtSMLY1 = HEX[26:42]
            
            # Upphæðunum breytt í strenglesgildi (e. string literal) á bætasniði
            amtcrypto2 = binascii.unhexlify(amtcrypto1)
            amtSMLY2 = binascii.unhexlify(amtSMLY1)
            
            # Uppröðun bætanna breytt út little endian og C týpunni breytt út 
            # unsigned long long
            amtcrypto3 = struct.unpack('<Q', amtcrypto2)[0]
            amtSMLY3 = struct.unpack('<Q', amtSMLY2)[0]
            
            # Margfalda að lokum með satoshi
            amtcrypto = amtcrypto3*satoshi
            amtSMLY = amtSMLY3*satoshi
            
            # Skoðað hvort skiptin séu undirvirði eða yfirvirði sem hlutf. SMLY/MYNT
            profitloss = profit_loss(abbr, amtcrypto, amtSMLY)
            
            # Tilboðið er óhagstætt fyrir mig...
               # ef um kauptilboð og yfirvirði SMLY/MYNT er að ræða. 
            if buyorsell == "0" and profitloss > 0:
                logger.debug("Óhagstætt tilboð upp á -" + str(abs(profitloss)) + 
                      "% SMLY/" + abbr + ". ")
                return
            
               # ef um sölutilboð og undirvirði SMLY/MYNT er að ræða. 
            elif buyorsell == "1" and profitloss < 0:
                logger.debug("Óhagstætt tilboð upp á -" + str(abs(profitloss)) + 
                      "% SMLY/" + abbr + ". ")
                return  
            elif buyorsell != "0" and buyorsell != "1":
                logger.debug("Hvorki sölu- né kauptilboð. ")
                return 
            
            # Veskisfang þess sem gerði tilboðið á hinni bálkakeðjunni 
            cryptoaddr0 = bytes.fromhex(HEX[42:]).decode("utf-8")
            
            # Sendi samþykktarfærslu
            acceptoffer(amtSMLY, abbr, txid, dcrawtxid)
            
        # Ef um samþykktarfærslu er að ræða...
        elif sendorreceive == "1":
            
            # er færsluauðkennið eftirfarandi
            acceptedofferTxid = bytes.fromhex(HEX[2:132]).decode("utf-8")
            
            # er veskisfang þess sem samþykkti færsluna á hinni bálkakeðjunni
            cryptoaddr1 = bytes.fromhex(HEX[132:]).decode("utf-8")
            logger.debug("Samþykktarfærsla: Færsluauðkenni samþykktarfærslunnar er " 
                  + acceptedofferTxid + " og veskisfang þess sem tók tilboðinu " 
                  + addrMYNT + " á hinni bálkakeðjunni. ")
            return()    
        else:
            logger.debug("Hvorki tilboðs- né samþykktarfærsla. ")
            return 
    return 

# =============================================================================
# Eftirfarandi fall býr til OP_RETURN fyrir samþykktarfærslu. 
# =============================================================================

def OP_RETURN(abbr, txid):
    
    # Færsluauðkenninu breytt yfir á HEX snið
    transid = ''.join([hex(ord(x))[2:] for x in txid])
    
    # Veskisfangið mitt á hinni bálkakeðjunni
    mycryptoa = mycryptoaddress(abbr)
    
    # Veskisfanginu breytt yfir á HEX snið
    mycryptoaddr = ''.join([hex(ord(x))[2:] for x in mycryptoa])
    
    # OP_RETURN-ið á HEX sniði
    opreturn = "02" + transid + mycryptoaddr
    
    return(opreturn)

# =============================================================================
# Eftirfarandi fall sendir samþykktarfærslu á kauphöllina
# =============================================================================

# Þegar þetta fall var prufað var ekki hægt að senda samþykktarfærslu á 
# Kauphöllina vegna þess að bætafjöldi OP_RETURNs samþykktarfærslunar fór 
# umfram hámarks bætafjölda OP_RETURNs sem senda mátti á broskallakeðjunni. 

# Hér væri sniðugt að skoða hvort það sé næg upphæð í veskinu mínu á 
# hinni bálkakeðjunni ef ég er að selja MYNT. 

def acceptoffer(amtSMLY, abbr, txid, dcrawtxid):
    
    # Heildarfjöldi broskalla í veskinu mínu 
    balance1 = subprocess.run([smlycmd, "getbalance"], capture_output=True)
    balance2 = json.loads(balance1.stdout.decode("utf-8"))
    
    # Breyti upphæðinni úr FLOAT í INT
    balance = math.floor(balance2)
    
    # Upphæð ónotaðra úttaka (utxo) frumstillt
    amtutxo = 0
    
    # Ef það er nóg inn á veskinu fyrir færsluna og námugjald...
    if balance >= amtSMLY+1:
        
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
            if amtutxo >= amtSMLY:
                break
            else:
                VIN += ","  
        VIN += "]"
            
        # Upphæðin sem send er á kauphöllina
        amttodex1 = dcrawtxid["vout"][0]["value"]
        amttodex = math.floor(amttodex1)
        
        # Upphæðin sem er send aftur til baka til mín
        amttome = balance-amttodex-1
        
        # HEX kóðinn með OP_RETURN-inu
        opreturn = OP_RETURN(abbr, txid)
        
        # VOUT skilgreint
        VOUT = f'{{"{DEX}":{amttodex},"{newaddress}":{amttome},"data":"{opreturn}:0"}}'
        
        # Rawtransaction búið til
        rawtx = subprocess.run([smlycmd, "createrawtransaction", VIN, VOUT], 
                capture_output = True)
        rawtxid = rawtx.stdout.decode("utf-8").strip()

        # Undirskrift fyrir rawtransaction 
        sgnrawtx = subprocess.run([smlycmd, "signrawtransaction", rawtxid], 
                capture_output = True)
        sgnrawtxid = json.loads(sgnrawtx.stdout.decode("utf-8"))
        print(sgnrawtxid)
        
        # Nýtt hex sem inniheldur einnig OP_RETURN-ið
        newhex = sgnrawtxid["hex"]
        
        # Rawtransaction sent
        #sendrawtx = subprocess.run([smlycmd, "sendrawtransaction", newhex], 
        #    capture_output = True)
        #print(sendrawtx)
        #sendrawtxid = sendrawtx.stdout.decode("utf-8").strip()
        
        #print(f"Færsla send á kauphöllina. Færsluauðkennið er: {sendrawtxid}")
    else:
        logger.debug("Ekki næg upphæð í veskinu til þess að taka tilboði. ")
        return()
    return()

# =============================================================================
# Eftirfarandi gagnarit (e. logger) er skilgreint svo hægt sé að finna þá 
# staði í forritinu þar sem ekki er sniðugt að taka tilboði og halda utan um
# kembunina (e. debug) í gagnaritsskrá (e. log file). 
# =============================================================================

# Gagnarit skilgreint
logger = logging.getLogger(__name__)

# Öll stig frá debug og hærri (info, warning, error og critical) leyfð
logger.setLevel(logging.DEBUG)

# Streymissýslarinn prentar skilaboðin í stjórnborðsgluggann (e. console window)
stream_handler = logging.StreamHandler()

# Skráarsýslarinn prentar skilaboðin í eftirfarandi gagnaritsskrá
file_handler = logging.FileHandler("bestdeal.log")

# Vel hvaða upplýsingar prentast út í gagnaritið
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Bæti að lokum sýslurunum við gagnaritið
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# =============================================================================
# Aðalfallið
# =============================================================================

def main():
    # Nokkur prufufærsluauðkenni sem ég bjó til. 
    txid = "bcb22e94a2f9730afe9be57bafd2e0cf0b9f8328a47098b7519486b10c2c2589"
    txid2 = "5dacca17d32c924d7afb7a469681b6136ea5d02db1b6c11bf3137e977769f845"
    txid3 = "eb93db73f3d8ee77eecc3e691474c1e189dbeddc5a117cbebd77a3eaa987a7de"
    txid4 = "57f6aeedac02bdf2053b0878915f70c631dd6184c7fb6dd980cd0b40187da775"
    txid5 = "1a760c0cb4b5bbeeeceeaf5f58f6869ddf1fd41c0139a15ead27323a0da2efb5"
    txid6 = "e7262c8f83b34230567a63c9d569f83de904d17ff9b3ff6b48d7ef8dab8cbe02"
    txid7 = "3e1a138869dde8171f88fd6a76a8844310b573b082942aec4fb70733a7823b85"
    txid8 = "9987926e9139dfac46bd116caab5b51e507d9ef6b069ef53363b76f306bdef15"
    txid9 = "2882cfa50340561864765a2d4430dc36c4a2272a3eaa8b11c7e7b6768438e59e"
    txid10 = "900e0fca2fe5071fdb9f28b3a614fc5f0213dd4fd255be5eb1b12b2f37829d92"
    txid11 = "e23ccdbada43cbc99b68b98a5aae5d9cd7957ccb44cc1c8873a3d7529d243b86"
    txid12 = "d87d82536c7bb324788c6b048a73883615075631fbe50817fa7fdb7cf559394f"

    # Fallið interpretopreturn að lokum keyrt á valið færsluauðkenni
    interpretopreturn(txid12)
    
    # Hér ætti ég að geta tengst WalletNotify
    #interpretopreturn(sys.argv[1])





if __name__ == "__main__":
    main()






