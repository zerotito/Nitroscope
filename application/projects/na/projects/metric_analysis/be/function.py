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


def metric_analysis():

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

def metric_apiv1():
    clusters = {}

    # Loading configuration parameters
    module_config = json.loads(open('{}'.format(CONF_FILE), 'r').read())["config"]["clusters"]

    json_data = request.get_json(force=True)
    cluster = json_data['cluster']
    if cluster in module_config:
        clusters = module_config[cluster]
    jsonString = json.dumps(clusters)
    return jsonString


def metric_apiv2():
    response = {}

    # Loading configuration parameters
    m_config = json.loads(open('{}'.format(CONF_FILE), 'r').read())
    module_config = m_config["config"]["clusters"]
    KPI_FOLDER = m_config["kpi folder"]
    script = m_config["script"]

    transaction_id = datetime.strftime(datetime.today(), '%Y%m%d%H%M%S')
    json_data = request.get_json(force=True)
    node_type = json_data['node type']
    cluster = json_data['cluster']
    node = json_data['node']

    temp_folder = f"{ABS_PATH}/temp/{transaction_id}"
    os.makedirs(temp_folder, exist_ok=True)

    # Files
    fn_alarm_trend = f"{temp_folder}/alarm_trend.json"
    fn_alarm_detail = f"{KPI_FOLDER}/alarm_info.parquet"
    fn_trend = f"{temp_folder}/trend.json"
    fn_anomaly = f"{temp_folder}/anomaly.json"
    fn_kpi_info = f"{temp_folder}/kpi_analysis.json"

    table_list = m_config["config"]["groups"][node_type]["table"]
    json_data = {
        "node type": node_type,
        "cluster": cluster,
        "node": node,
        "temp folder": temp_folder,
        "table list": table_list
    }
    with open(f'{temp_folder}/config.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False)

    # Run KPI Analysis
    os.system(f'python {script} {temp_folder}')

    # Alarm Information
    graphJSON_alarm = json.loads(open(fn_alarm_trend, 'r').read())

    # Trend Graph
    graphJSON_trend = json.loads(open(fn_trend, 'r').read())

    # Anomaly Graph
    graphJSON_anomaly = json.loads(open(fn_anomaly, 'r').read())

    # KPI Results
    kpi_result = json.loads(open(fn_kpi_info, 'r').read())

    kpi_table_dict = {}
    for kf, values in kpi_result.items():
        kpi_table_dict[kf] = {}
        for e in values["trends"]:
            if e["flag"]:
                kpi_table_dict[kf][e["kpi"]] = ["True"]
        for e in values["anomalies"]:
            if e["kpi id"] not in kpi_table_dict[kf]:
                kpi_table_dict[kf][e["kpi id"]] = [
                    "False",
                    e["kpi"],
                    str(e["flag"])
                ]
            else:
                kpi_table_dict[kf][e["kpi id"]] = kpi_table_dict[kf][e["kpi id"]] + [e["kpi"], str(e["flag"])]
    kpi_table = []
    for kf in kpi_table_dict:
        for kpi, kpiv in kpi_table_dict[kf].items():
            t = [kf, kpi, kpiv[1], kpiv[2], kpiv[0]]
            kpi_table.append(t)
    table_header = ["Table", "KPI Id", "KPI Text", "Anomaly", "Trend Change"]
    response = {
        "alarm": graphJSON_alarm,
        "trend": graphJSON_trend,
        "anomaly": graphJSON_anomaly,
        "kpi table": kpi_table,
        "kpi table header": table_header,
        "temp folder": temp_folder
    }
    jsonString = json.dumps(response)
    return jsonString


def metric_apiv3():
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

def metric_apiv4():

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

