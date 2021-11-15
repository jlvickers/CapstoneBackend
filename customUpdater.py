import pandas as pd
import requests as req
import pymysql.cursors
import argparse
import yaml
import ta
import warnings
import inspect
import sqlInt as si
from ta.utils import dropna

#loads credentials from YAML doc in local folder
def loadYAML(creds):
    with open(creds, "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    credentials = {
        'host': data['databases']['SecurityDataDev']['host'],
        'user': data['databases']['SecurityDataDev']['user'],
        'password': data['databases']['SecurityDataDev']['password']}
    apiInfo = {
        'key': data['AVInfo']['api_key'],
        'intraday_url': data['AVInfo']['intraday_url']}
    return credentials, apiInfo

#resets table for dev purposes. DELETE IN FINAL PRODUCT
def resetTables():
    creds = loadYAML('creds.yml')[0]
    connection = pymysql.connect(creds['host'], creds['user'], creds['password'], 'SecurityDataDev')
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM secQueryInfo")
        cursor.execute("DELETE FROM secPriceInfo")
        cursor.execute("ALTER TABLE secQueryInfo AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE secPriceInfo AUTO_INCREMENT = 1")
    connection.commit()

#function to call api, load json into dataframe and transform dataframe to usable format
def queryToDF(symbol, interval: int):
    apiInfo = loadYAML("creds.yml")[1]
    r = req.get(apiInfo["intraday_url"] % (symbol, interval)).json()
    #checks JSON file from AV API to determine what portion the data is housed in
    if interval == 1:
        df = pd.DataFrame(r['Time Series (1min)'])
    elif interval == 5:
        df = pd.DataFrame(r['Time Series (5min)'])
    elif interval == 15:
        df = pd.DataFrame(r['Time Series (15min)'])
    elif interval == 30:
        df = pd.DataFrame(r['Time Series (30min)'])
    elif interval == 60:
        df = pd.DataFrame(r['Time Series (60min)'])
    #metadata for our secQueryInfo table
    metaData = r['Meta Data']['1. Information']
    #set columns and cleans up the DF before we transform it
    df.columns = [i.split(".")[-1].strip() for i in df.columns]
    df = dropna(df.T)
    df.reset_index(inplace=True)
    #cleans up column names and sets their datatype, then returns the dataframe
    df.rename(columns={'index': 'infoTime',
                '1. open':'open',
                '2. high':'high',
                '3. low':'low',
                '4. close':'close',
                '5. volume':'volume'}, inplace = True)
    #sets the datatypes for easy DB integration
    df['infoTime'] = df['infoTime'].astype(str)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(int)
    return df, metaData

#determines best timeframe based on user defined timeframe passed into it
def getBestTF(givenTF):
    valid = [1,5,15,30,60]
    working = []
    #mod of given value against pre-defined timeframes from AV, then returns the highest value so we're getting the most accurate/efficient info
    for x in valid:
        mod = givenTF % x
        if mod == 0:
            working.append(x)
    return max(working)

def paramFilter(attr, df) -> list:
    #creates list of parameters that the function passed into it takes
    paras = inspect.signature(attr).parameters
    h = []
    #checks for what dataframe columns we need and appends them to list & returns list
    for p in paras:
        if p == 'high':
            h.append(df['high'])
        if p == 'low':
            h.append(df['low'])
        if p == 'close':
            h.append(df['close'])
        if p == 'volume':
            h.append(df['volume'])
    return h

