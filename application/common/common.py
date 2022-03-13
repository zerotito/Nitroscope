from libraries import *

log_types = ["STARTED", "FINISHED", "ERROR"]
CUR_DIRECTORY = os.path.dirname(__file__)
ABS_PATH = os.path.abspath(os.path.join(CUR_DIRECTORY, os.pardir))
KPI_FOLDER = f"{ABS_PATH}/db"
ad_config = {
    "levels": {
        "minor": "1",
        "medium": "1.3",
        "major": "1.6",
        "critical": "2"
    }
}
DATE_COLUMN = "datetime"
OBJECT_COLUMN = "node"

def using_grouper(df, typ="sum"):
    level_values = df.index.get_level_values
    len_level = len(df.index.names) - 1
    if typ == 'mean':
        return (
            df.groupby([level_values(i) for i in list(range(len_level))] + [pd.Grouper(freq='1H', level=-1)]).mean())
    else:
        return (df.groupby([level_values(i) for i in list(range(len_level))] + [pd.Grouper(freq='1H', level=-1)]).sum())


def prepare_kpi_series_lv1(kpi_list, df_main, object_column, ad_config, size=5000):
    df_series = []
    for kpi in kpi_list:
        df_kpi = df_main[[object_column, kpi]]
        node_list = sorted(list(df_kpi[object_column].unique()))
        for node in node_list:
            df = df_kpi[df_kpi[object_column] == node].reset_index().set_index([object_column, 'datetime'])
            df = using_grouper(df, typ="mean").reset_index()  # Normalizing 1 hour
            if df[kpi].max() != df[kpi].min() and df[kpi].max() > size:
                df.drop([object_column], axis=1, errors='ignore', inplace=True)
                df_series.append({
                    "config": ad_config,
                    "data": df,
                    "kpi": kpi,
                    "node": node
                })
    return df_series


def run_in_parallel(function_name, series, cpu_process_count=6, desc=""):
    """

    :param function_name: function which is goint to be run in paralel
    :param series: series input for function
    :param cpu_process_count:
    :param desc:
    :return:
    """
    p = Pool(cpu_process_count)
    predictions = list(tqdm(p.imap(function_name, series), total=len(series), desc=desc))
    p.close()
    p.join()
    return predictions


def calculate_trend_change(params):
    ts1 = params["data"][params["data"].columns[1]].to_numpy()
    algo1 = rpt.Pelt(model="rbf").fit(ts1)
    change_location1 = algo1.predict(pen=10)
    if len(ts1) in change_location1: change_location1.remove(len(ts1))
    change_location = [params["data"][params["data"].index == x - 1].datetime.values[0] for x in change_location1]
    change_location_ng = [pd.to_datetime(str(x)).strftime('%Y-%m-%d %H:%M:%S') for x in change_location]
    if len(change_location_ng) > 0:
        fTrend = True
    else:
        fTrend = False
    response = {
        "node": params["node"],
        "flag": fTrend,
        "kpi": params["kpi"],
        "changes": change_location_ng
    }
    return response


