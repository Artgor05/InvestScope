from flask import Flask, render_template, request, session
import analytics
import plotly.graph_objects as go

info_1 = """
Ключевой статистический показатель:
    Волотильность

Чем ниже данный показатель, тем меньше резко изменяется цена,
следственно меньше вероятность сильного падения.

Оценка значений:
      < 0.15     -  Низкая
    0.15 - 0.25  -  Умеренная
    0.25 - 0.4   -  Высокая
      < 0.4      -  Очень высокая
"""
info_2 = """
Ключевой статистический показатель:
    Коэффициент Шарпа

Чем выше данный показатель, тем выше доходность на еденицу риска.

Оценка значений:
      > 3     -   Исключительный
    2  -  3   -   Очень хорошый
    1  -  2   -   Хорошый
    0  -  1   -   Слабый
      < 0     -   Плохой
"""
info_3 = """
Ключевой статистический показатель:
    Средняя доходность

Чем выше данный показатель, тем выше доходность данной акции.

Оценка значений:
      > 0.35     -  Очень высокая
    0.2  - 0.35  -  Хорошая
    0.1  - 0.2   -  Умеренная
    0    - 0.1   -  Низкая
      < 0        -  Убыточная
"""


def build_candle_graph(df, secid):

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["TRADEDATE"],
                open=df["OPEN"],
                high=df["HIGH"],
                low=df["LOW"],
                close=df["CLOSE"]
            )
        ]
    )

    fig.update_layout(
        title="Свечной график: " + secid,
        xaxis_title="Дата",
        yaxis_title="Цена",
        xaxis_rangeslider_visible=False
    )

    return fig.to_html(
        full_html=False
    )


app = Flask(__name__)
app.secret_key = "investscope_secret_key"

@app.route("/")
def start():

    return render_template("start.html")


@app.route("/recommendation", methods=["POST"])
def recommendation():

    stock_type = request.form["stock_type"]
    analysis_mode = request.form["analysis_mode"]

    if stock_type == "base_stock" and analysis_mode == "recommendation":
        return render_template("recommendation_select.html")
    else:
        print("Error")


@app.route("/result", methods=["POST"])
def result():
    graph = None

    if "investment_mode" in request.form:
        investment_mode = request.form["investment_mode"]
        session["investment_mode"] = investment_mode
    else:
        investment_mode = session.get("investment_mode")
        secid = request.form["selected_stock"]

        df_graph = analytics.get_stock_history(secid)
        graph = build_candle_graph(df_graph, secid)


    if investment_mode == "conservative":
        df = analytics.basicAnalysis(1, 20)
        selected_mode = "Консервативный"
        info = info_1
    elif investment_mode == "balanced":
        df = analytics.basicAnalysis(2, 20)
        selected_mode = "Сбалансированный"
        info = info_2
    else:
        df = analytics.basicAnalysis(3, 20)
        selected_mode = "Высокая доходность"
        info = info_3

    stocks = df.to_dict(orient="records")

    return render_template(
        "recommendation_result.html",
        selected_mode=selected_mode,
        stocks=stocks,
        graph=graph,
        info=info
    )


if __name__ == "__main__":
    app.run(debug=True)