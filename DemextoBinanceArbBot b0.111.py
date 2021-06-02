# DemextoBinanceArbBot b0.111
# Copyright © 2021 Coco for Switcheo / MaiTePora <3
# Licenced under GPL

# LIBRARYS
# ------------------------------------------------------------------------------
import time

# LIBRARYS DEM
# ------------------------------------------------------------------------------
import tradehub
from tradehub.wallet import Wallet
from tradehub.authenticated_client import AuthenticatedClient

from tradehub.types import CreateOrderMessage

# LIBRARYS BIN
# ------------------------------------------------------------------------------
from binance.client import Client

# PARAMETERS
# ------------------------------------------------------------------------------
myMnemonic = 'program cram lunch mail clump kebab paela switcheo make people rich now' #Tradehub mnemonic (example here: 12 word TradeHub mnemonic)

binanceApiKey = Client('SOoZ4v9c7tP5K6ezezaezkvvXtxR0FWIKVCkJuUyIfFmE', 'jnVFKJer4vKNDFKVHLezaezaezadJT0STsn6BmIyJHbIECG')

binTicker = "BUSDBUSDT"
demTicker = "busd1_usdc1"

baseRatio = 0.15 #Base Ratio (1.42 = 1.42%)
varRatio = 0.15 #Variance add (0.15 = 0.15%) goes down every 1H.
maxRaGreedIsNotGoodtio = 4.7 #Max Ratio (4.2 = 4.2%)

ratio = baseRatio #Def Ratio Var
tradeCounter = 1 #Counter of trades
timerLastTrade = 0 #Time last trade have been made
breaktimeTrades = 5 #Time pause after a run (10 = 10sec)
timeChangeRatio = 3 #Time since last trade to lower ratio (3600 = 1H)

# CONSTANTS
# ------------------------------------------------------------------------------
binPK = binanceApiKey
demPK = Wallet(myMnemonic, network="mainnet")
clientDem = AuthenticatedClient(demPK, network="mainnet",trusted_ips=None, trusted_uris=["http://54.255.5.46:5001", "http://175.41.151.35:5001"])

# Variables
# ------------------------------------------------------------------------------
global binBuyPrice
global binSellPrice
global demBuyPrice
global demSellPrice
global demQtySizeAsk
global demQtySizeBids

# FUNCTIONS
# ------------------------------------------------------------------------------
def GetBinDephs():
    global binBuyPrice
    global binSellPrice
    depthBin = binPK.get_order_book(symbol=binTicker)
    askBin = depthBin['asks'][0:1]
    bidsBin = depthBin['bids'][0:1]
    binBuyPrice = round(float((askBin[0])[0]),5)
    binSellPrice = round(float((bidsBin[0])[0]),5)

def GetDemDephs():
    global demBuyPrice
    global demSellPrice
    global demQtySizeAsk
    global demQtySizeBids
    depthDem = clientDem.get_orderbook(demTicker)
    askDemex = depthDem['asks'][0:1]
    bidsDemex = depthDem['bids'][0:1]
    askDem = list(askDemex[0].values())
    bidsDem = list(bidsDemex[0].values())
    demBuyPrice = askDem[0]
    demSellPrice = bidsDem[0]
    demQtySizeAsk = askDem[1]
    demQtySizeBids = bidsDem[1]

# MAIN
# ------------------------------------------------------------------------------
GetBinDephs()
print(f"Connected To Demex --- {demPK.address}")
GetDemDephs()
#print(f"Connected To Binance --- {binPK.get_account()['updateTime']}")
print ("Matching...")

while True :
    GetBinDephs()
    GetDemDephs()
    
    #---------------------SET ORDERS
    #If binSellPrice goes (+ratio) over demBuyPrice
    if float(binSellPrice) >= ((float(demBuyPrice))+(float(demBuyPrice)*(float(ratio))/100)):
        #BUY on demex
        message = CreateOrderMessage(demTicker, "buy", demQtySizeAsk, demBuyPrice)
        result = clientDem.create_order(message)
        print (tradeCounter,"- Buy", demQtySizeAsk, "---", demBuyPrice, "on Demex, ratio:", round(float(ratio),2))
        
        #Set reorders arb gains latency
        message = CreateOrderMessage(demTicker, "sell", (demQtySizeAsk), (demBuyPrice+(demBuyPrice*ratio/50))
        result = clientDem.create_order(message)

        #Sell on binance:
        order = client.order_market_sell(symbol=binTicker,quantity=demQtySizeAsk)
        print (tradeCounter,"- Sell:", demQtySizeAsk, "---:", binSellPrice, "on Binance, ratio:", round(float(ratio),2))
        tradeCounter = int(tradeCounter)+1
        #change ratio:
        if float(ratio)>=float(baseRatio) and float(ratio)<=float(maxRatio):
            ratio = float(ratio)+float(varRatio)
        #set last trade time
        timerLastTrade = time.time()

    #If demSellPrice goes (+ratio) over binBuyPrice
    if float(demSellPrice) >= ((float(binBuyPrice))+(float(binBuyPrice)*(float(ratio))/100)):
        #Sell on demex
        message = CreateOrderMessage(demTicker, "sell", demQtySizeBids, demSellPrice)
        result = clientDem.create_order(message)
        print (tradeCounter,"- Sell:",  demQtySizeBids, "---", demSellPrice, "on Demex, ratio:", round(float(ratio),2))
        
        #Set reorders arb gains latency
        message = CreateOrderMessage(demTicker, "buy", (demQtySizeBids), (demSellPrice-(demSellPrice*ratio/50))
        result = clientDem.create_order(message)
        
        #Buy on binance:
        #order = client.order_market_buy(symbol=binTicker,quantity=demQtySizeBids)
        print (tradeCounter, "- Buy", demQtySizeBids, "---", binBuyPrice, "on Binance, ratio:", round(float(ratio),2))
        tradeCounter = int(tradeCounter)+1
        #change ratio
        if float(ratio)>=float(baseRatio) and float(ratio)<=float(maxRatio):
            ratio = float(ratio)+float(varRatio)
        #set last trade time
        timerLastTrade = time.time()

    #Equilibration of spread
    if int(time.time())>(int(timerLastTrade)+int(timeChangeRatio)) and float(ratio)>(float(baseRatio)+float(varRatio)):
        ratio = float(ratio)-float(varRatio)
        timerLastTrade = time.time()

    #---------------------GET AND SET BALANCES
    balBinAssetA = binPK.get_asset_balance(asset='BTC')['free']
    balBinAssetB = binPK.get_asset_balance(asset='BUSD')['free']
    balDemAssetA = clientDem.get_balance(demPK.address)['btcb1']['available']
    balDemAssetB = clientDem.get_balance(demPK.address)['busd1']['available']

    ##Time pause after a run (10 = 10sec)
    time.sleep(breaktimeTrades)
