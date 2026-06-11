import requests
import pandas as pd
import sqlite3
from datetime import date


#Базовые математичнские подсчёты
def volatility(df):
    if len(df) > 1:
        returns = df["CLOSE"].pct_change(fill_method=None).dropna()

        if len(returns) == 0:
            return None

        vol = returns.std() * (len(df) ** 0.5)
        if pd.isna(vol):
            return None
        return vol
    return None

def averageYield(df):
    if len(df) > 1:
        returns = df["CLOSE"].pct_change(fill_method=None).dropna()

        if len(returns) == 0:
            return None

        ave = returns.mean() * len(df)
        if pd.isna(ave):
            return None
        return ave
    return None

def sharpeRatio(df, risk_free_rate):
    ave = averageYield(df)
    vol = volatility(df)
    return None if (ave is None) or (vol is None) else (ave - risk_free_rate) / vol



#Функции подчсёта экономических велечин
def getVolatility(secid, date_from, date_till):
    connection = sqlite3.connect('project_database.db')
    df_history = pd.read_sql(
        "SELECT CLOSE FROM history WHERE SECID = '" + secid + "' AND TRADEDATE BETWEEN '" + date_from + "' AND '" + date_till + "'",
        connection
    )
    connection.close()
    vol = volatility(df_history)

    return None if vol is None else float(vol)

def getSharpeRatio(secid, date_from, date_till):
    connection = sqlite3.connect('project_database.db')
    df_history = pd.read_sql(
        "SELECT CLOSE FROM history WHERE SECID = '" + secid + "' AND TRADEDATE BETWEEN '" + date_from + "' AND '" + date_till + "'",
        connection
    )
    connection.close()
    shar = sharpeRatio(df_history, 0.11) # гособлигации РФ - 11%

    return None if shar is None else float(shar)

def getAverageYield(secid, date_from, date_till):
    connection = sqlite3.connect('project_database.db')
    df_history = pd.read_sql(
        "SELECT CLOSE FROM history WHERE SECID = '" + secid + "' AND TRADEDATE BETWEEN '" + date_from + "' AND '" + date_till + "'",
        connection
    )

    connection.close()
    ave = averageYield(df_history)

    return None if ave is None else float(ave)



#Заполнение баз данных
def updateVolatilityInAnalyrics(date_from, date_till):
    connection = sqlite3.connect('project_database.db')
    df_companies = pd.read_sql(
        "SELECT SECID FROM companies",
        connection
    )
    cursor = connection.cursor()

    for i in range(len(df_companies)):
        secid = df_companies.loc[i, "SECID"]
        cursor.execute('''UPDATE analytics SET volatility = ?, volatilityCalculationDate = ? WHERE SECID = ?''',
                       (getVolatility(secid, date_from, date_till), date.today().strftime("%Y-%m-%d"), str(secid)))
    connection.commit()
    connection.close()

def updateSharpeRatioInAnalyrics(date_from, date_till):
    connection = sqlite3.connect('project_database.db')
    df_companies = pd.read_sql(
        "SELECT SECID FROM companies",
        connection
    )
    cursor = connection.cursor()

    for i in range(len(df_companies)):
        secid = df_companies.loc[i, "SECID"]
        cursor.execute('''UPDATE analytics SET sharpeRatio = ?, sharpeRatioCalculationDate = ? WHERE SECID = ?''',
                       (getSharpeRatio(secid, date_from, date_till), date.today().strftime("%Y-%m-%d"), str(secid)))
    connection.commit()
    connection.close()

def updateAverageYieldInAnalyrics(date_from, date_till):
    connection = sqlite3.connect('project_database.db')
    df_companies = pd.read_sql(
        "SELECT SECID FROM companies",
        connection
    )
    cursor = connection.cursor()

    for i in range(len(df_companies)):
        secid = df_companies.loc[i, "SECID"]
        cursor.execute('''UPDATE analytics SET averageYield = ?, averageYieldCalculationDate = ? WHERE SECID = ?''',
                       (getAverageYield(secid, date_from, date_till), date.today().strftime("%Y-%m-%d"), str(secid)))
    connection.commit()
    connection.close()