def calculate_anomaly_fe(params):
    """
    :param params: {
        "config": {}, # anomaly config parameters
        "data": df # Dataframe which has two columns first column should be datetime and second column numerical
        "kpi": {}, # anomaly config parameters
        "cluster": {}, # cluster name
        "node": {}, # node name
        "service": {}, # service (optional)
        "sub_service": {}, # sub service (optional)
    }
    :return:
    """
    ad_config = params["config"]
    df = params["data"]
    kpi = params["kpi"]
    node = params["node"]
    df.columns = ["ds", "y"]
    m = Prophet(n_changepoints=2, changepoint_prior_scale=0.5, changepoint_range=0.9, interval_width=0.95)
    m.fit(df)
    future = m.make_future_dataframe(periods=0)
    forecast = m.predict(future)
    result = pd.concat([df.set_index('ds')['y'], forecast.set_index('ds')[['yhat', 'yhat_lower', 'yhat_upper']]],
                       axis=1)
    result['error'] = result['y'] - result['yhat']
    result['uncertainty'] = result['yhat_upper'] - result['yhat_lower']
    result['anomaly'] = result.apply(lambda x:
                                     'Critical' if (np.abs(x['error']) > float(ad_config["levels"]["critical"]) * x[
                                         'uncertainty']) else (
                                         'Major' if (np.abs(x['error']) > float(ad_config["levels"]["major"]) * x[
                                             'uncertainty']) else (
                                             'Medium' if (
                                                     np.abs(x['error']) > float(ad_config["levels"]["medium"]) *
                                                     x[
                                                         'uncertainty']) else (
                                                 'Minor' if (np.abs(x['error']) > float(
                                                     ad_config["levels"]["minor"]) *
                                                             x['uncertainty']) else 'None'))), axis=1)
    flagAnomaly = False
    mail_anomaly_list = ["Critical", "Major", "Medium", "Minor"]
    for i in range(20):
        if result[result.index == result.index[i - 1]].anomaly.values[0] in mail_anomaly_list:
            flagAnomaly = True
            break
    result = result[['y', 'yhat', 'yhat_lower', 'yhat_upper', 'anomaly']]
    response = {
        "flag": flagAnomaly,
        "kpi": kpi,
        "node": node,
        "data": result
    }
    return response


def prepare_plot_from_list_fe(s):
    df = s["data"]
    T_PLOT_FOLDER = s["folder"]
    pc = s["pc"]
    changepoints = s["changepoints"]
    title = f'<b>Node:</b> {s["node"]}<br><b>KPI Id:</b> {s["kpi id"]}<br><b>KPI:</b> {s["kpi"]}'
    pc.layout["title"]["text"] = title
    df["anomaly_value"] = df.apply(lambda x: x.y if x.anomaly != "None" else None, axis=1)
    if df.iloc[-1].anomaly != "None":
        pc.annotation_config["x"] = df.iloc[-1].name.strftime('%Y-%m-%d %H:%M:%S')
        pc.annotation_config["y"] = df.iloc[-1].anomaly_value
        pc.annotation_config["text"] = f"{df.iloc[-1].name.strftime('%Y-%m-%d %H:%M:%S')}<br>{df.iloc[-1].anomaly}<br>{df.iloc[-1].anomaly_value}"
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["yhat_lower"], line=pc.lbond_config, name='Lower Bond'))
    fig.add_trace( go.Scatter(x=df.index, y=df["yhat_upper"], line=pc.ubond_config, fill='tonexty', fillcolor=pc.ubond_fill,
                   name='Upper Bond'))
    fig.add_trace(go.Scatter(x=df.index, y=df["y"], mode='lines', marker_color=pc.color_actual, name='Actual'))
    fig.add_trace(go.Scatter(x=df.index, y=df["yhat"], mode='lines', marker_color=pc.color_trend, name='Prediction'))
    fig.add_trace(
        go.Scatter(x=df.index, y=df["anomaly_value"], mode='markers', marker=pc.anomaly_config, name='Anomaly'))
    fig.update_layout(pc.layout)
    fig.update_layout(legend=dict(
        yanchor="top",
        xanchor="left",
        x=1.01, y=1,
        traceorder="reversed",
        title_font_family="Times New Roman",
        font=dict(
            family="Times New Roman",
            color="rgba(123, 176, 244, 1)"
        ),
        bgcolor="rgba(0, 0, 0, 0)",
        bordercolor="Black",
        borderwidth=0
    ))
    #fig.update_layout(width=800, height=400)
    fig.update_layout(autosize=True)
    fig.update_xaxes(pc.xaxes_config)
    fig.update_yaxes(pc.yaxes_config)
    for e in changepoints:
        fig.add_vline(x=e, line_width=3, line_dash="dash", line_color="purple")
    fig.write_json(f'{T_PLOT_FOLDER}/{s["kpi id"]}.json')


def resample_dataframe(df, typ, freq, len_level=2):
    """
    :param df:  Dataframe
    :param typ: sum or mean
    :param freq: 30min....
    :param len_level:
    :return:
    """
    level_values = df.index.get_level_values
    if typ == 'mean':
        return (
            df.groupby([level_values(i) for i in list(range(len_level))] + [pd.Grouper(freq=freq, level=-1)]).mean())
    else:
        return (df.groupby([level_values(i) for i in list(range(len_level))] + [pd.Grouper(freq=freq, level=-1)]).sum())


