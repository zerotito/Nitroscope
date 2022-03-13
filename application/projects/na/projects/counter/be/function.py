import os, sys, json
import pandas as pd
from flask import render_template, request, jsonify
import socket
from datetime import datetime, timedelta

import dask.dataframe as dd
import numpy as np

import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Global Variables
SESSION_NAME = socket.gethostname()

CUR_DIRECTORY = os.path.dirname(__file__)
ABS_PATH = os.path.abspath(os.path.join(CUR_DIRECTORY, os.pardir))

CONF_FILE = "{}/conf/config.json".format(ABS_PATH)


def counter_analysis():

    # Loading configuration parameters
    module_config = json.loads(open('{}'.format(CONF_FILE), 'r').read())
    title = module_config["title"]
    webpage = "{}/{}".format(os.path.basename(ABS_PATH), module_config["webpage"])
    domains = module_config["config"]["groups"]
    clusters = {}
    for e in domains:
        clusters[e] = domains[e]["cluster"]
    return render_template(
        webpage, page_hdr=title,
        domains=clusters
    )


def counter_apiv1():
    clusters = {}

    # Loading configuration parameters
    module_config = json.loads(open('{}'.format(CONF_FILE), 'r').read())
    KPI_FOLDER = module_config["kpi folder"]
    json_data = request.get_json(force=True)
    cluster = json_data['node type']
    counter_list = []
    if cluster in module_config["config"]["groups"]:
        table_list = module_config["config"]["groups"][cluster]["table"]
        for table in table_list:
            file_name = f"{KPI_FOLDER}\\{table}.parquet"
            df = pd.read_parquet(file_name, engine="pyarrow")
            df = df.reset_index()
            column_list = list(df.columns)
            column_list.remove("datetime")
            column_list.remove("node")
            df = pd.DataFrame(column_list)
            df.columns = ["counter"]
            from application.common.counter_description import counter_description
            df["counter text"] = df["counter"].apply(lambda x: counter_description[x] if x in counter_description else x)
            df = df.drop_duplicates()
            df["table"] = table
            df = df[["table", "counter", "counter text"]]
            counter_list = counter_list + df.values.tolist()
    jsonString = json.dumps(counter_list)
    return jsonString


def counter_apiv2():
    response = {}

    # Loading configuration parameters
    module_config = json.loads(open('{}'.format(CONF_FILE), 'r').read())
    KPI_FOLDER = module_config["kpi folder"]

    transaction_id = datetime.strftime(datetime.today(), '%Y%m%d%H%M%S')
    json_data = request.get_json(force=True)
    table = json_data['table']
    kpi = json_data['kpi']
    kpi_text = json_data['kpi text']

    temp_folder = f"{ABS_PATH}/temp/{transaction_id}"
    os.makedirs(temp_folder, exist_ok=True)

    file_name = f"{KPI_FOLDER}\\{table}.parquet"
    df = pd.read_parquet(file_name, engine="pyarrow")
    df = df[["node", kpi]]
    df.reset_index(inplace=True)
    fig = px.line(df, x="datetime", y=kpi, color='node')
    fig.update_layout(autosize=True)
    title = f'<b>KPI:</b> {kpi}<br><b>KPI Text:</b> {kpi_text}'
    layout = dict(
        autosize=True,
        title={
            'text': title,
            'xanchor': 'left',
            'yanchor': 'top'
        }
    )
    fig.update_layout(layout)
    #graphJSON = plotly.io.to_json(fig)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    jsonString = json.dumps(graphJSON)
    return jsonString


def counter_apiv3():
    response = {}

    # Loading configuration parameters
    module_config = json.loads(open('{}'.format(CONF_FILE), 'r').read())

    json_data = request.get_json(force=True)

    table = json_data['table']
    kpi = json_data['kpi']
    temp_folder = json_data['folder']
    file_name = f'{temp_folder}\\anomaly\\{table}\\{kpi}.json'

    # Alarm Configuration
    graphJSON = json.loads(open(file_name, 'r').read())

    jsonString = json.dumps(graphJSON)
    return jsonString

def counter_apiv4():

    module_config = json.loads(open('{}'.format(CONF_FILE), 'r').read())
    KPI_FOLDER = module_config["kpi folder"]

    json_data = request.get_json(force=True)

    selected_date = json_data['date']
    temp_folder = json_data['folder']

    alarm_file = f'{KPI_FOLDER}\\alarms.parquet'
    df = pd.read_parquet(alarm_file, engine="pyarrow")
    df = df.reset_index()
    sdt = datetime.strptime(selected_date, "%Y-%m-%d %H:%M")
    edt = sdt + timedelta(hours=1)
    df = df[edt >= df.alarmtime]
    df = df[df.alarmtime >= sdt]
    df["alarmtime"] = df.alarmtime.astype('string')
    df = df[["alarmtime", "alarm", "text"]]

    table_values = list(df.values.tolist())

    jsonString = json.dumps(table_values)
    return jsonString

