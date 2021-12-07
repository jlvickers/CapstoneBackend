import pandas as pd
import pymysql.cursors
import datetime as dt
import yaml

#object to handle all interactions with DB. Pass in yaml file with ticker symbol, credentials, and db name on initialization
class sqlInt:
    def __init__(self, symbol, creds, dbName) -> None:
        self.symbol = symbol
        self.creds = creds
        self.dbName = dbName
        with open(self.creds, "r") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        self.login = {
            'host': data['databases'][self.dbName]['host'],
            'user': data['databases'][self.dbName]['user'],
            'password': data['databases'][self.dbName]['password']}
        self.apiInfo = {
            'key': data['AVInfo']['api_key'],
            'intraday_url': data['AVInfo']['intraday_url']}
        self.connection = pymysql.connect(host=self.login['host'], user=self.login['user'], password=self.login['password'], db=self.dbName)

    #adds query info used for logging API requests and preventing unnecessary API calls
    def addQueryInfo(self, queryInfo: str) -> None:
        rightNow = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sqlQueryInfo = "INSERT INTO `secQueryInfo` (`symbol`, `queryInfo`, `lastQueried`) VALUES (%s, %s, %s)"
        with self.connection.cursor() as cursor:
            cursor.execute(sqlQueryInfo, (self.symbol, queryInfo, rightNow))
        self.connection.commit()
    
    #sets query ID to to use in other functions.
    def setQueryID(self) -> None:
        sqlQueryID = "SELECT queryID FROM secQueryInfo WHERE symbol = %s ORDER BY queryID DESC LIMIT 1"
        with self.connection.cursor() as cursor:
            cursor.execute(sqlQueryID, self.symbol)
            self.queryID = cursor.fetchone()

    #adds price info from dataframe to database.
    def addPriceInfo(self, df) -> None:
        self.setQueryID()
        sqlPriceInfo = "INSERT INTO secPriceInfo (queryID, infoTime, open, high, low, close, vol) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        with self.connection.cursor() as cursor:
            for i, row in df.iterrows():
                cursor.execute(sqlPriceInfo, (self.queryID, str(i), row.open, row.high, row.low, row.close, row.volume))
        self.connection.commit()
        
    #checks DB for useful info IE not outdated, loads into DF if there is, otherwise returns None
    def checkDB(self, tf) -> pd.Dataframe:
        timeframe = "({0}min)".format(tf)
        query = "SELECT * FROM secQueryInfo WHERE symbol = '{0}' AND queryInfo LIKE '%{1}%' ORDER BY queryID DESC LIMIT 1".format(self.symbol, timeframe)
        with self.connection.cursor() as cursor:
            cursor.execute(query)
        row = cursor.fetchone()
        if row is not None and row[3].date() == dt.date.today():
            priceQuery = "SELECT * FROM secPriceInfo WHERE queryID = '{0}'".format(row[0])
            df = pd.read_sql(priceQuery, self.connection)
            return df