def addIndicators(indList: list, lib, df):
    trouble = {'psar_up'}
    allNames = ['VolumeWeightedAveragePrice', 'acc_dist_index', 'chaikin_money_flow', 'ease_of_movement', 'force_index', 'money_flow_index', 
            'negative_volume_index', 'np', 'on_balance_volume', 'pd', 'sma_ease_of_movement', 'volume_price_trend', 'volume_weighted_average_price',
            'AverageTrueRange', 'BollingerBands', 'DonchianChannel', 'KeltnerChannel', 'UlcerIndex', 'average_true_range', 'bollinger_hband', 
            'bollinger_hband_indicator', 'bollinger_lband', 'bollinger_lband_indicator', 'bollinger_mavg', 'bollinger_pband', 'bollinger_wband', 
            'donchian_channel_hband', 'donchian_channel_lband', 'donchian_channel_mband', 'donchian_channel_pband', 'donchian_channel_wband', 
            'keltner_channel_hband', 'keltner_channel_hband_indicator', 'keltner_channel_lband', 'keltner_channel_lband_indicator', 'keltner_channel_mband', 
            'keltner_channel_pband', 'keltner_channel_wband', 'np', 'pd', 'ulcer_index', 'MACD', 'MassIndex', 'adx', 'adx_neg', 'adx_pos', 'aroon_down', 
            'aroon_up', 'cci', 'dpo', 'ema_indicator', 'ichimoku_a', 'ichimoku_b', 'ichimoku_base_line', 'ichimoku_conversion_line', 'kst', 'kst_sig', 
            'macd', 'macd_diff', 'macd_signal', 'mass_index', 'np', 'pd', 'psar_down', 'psar_down_indicator', 'psar_up', 'psar_up_indicator', 'sma_indicator', 
            'stc', 'trix', 'vortex_indicator_neg', 'vortex_indicator_pos', 'wma_indicator', 'StochasticOscillator', 'UltimateOscillator', 'awesome_oscillator', 
            'np', 'pd', 'ppo', 'ppo_hist', 'ppo_signal', 'pvo', 'pvo_hist', 'pvo_signal', 'roc', 'rsi', 'stoch', 'stoch_signal', 'stochrsi', 'stochrsi_d', 
            'stochrsi_k', 'tsi', 'ultimate_oscillator', 'williams_r', 'kama']
    h = {}
    for x in indList:
        if type(x) == list:
            if x[0] in allNames:
                name = x[0]
                #sets attr to the function we need based on the params sent in (looks for name provided in library)
                attr = getattr(lib, name)
                #removing name from list and setting values to ints to pass into TA function
                x.remove(x[0])
                x = list(map(int, x))
                #creates list of required df series objects
                params = paramFilter(attr, df)
                #astrix used to unpack list into individ args
                if name in trouble:
                    df[name] = attr(*params, *x, fillna=True)
                else:
                    df[name] = attr(*params, *x)
                h[name + str(x[0])] = round(df.iloc[-1][name], 4)
        else:
            if x in allNames:
                attr = getattr(lib, x)
                params = paramFilter(attr, df)
                if x in trouble:
                    df[x] = attr(*params, fillna=True)
                else:
                    df[x] = attr(*params)
                h[name] = str(round(df.iloc[-1][x], 4))
    return h

def parseAndAdd(args, df):
    h = {}
    df = dropna(df)
    if args.vol != None:
        volInds = [x.split(';') if ';' in x else x for x in args.vol.split(',')]
        h = h | addIndicators(volInds, ta.volume, df)
    if args.volatil != None:
        volatilInds = [x.split(';') if ';' in x else x for x in args.volatil.split(',')]
        h = h | addIndicators(volatilInds, ta.volatility, df)
    if args.trend != None:
        trendInds = [x.split(';') if ';' in x else x for x in args.trend.split(',')]
        h = h | addIndicators(trendInds, ta.trend, df)
    if args.momo != None:
        momoInds = [x.split(';') if ';' in x else x for x in args.momo.split(',')]
        h = h | addIndicators(momoInds, ta.momentum, df)
    return h

#main function, written this way to indicate it's to be run as a CLI script
if __name__ == '__main__':
    agg_dict = {'open': 'first',
          'high': 'max',
          'low': 'min',
          'close': 'last',
          'volume': 'sum'}
    dbAgg_dict = {'open': 'first',
          'high': 'max',
          'low': 'min',
          'close': 'last',
          'vol': 'sum'}
    warnings.filterwarnings('ignore')
    parser = argparse.ArgumentParser()
    parser.add_argument("-local", "--local", action="store_true", default=True)
    parser.add_argument("-n", "--n")
    parser.add_argument("-tf", "--tf")
    parser.add_argument("-vol", "--vol")
    parser.add_argument("-volatil", "--volatil")
    parser.add_argument("-trend", "--trend")
    parser.add_argument("-momo", "--momo")
    args = parser.parse_args()
    dbWorker = si.sqlInt(args.n.upper(), 'creds.yml', 'SecurityDataDev')
    try:
        #getting data from DB, if not, querying API
        best = getBestTF(int(args.tf))
        d = dbWorker.checkDB(str(best))
        APIdata = False
        if d is None:
            d, queryMD = queryToDF(args.n.upper(), best)
            APIdata = True
        #dataframe index manipulation to prep for resampling
        d.set_index('infoTime', inplace=True)
        d.index = pd.to_datetime(d.index)
        d.index.strftime('%Y-%m-%d %H:%M:%S')
        if APIdata:
            dAgg = d.resample("{}min".format(args.tf)).agg(agg_dict)
        else:
            dAgg = d.resample("{}min".format(args.tf)).agg(dbAgg_dict)
            dAgg.rename(columns={'vol':'volume'}, inplace = True)

        #dictionary result for json formatting
        dictOut = {'ticker': args.n.upper(),
                    'Most Recent Data': str(dAgg.tail(1).index[0]), 
                    'Closing Price': dAgg.tail(1).close[0],
                    'indicators': parseAndAdd(args, dAgg)}
        print(dictOut)
        
        #if new data, add to DB
        if APIdata:
            try:
                dbWorker.addQueryInfo(queryMD)
                dbWorker.addPriceInfo(d)
            except Exception as e:
                print("Database Addition Error: "+type(e), e)
                quit()

    #general error handling
    except Exception as e:
        print("Error in Query",+type(e),e)
        quit()
    