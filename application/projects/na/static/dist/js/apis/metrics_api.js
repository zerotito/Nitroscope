function fetch_list_data(json_data, url){
    $.ajax({
        url: url,
        type: "post",
        data: JSON.stringify(json_data),
        dataType: "json",
        contentType: "application/json",
        success: function (data) {
            cluster_nodes = data
            temp_html = ""
            for (j = 0; j < data.length; j++) {
                t = '<option class="form-control form-control-user" value="' + data[j] + '">' + data[j] + '</option>'
                temp_html = temp_html + t
            }
            document.getElementById("node").innerHTML = temp_html
        },
        error: function (xhr, status, error) {
            console.log(error)
        }
      });
}

function fetch_fni_data(json_data, url){
    $.ajax({
        url: url,
        type: "post",
        data: JSON.stringify(json_data),
        dataType: "json",
        contentType: "application/json",
        success: function (data) {
            data_x = data
            temp_folder = data["temp folder"]

            table_counter.destroy();
            column_def_counter = [{ "visible": false, "targets": [0] }]
            cols_counter = prepare_columns(data["kpi table header"])
            table_counter = create_table('table_counter', cols_counter, column_def_counter)
            fill_tables(table_counter, data["kpi table"])

            $('#chart_alarm').remove();
            $('#chart_group_alarm').append('<div id="chart_alarm" style="width: 100%;height: 100%;"></div>');
            graph_alarm = data["alarm"]
            plot_alarm = document.getElementById('chart_alarm')
            var fig_config = {
                scrollZoom: false,
                responsive: true,
                staticPlot: false,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select'],
                modeBarButtonsToAdd: ['drawline',
                                        'drawrect',
                                        'eraseshape'
                                        ],
                toImageButtonOptions: {
                    format: 'png',
                    filename: 'custom_image',
                    height: 500,
                    width: 700,
                    scale: 1
                }}
            graph_alarm.config = fig_config

            Plotly.plot("chart_alarm", graph_alarm, {}, fig_config)

            plot_alarm.on('plotly_click', function(data){
                selected_date = data["points"][0]["x"]
                json_data = {
                    "folder": temp_folder,
                    "date": selected_date

                }
                fetch_alarms(json_data, "http://127.0.0.1:3000/na/metrics/apiv4")
            });

            $('#chart_trend').remove();
            $('#chart_group_trend').append('<div id="chart_trend" style="width: 100%;height: 100%;"></div>');
            var graph_trend = data["trend"]
            graph_trend.config = fig_config
            plot_trend = document.getElementById('chart_trend')
            Plotly.plot("chart_trend", graph_trend, {}, fig_config)

            $('#chart_anomaly').remove();
            $('#chart_group_anomaly').append('<div id="chart_anomaly" style="width: 100%;height: 100%;"></div>');
            var graph_anomaly = data["anomaly"]
            graph_anomaly.config = fig_config
            plot_anomaly = document.getElementById('chart_anomaly')
            Plotly.plot("chart_anomaly", graph_anomaly, {}, fig_config)

            $('#table_counter tbody').on( 'click', 'td', function () {
                var json_data = {
                    "table": table_counter.row( $(this).parents('tr') ).data()[0],
                    "folder": temp_folder,
                    "kpi": table_counter.row( $(this).parents('tr') ).data()[1]
                }
                fetch_analysis_data(json_data, "http://127.0.0.1:3000/na/metrics/apiv3")
            } );
        },
        error: function (xhr, status, error) {
            console.log(error)
        }
      });
}

function fetch_alarms(json_data, url){
    $.ajax({
        url: url,
        type: "post",
        data: JSON.stringify(json_data),
        dataType: "json",
        contentType: "application/json",
        success: function (data) {
            table_alarm.destroy();
            column_def_alarm = [{ "visible": false, "targets": [2] }]
            cols_alarms = prepare_columns(["Event Time", "Alarm Header", "Alarm Text"])
            table_alarm = create_table('table_alarm', cols_alarms, column_def_alarm)
            fill_tables(table_alarm, data)
            $('#table_alarm tbody').on('click', 'td', function () {
                document.getElementById('alarm_content').innerHTML = ""
                if ( $(this).hasClass('selected') ) {
                    $(this).removeClass('selected');
                }
                else {
                    table_alarm.$('tr.selected').removeClass('selected');
                    $(this).addClass('selected');
                }
                var alarm_text = table_alarm.row( $(this).parents('tr') ).data()[2];
                document.getElementById('alarm_content').innerHTML = "<p>" + alarm_text + "</p>"
            })
        },
        error: function (xhr, status, error) {
            console.log("Hata : " + error);
        }
      });
}

function fetch_analysis_data(json_data, url){
    console.log(json_data)
    $.ajax({
        url: url,
        type: "post",
        data: JSON.stringify(json_data),
        dataType: "json",
        contentType: "application/json",
        success: function (data) {
            $('#chart_counter').remove();
            $('#chart_group_counter').append('<div id="chart_counter" style="width: 100%;height: 100%;"></div>');
            var graph_counter = data
            plot_counter = document.getElementById('chart_counter')
            var fig_config = {
                scrollZoom: false,
                responsive: true,
                staticPlot: false,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select'],
                modeBarButtonsToAdd: ['drawline',
                                        'drawrect',
                                        'eraseshape'
                                        ],
                toImageButtonOptions: {
                    format: 'png',
                    filename: 'custom_image',
                    height: 500,
                    width: 700,
                    scale: 1
                }}
            graph_counter.config = fig_config
            Plotly.plot("chart_counter", graph_counter, {}, fig_config)
        },
        error: function (xhr, status, error) {
            console.log("Hata : " + error);
        }
      });
}

// DataTable Functions
function fill_tables(table_id, datas){
    table_id.clear()
    table_id.draw()
    for (j = 0; j < datas.length; j++) {
        table_id.row.add(datas[j]);
    }
    table_id.draw()
}

function create_table(table_id, column_list, column_defs){
    return $('#' + table_id).DataTable( {
        "paging":   true,
        "ordering": true,
        "info":     true,
        "searching": true,
        "select": true,
         columns: column_list,
         "columnDefs": column_defs
    });
}

function prepare_columns(data) {
    var col_list = []
    for (j = 0; j < data.length; j++) {
        col_list[j] = { title: data[j] }
    }
    return col_list
}