def getListOfCompanies():
    start = 0
    while True:
        url = "https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities.json"
        params = {
            "start": start
        }
        response = requests.get(url, params=params)
        data = response.json()

        history = data["history"]
        df = pd.DataFrame(
            history["data"],
            columns=history["columns"]
        )
        df = df.drop(columns=["BOARDID", "NUMTRADES", "VALUE", "OPEN", "LOW", "HIGH", "LEGALCLOSEPRICE",
                              "WAPRICE", "CLOSE", "VOLUME", "MARKETPRICE2", "MARKETPRICE3", "ADMITTEDQUOTE",
                              "MP2VALTRD", "MARKETPRICE3TRADESVALUE", "ADMITTEDVALUE", "WAVAL", "TRADINGSESSION",
                              "CURRENCYID", "TRENDCLSPR", "TRADE_SESSION_DATE"])

        connection = sqlite3.connect('project_database.db')
        df.to_sql(
            "companies",
            connection,
            if_exists="append",
            index=False
        )
        connection.close()

        index, total, pagesize = map(int, data["history.cursor"]["data"][0])
        if (index + pagesize) > total:
            break
        start += 100

def appendListOfStocks(date_from, date_till):
    connection = sqlite3.connect('project_database.db')
    df_companies = pd.read_sql(
        "SELECT * FROM companies",
        connection
    )
    connection.close()

    #len(df_companies)
    for i in range(len(df_companies)):
        sec = df_companies.loc[i, "SECID"]
        print(str(i + 1) + "/261 - " + str(sec))
        start = 0
        while True:
            url = "https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/" + sec + ".json"
            params = {
                "start": start,
                "from": date_from,
                "till": date_till
            }
            response = requests.get(url, params=params)
            data = response.json()

            history = data["history"]
            df_history = pd.DataFrame(
                history["data"],
                columns=history["columns"]
            )
            df_history = df_history.drop(
                columns=["BOARDID", "LEGALCLOSEPRICE", "MARKETPRICE2", "MARKETPRICE3", "ADMITTEDQUOTE", "MP2VALTRD",
                         "MARKETPRICE3TRADESVALUE", "ADMITTEDVALUE", "WAVAL", "TRADINGSESSION", "CURRENCYID",
                         "TRENDCLSPR", "TRADE_SESSION_DATE"])

            connection = sqlite3.connect('project_database.db')
            df_history.to_sql(
                "history",
                connection,
                if_exists="append",
                index=False
            )
            connection.close()

            index, total, pagesize = map(int, data["history.cursor"]["data"][0])
            if (index + pagesize) > total:
                break
            start += 100



#Аналитика
def basicAnalysis(sortMode, n):
    connection = sqlite3.connect('project_database.db')
    df_analytics = pd.read_sql(
        "SELECT * FROM analytics",
        connection
    )
    connection.close()

    if sortMode == 1:
        df_volatility = (df_analytics
                        .drop(columns=["sharpeRatio", "sharpeRatioCalculationDate","averageYield", "averageYieldCalculationDate", "volatilityCalculationDate"])
                        .sort_values(by="volatility")
                        .head(n))
        df_volatility.rename(columns={'volatility': 'value'}, inplace=True)
        mas = []
        for i in range(n):
            mas += [volatilityAssessment(float(df_volatility.iloc[[i], 1]))]
        df_volatility.insert(2, "rating", mas)
        return df_volatility

    elif sortMode == 2:
        df_sharpe = (df_analytics
                     .drop(columns=["volatility", "volatilityCalculationDate", "averageYield", "averageYieldCalculationDate", "sharpeRatioCalculationDate"])
                     .sort_values(by="sharpeRatio", ascending=False)
                     .head(n))
        df_sharpe.rename(columns={'sharpeRatio': 'value'}, inplace=True)
        mas = []
        for i in range(n):
            mas += [sharpeRatioAssessment(float(df_sharpe.iloc[[i], 1]))]
        df_sharpe.insert(2, "rating", mas)
        return df_sharpe
    else:
        df_average = (df_analytics
                      .drop(columns=["volatility", "volatilityCalculationDate", "sharpeRatio", "sharpeRatioCalculationDate", "averageYieldCalculationDate"])
                      .sort_values(by="averageYield", ascending=False)
                      .head(n))
        df_average.rename(columns={'averageYield': 'value'}, inplace=True)
        mas = []
        for i in range(n):
            mas += [averageYieldAssessment(float(df_average.iloc[[i], 1]))]
        df_average.insert(2, "rating", mas)
        return df_average

def volatilityAssessment(vol):
    if vol <= 0.15:
        return "Низкая"
    elif vol > 0.15 and vol <= 0.25:
        return "Умеренная"
    elif vol > 0.25 and vol <= 0.40:
        return "Высокая"
    else:
        return "Очень высокая"

