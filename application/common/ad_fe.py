import sys, importlib
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

from counter_description import counter_description
from common import *
from common import plot_configuration_fe as pc


CUR_DIRECTORY = sys.argv[1]
cpu_process_count = int(cpu_count() / 4 * 3)  # To optimize the cpu load, cpu_process_count can be modified
control_list = []


logging.info('Fetching parameters from JSON')
try:
    with open(f"{CUR_DIRECTORY}/config.json") as json_file:
        config = json.load(json_file)
    node_type = config["node type"]
    cluster = config["cluster"]
    node = config["node"]
    temp_folder = config["temp folder"]
    table_list = config["table list"]
    ANOMALY_FOLDER = f"{temp_folder}\\anomaly"
    os.makedirs(ANOMALY_FOLDER, exist_ok=True)
    fn_alarm_detail = f"{KPI_FOLDER}/alarms.parquet"
    fn_alarm_trend = f"{temp_folder}/alarm_trend.json"
    fn_kpi_info = f"{temp_folder}/kpi_analysis.json"
    fn_trend = f"{temp_folder}/trend.json"
    fn_anomaly = f"{temp_folder}/anomaly.json"
except Exception as e:
    logging.error(f'Fetching parameters from JSON : {e}')
    exit()

if __name__ == '__main__':
    global_trend = {}
    global_anomalies = {}
    global_info = {}
    logging.info(f"Fetching Alarms")
    alarm_anomalies(node, fn_alarm_detail, fn_alarm_trend)

    for table in table_list:
        global_trend[table] = []
        global_anomalies[table] = []
        global_info[table] = {}
        KPI_FILE = f'{KPI_FOLDER}\\{table}.parquet'
        logging.info(f"Fetching Table : {table}")
        df_data = pd.read_parquet(KPI_FILE, engine="pyarrow", filters=[(OBJECT_COLUMN, '==', node)])
        kpi_list = list(df_data.columns)
        kpi_list.remove(OBJECT_COLUMN)
        global_info[table]["kpi count"] = len(kpi_list)
        logging.info(f"Preparing Series for parallel operation : {table}")
        df_series = prepare_kpi_series_lv1(kpi_list, df_data, OBJECT_COLUMN, ad_config, size=100)
        logging.info(f"Calculating trend changes : {table}")
        predictions = run_in_parallel(calculate_trend_change, df_series, cpu_process_count=cpu_process_count, desc=table)
        for e in predictions:
            if not e["flag"]: continue
            global_trend[table].append(e)
        logging.info(f"Calculating anomalies : {table}")
        predictions = run_in_parallel(calculate_anomaly_fe, df_series, cpu_process_count=cpu_process_count, desc=table)
        global_anomalies[table] = predictions

    logging.info("Figuring Anomalies")
    for table, gas in global_anomalies.items():
        T_PLOT_FOLDER = f'{ANOMALY_FOLDER}\\{table}'
        os.makedirs(T_PLOT_FOLDER, exist_ok=True)
        for e in gas:
            e["folder"] = T_PLOT_FOLDER
            e["pc"] = pc
            for e2 in global_trend[table]:
                changes = []
                if "kpi" in e2:
                    if e["kpi"] == e2["kpi"]:
                        changes = e2["changes"]
                        break
            e["changepoints"] = changes
            kpi = e["kpi"]
            kpi_text = kpi
            if kpi in counter_description:
                kpi_text = counter_description[kpi]
            e["kpi"] = kpi_text
            e["kpi id"] = kpi
        t = run_in_parallel(prepare_plot_from_list_fe, gas, cpu_process_count=cpu_process_count, desc=table)


    logging.info("Exporting Infos")
    for kf, gas in global_anomalies.items():
        for e in gas:
            del e["pc"]
            del e["data"]
    for e in global_info:
        global_info[e]["trends"] = global_trend[e]
        global_info[e]["anomalies"] = global_anomalies[e]
    with open(fn_kpi_info, 'w', encoding='utf-8') as f:
        json.dump(global_info, f, ensure_ascii=False)

    logging.info("Figuring Trend Changes")
    labels = ['Trend Change', 'Total Counter']
    kpi_count = 0
    change_count = 0
    for kf in global_info:
        kpi_count = kpi_count + global_info[kf]["kpi count"]
        for e in global_info[kf]["trends"]:
            if "kpi" in e and e["node"] == node:
                change_count = change_count + 1
    values = [change_count, kpi_count]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, pull=[0.2, 0])])
    fig.update_traces(marker=dict(colors=["gold", "purple"], line=dict(color='#000000', width=1)))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, zeroline=False)
    fig.update_xaxes(showgrid=False, gridwidth=1, gridcolor='gray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='gray')
    fig.update_layout({
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
            "font_color": "rgba(123, 176, 244, 1)",
        }, showlegend=False)
    fig.update_xaxes(title_font=dict(color="rgba(0, 0, 0, 0)"))
    fig.update_yaxes(title_font=dict(color="rgba(0, 0, 0, 0)"))
    fig.update_yaxes(ticksuffix="  ")
    #fig.update_layout(margin={'t': 0})
    fig.update_layout(autosize=True, margin={'t': 0})
    fig.write_json(fn_trend)

    labels = ['Anomalies', 'Total Counter']
    kpi_count = 0
    change_count = 0
    for kf in global_info:
        kpi_count = kpi_count + global_info[kf]["kpi count"]
        for e in global_info[kf]["anomalies"]:
            if "kpi" in e and e["flag"] and e["node"] == node:
                change_count = change_count + 1
    values = [change_count, kpi_count]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, pull=[0.2, 0])])
    fig.update_traces(marker=dict(colors=["red", "green"], line=dict(color='#000000', width=1)))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, zeroline=False)
    fig.update_xaxes(showgrid=False, gridwidth=1, gridcolor='gray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='gray')
    fig.update_layout({
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
            "font_color": "rgba(123, 176, 244, 1)",
        })
    fig.update_layout(autosize=True, margin={'t': 0})
    #fig.update_layout(margin={'t': 0})
    fig.update_xaxes(title_font=dict(color="rgba(0, 0, 0, 0)"))
    fig.update_yaxes(title_font=dict(color="rgba(0, 0, 0, 0)"))
    fig.update_yaxes(ticksuffix="  ")
    fig.write_json(fn_anomaly)