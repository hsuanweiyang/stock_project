from datetime import datetime
from dash.dependencies import Input, Output, State
import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
import json
import time

app = dash.Dash(__name__)

realtime_column_map = {'c': '股票代號', 'n': '公司名稱', 'z': '成交價', 'tv': '當盤成交量', 'v': '累積成交量',
                       'o': '開盤價', 'h': '最高', 'l': '最低', 'y': '昨收', 't': '時間'}

history_column_map = {'Date': '日期', 'Open': '開盤', 'High': '最高', 'Low': '最低', 'Close': '收盤', 'Volume': '成交量(股)'}

realtime_code_input = dbc.Card(
    [
        dbc.CardHeader(id='realtime_data_header', children=['即時報價']),
        dbc.Row(
            [
                dbc.Input(id='stock_code', type='text', placeholder='請輸入股票代號'),
                dbc.Button('Submit', id='send_button')
            ]
        )
    ], className='col-card'
)

realtime_data = dbc.Card(
    [
        dash_table.DataTable(
            id='realtime_data_table',
            columns=[{'name': realtime_column_map[col], 'id': col} for col in realtime_column_map.keys()]
        ),

    ]
)
realtime_card = dbc.Card(
    [realtime_code_input, realtime_data], className='col'
)

history_code_input = dbc.Card(
    [
        dbc.Row(
            [
                dbc.CardHeader(id='history_data_header', children=['歷史資料']),
                dbc.Input(id='history_code', type='text', placeholder='請輸入股票代號'),
                dcc.DatePickerRange(
                    id='history_date_range', min_date_allowed=datetime(1999, 1, 1), max_date_allowed=datetime.now(),
                    start_date_placeholder_text='開始日期', end_date_placeholder_text='結束日期',
                    initial_visible_month=datetime.now(), style={'height': '2%'}),
                dbc.Button('Submit', id='history_request_submit')
            ], className='col-card'
        )
    ]
)

history_data = dbc.Card(
    [
        dash_table.DataTable(
            id='history_data_table',
            columns=[{'name': history_column_map[col], 'id': col} for col in history_column_map.keys()],
            style_table={'height': '35vh', 'overflowY': 'scroll'},
            export_format='csv',
            export_headers='display'
        )
    ]
)

history_price_graph = dcc.Graph(
    id='historical_price_graph'
)
history_volume_graph = dcc.Graph(
    id='historical_volume_graph'
)


history_card = dbc.Card(
    [history_code_input, history_data, history_price_graph, history_volume_graph], className='col'
)

body = html.Div(
    [
        dbc.Row(
            [
                dbc.Col([realtime_card], style={'width': '50%'}),
                dbc.Col([history_card], style={'width': '50%'})
            ], style={'width': '100%', 'display': 'inline-flex'}
        )
    ]
)
app.layout = html.Div([body])


@app.callback(
    [Output('realtime_data_table', 'data'), Output('history_code', 'value')],
    [Input('send_button', 'n_clicks')],
    [State('stock_code', 'value')]
)
def get_realtime_data(n_clicks, stock_code_list):
    if n_clicks:
        output = []
        for stock_code in stock_code_list.split(','):
            api_url = 'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{0}.tw'.format(stock_code)
            api_request = requests.get(url=api_url)
            result = json.loads(api_request.text)
            result_df = pd.DataFrame(result['msgArray'], columns=list(realtime_column_map.keys()))
            output.extend(result_df.to_dict('records'))
        return output, stock_code_list.split(',')[0]


@app.callback(
    Output('history_data_table', 'data'),
    [Input('history_request_submit', 'n_clicks')],
    [State('history_code', 'value'), State('history_date_range', 'start_date'), State('history_date_range', 'end_date')]
)
def get_historical_data(n_clicks, stock_code, start_date, end_date):
    if n_clicks:
        def date2timestamp(date):
            datetime_obj = datetime.strptime(date, '%Y-%m-%d')
            timestamp = time.mktime(datetime_obj.timetuple())
            return int(timestamp)

        start = str(date2timestamp(start_date))
        end = str(date2timestamp(end_date))
        req = requests.post('https://query1.finance.yahoo.com/v7/finance/download/{0}.TW?period1={1}&period2={2}&'
                            'interval=1d&events=history&crumb=hP2rOschxO0'.format(stock_code, start, end))
        result = req.text
        with open('tmp_file.csv', 'w') as tmp_file:
            tmp_file.writelines(result)
        df = pd.read_csv('tmp_file.csv')
        df = df.replace('null', np.nan, regex=True)
        df_nonull = df.dropna()
        df_nonull[np.setdiff1d(df.columns, 'Date')] = df_nonull[np.setdiff1d(df.columns, 'Date')].astype(float)
        output = df_nonull[history_column_map]
    return output.to_dict('records')


@app.callback(
    [Output('historical_price_graph', 'figure'), Output('historical_volume_graph', 'figure')],
    [Input('history_data_table', 'data')],
    [State('history_code', 'value')]
)
def plot_history_graph(history_graph_data, stock_code):
    x_data = [n['Date'] for n in history_graph_data]
    y_price = [n['Close'] for n in history_graph_data]
    y_vol = [n['Volume'] for n in history_graph_data]
    price_figure = dict(
        data=[
            dict(
                x=x_data, y=y_price, name=stock_code
            ),
        ],
        layout=dict(
            title='Price of {}'.format(stock_code), showlegend=True
        )
    )
    volume_figure = dict(
        data=[
            dict(
                x=x_data, y=y_vol, name=stock_code, type='bar'
            ),
        ],
        layout=dict(
            title='Volume of {}'.format(stock_code), showlegend=True
        )
    )
    return price_figure, volume_figure


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=1234)