def sharpeRatioAssessment(shar):
    if shar <= 0.0:
        return "Плохо"
    elif shar > 0.0 and shar <= 1.0:
        return "Слабый"
    elif shar > 1.0 and shar <= 2.0:
        return "Хороший"
    elif shar > 2.0 and shar <= 3.0:
        return "Очень хороший"
    else:
        return "Исключительный"

def averageYieldAssessment(ave):
    if ave <= 0.0:
        return "Убыточная"
    elif ave > 0.0 and ave <= 0.10:
        return "Низкая"
    elif ave > 0.10 and ave <= 0.20:
        return "Умеренная"
    elif ave > 0.20 and ave <= 0.35:
        return "Хорошая"
    else:
        return "Очень высокая"

def get_stock_history(secid):
    connection = sqlite3.connect('project_database.db')
    df_st_his = pd.read_sql(
        'SELECT TRADEDATE, OPEN, HIGH, LOW, CLOSE, VOLUME FROM history '
        'WHERE SECID = "' + secid + '" ORDER BY TRADEDATE DESC LIMIT 252',
        connection
    )
    connection.close()
    return df_st_his



#База данный SQLite
def createDataBase(commad):
    connection = sqlite3.connect('project_database.db')
    cursor = connection.cursor()

    cursor.execute(commad)

    connection.commit()
    connection.close()

def dropTable(table):
    connection = sqlite3.connect('project_database.db')
    cursor = connection.cursor()

    cursor.execute('''DROP TABLE ''' + table)

    connection.commit()
    connection.close()

def selectTable(table):
    connection = sqlite3.connect('project_database.db')
    df = pd.read_sql(
        "SELECT * FROM " + table,
        connection
    )
    print(df)

    connection.close()

def insertAnalytics():
    connection = sqlite3.connect('project_database.db')
    df_companies = pd.read_sql(
        "SELECT SECID FROM companies",
        connection
    )
    cursor = connection.cursor()

    for i in range(len(df_companies)):
        secid = df_companies.loc[i, "SECID"]
        cursor.execute('''INSERT INTO analytics(SECID) VALUES (?)''', (secid,))
    connection.commit()
    connection.close()



#Блок управления
def remakeCompanies():
    dropTable("companies")
    print("Таблица companies - удалена.")
    createDataBase('''CREATE TABLE companies (id INTEGER PRIMARY KEY, SECID TEXT, SHORTNAME TEXT, TRADEDATE DATE)''')
    print("Таблица companies - создана.")
    getListOfCompanies()
    print("Таблица companies - заполнена.")

def remakeHistory(date_from, date_till):
    dropTable("history")
    print("Таблица history - удалена.")
    createDataBase(
        '''CREATE TABLE history (
            id INTEGER PRIMARY KEY, 
            SECID TEXT, 
            SHORTNAME TEXT, 
            TRADEDATE DATE,
            OPEN REAL,
            LOW REAL,
            HIGH REAL,
            CLOSE REAL,
            VOLUME REAL,
            VALUE REAL,
            NUMTRADES REAL,
            WAPRICE REAL
        )'''
    )
    print("Таблица history - создана.")
    print("Заполнение таблица history:")
    appendListOfStocks(date_from, date_till)
    print("Таблица history - заполнена.")

def remakeAnalytics(date_from, date_till):
    dropTable("analytics")
    print("Таблица analytics - удалена.")
    createDataBase('''CREATE TABLE analytics (SECID TEXT,
                                            volatility REAL, volatilityCalculationDate DATE,
                                            sharpeRatio REAl, sharpeRatioCalculationDate DATE,
                                            averageYield REAL, averageYieldCalculationDate DATE)''')
    print("Таблица analytics - создана.")
    insertAnalytics()
    print("Таблица analytics - подготовлена к аналитике.")

    updateVolatilityInAnalyrics(date_from, date_till)
    print("_Волотильность_ в таблице analytics - расчитана.")
    updateSharpeRatioInAnalyrics(date_from, date_till)
    print("_Коэффициент Шарпа_ в таблице analytics - расчитан.")
    updateAverageYieldInAnalyrics(date_from, date_till)
    print("_Средняя доходность_ в таблице analytics - расчитана.")



#Ручное управление
#remakeCompanies()
#remakeHistory("2025-06-01", "2026-01-01")
#remakeAnalytics("2025-06-01", "2026-06-09")

#appendListOfStocks("2026-01-01", "2026-06-09")

#selectTable("companies")
#selectTable("history")
#selectTable("analytics")


#print(basicAnalysis(1, 10))
#basicAnalysis(1, 10)
#basicAnalysis(3, 25)