def write_to_excel(export_file_name, df_excel):
    import xlwt
    from xlwt import Workbook
    writer = pd.ExcelWriter(export_file_name, engine='xlsxwriter')
    df_excel.to_excel(writer, sheet_name='ANOMALIES', startrow=1, header=False, index=False)
    workbook = writer.book
    worksheet = writer.sheets['ANOMALIES']
    # Add a header format.
    header_format = workbook.add_format({
        'bold': True,
        'align': 'left',
        'font_color': '#FFFFFF',
        'fg_color': '#1F497D',
        'text_wrap': True,
        'border': 1})
    wrap_format = workbook.add_format({'text_wrap': True})
    for col_num, value in enumerate(df_excel.columns.values):
        worksheet.write(0, col_num, value, header_format)
        column_len = df_excel[value].astype(str).str.len().max()
        # Setting the length if the column header is larger
        # than the max column value length
        column_len = max(column_len, len(value)) + 3
        # set the column length
        worksheet.set_column(col_num, col_num, column_len)
    writer.save()


def alarm_anomalies(node, alarm_file, export_file):
    df_alarm = pd.read_parquet(alarm_file, engine="pyarrow", filters=[(OBJECT_COLUMN, '==', node)])
    df_alarm["count"] = 1
    df_alarm = df_alarm.reset_index()
    df_alarm[DATE_COLUMN] = pd.to_datetime(df_alarm['alarmtime']).dt.floor('h')
    df_alarm = df_alarm[[DATE_COLUMN, "count"]].groupby([DATE_COLUMN]).sum().reset_index().dropna()
    df_alarm.set_index(DATE_COLUMN, inplace=True)
    df_orig = pd.date_range(df_alarm.index.min(), df_alarm.index.max(), freq="1h", normalize=True)
    df_orig = pd.DataFrame(df_orig)
    df_orig.columns = [DATE_COLUMN]
    df_orig = df_orig.set_index(DATE_COLUMN)
    df_alarm = df_orig.join(df_alarm).fillna(0)
    df_alarm["count"] = df_alarm["count"].astype("int")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_alarm.index, y=df_alarm["count"],
                             line=dict(color='rgba(255, 0, 0, 1)'),
                             fill='tonexty',
                             fillcolor='rgba(255, 0, 0, 0.7)',
                             showlegend=False))
    fig.update_xaxes(matches=None)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, zeroline=False)
    fig.update_xaxes(showgrid=False, gridwidth=1, gridcolor='gray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='gray')
    fig.update_layout(
        {
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
            "font_color": "rgba(123, 176, 244, 1)",
        }, showlegend=False)
    #fig.update_layout(width=800, height=350, margin={'t': 0})
    fig.update_layout(autosize=True, margin={'t': 0, 'b': 0})
    fig.update_yaxes(ticksuffix="  ")
    fig.write_json(export_file)

class plot_configuration():
    lbond_config = dict(color='rgba(255, 178, 102, 0.9)', width=2)
    ubond_config = dict(color='rgba(255, 178, 102, 0.9)', width=2)
    ubond_fill = 'rgba(255, 178, 102, 0.3)'
    color_actual = 'rgba(0, 0, 255, 1)'
    color_trend = 'rgba(0, 255, 0, 1)'
    anomaly_config = dict(color='rgba(255, 0, 0, 0.7)', size=10, line=dict(color='rgba(255, 0, 0, 1)', width=2))
    layout = dict(
        font=dict(
            size=10,
        ),
        title={
            'text': "",  # must be changed with data
            # 'y': 0.9,
            # 'x': 0.5,
            'xanchor': 'left',
            'yanchor': 'top'
        },
        plot_bgcolor='rgb(255,255,255,1)',
        paper_bgcolor='rgb(255,255,255, 0)',
        legend=dict(
            yanchor="top",
            xanchor="left",
            x=0.01, y=0.99,
            traceorder="reversed",
            title_font_family="Times New Roman",
            font=dict(
                family="Courier",
                color="black"
            ),
            bgcolor='rgb(192,192,192,0.5)',
            bordercolor="Black",
            borderwidth=2
        ),
        showlegend=True,
        legend_traceorder="reversed",
        yaxis=dict(
            tickmode="array",
            titlefont=dict(size=30)
        ),
        xaxis=dict(
            tickmode="array",
            titlefont=dict(size=30),
        )
    )
    fig_config = dict({
        'scrollZoom': False,
        'responsive': False,
        'staticPlot': False,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d', 'select'],
        'modeBarButtonsToAdd': ['drawline',
                                'drawrect',
                                'eraseshape'
                                ],
        'toImageButtonOptions': {
            'format': 'png',  # one of png, svg, jpeg, webp
            'filename': 'custom_image',
            'height': 500,
            'width': 700,
            'scale': 1
        }})
    xaxes_config = dict(
        showgrid=False, gridwidth=1, gridcolor='LightPink',
        zeroline=True, linewidth=2, linecolor='black', mirror=True,
        matches='x'
    )
    yaxes_config = dict(
        showgrid=True, gridwidth=1, gridcolor='gray',
        zeroline=True, linewidth=2, linecolor='black', mirror=True
    )
    annotation_config = dict(
        x="2022-02-16 00:30:00",  # must be changed with data
        y=1539,  # must be changed with data
        xref="x",
        yref="y",
        text=f"2022-02-16 00:30:00",  # must be changed with data
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            color="black"
        ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=20,
        ay=-30,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8
    )


class plot_configuration_fe():
    lbond_config = dict(color='rgba(255, 178, 102, 0.9)', width=2)
    ubond_config = dict(color='rgba(255, 178, 102, 0.9)', width=2)
    ubond_fill = 'rgba(255, 178, 102, 0.3)'
    color_actual = 'rgba(0, 0, 255, 1)'
    color_trend = 'rgba(0, 255, 0, 1)'
    anomaly_config = dict(color='rgba(255, 0, 0, 0.7)', size=10, line=dict(color='rgba(255, 0, 0, 1)', width=2))
    layout = dict(
        font=dict(
            size=10,
            color="rgba(123, 176, 244, 1)"
        ),
        title={
            'text': "",  # must be changed with data
            'xanchor': 'left',
            'yanchor': 'top'
        },
        plot_bgcolor='rgb(255,255,255,1)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        legend=dict(
            yanchor="top",
            xanchor="left",
            x=0.01, y=0.99,
            traceorder="reversed",
            title_font_family="Times New Roman",
            font=dict(
                family="Courier",
                color="black"
            ),
            bgcolor='rgb(192,192,192,0.5)',
            bordercolor="Black",
            borderwidth=2
        ),
        showlegend=True,
        legend_traceorder="reversed",
        yaxis=dict(
            tickmode="array",
            titlefont=dict(size=30)
        ),
        xaxis=dict(
            tickmode="array",
            titlefont=dict(size=30),
        )
    )
    fig_config = dict({
        'scrollZoom': False,
        'responsive': False,
        'staticPlot': False,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d', 'select'],
        'modeBarButtonsToAdd': ['drawline',
                                'drawrect',
                                'eraseshape'
                                ],
        'toImageButtonOptions': {
            'format': 'png',  # one of png, svg, jpeg, webp
            'filename': 'custom_image',
            'height': 500,
            'width': 700,
            'scale': 1
        }})
    xaxes_config = dict(
        showgrid=False, gridwidth=1, gridcolor='LightPink',
        zeroline=True, linewidth=2, linecolor='black', mirror=True,
        matches='x'
    )
    yaxes_config = dict(
        showgrid=True, gridwidth=1, gridcolor='gray',
        zeroline=True, linewidth=2, linecolor='black', mirror=True
    )
    annotation_config = dict(
        x="2022-02-16 00:30:00",  # must be changed with data
        y=1539,  # must be changed with data
        xref="x",
        yref="y",
        text=f"2022-02-16 00:30:00",  # must be changed with data
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            color="black"
        ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=20,
        ay=-30,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8
    )
