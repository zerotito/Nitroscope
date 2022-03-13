function fetch_counter_data(json_data, url){
    $.ajax({
        url: url,
        type: "post",
        data: JSON.stringify(json_data),
        dataType: "json",
        contentType: "application/json",
        success: function (data) {
            data_x = data

            table_counter.destroy();
            column_def_counter = [{ "visible": false, "targets": [] }]
            cols_counters = prepare_columns(["Table", "Counter", "Description"])
            table_counter = create_table('table_counter', cols_counters, column_def_counter)
            fill_tables(table_counter, data)

            $('#table_counter tbody').on( 'click', 'td', function () {
                var json_data = {
                    "table": table_counter.row( $(this).parents('tr') ).data()[0],
                    "kpi": table_counter.row( $(this).parents('tr') ).data()[1],
                    "kpi text": table_counter.row( $(this).parents('tr') ).data()[2]
                }
                fetch_analysis_data(json_data, window.location.href + "/apiv2")
            } );
        },
        error: function (xhr, status, error) {
            console.log(error)
        }
      });
}

function fetch_analysis_data(json_data, url){
    $.ajax({
        url: url,
        type: "post",
        data: JSON.stringify(json_data),
        dataType: "json",
        contentType: "application/json",
        success: function (data) {
            data_x = data

            $('#chart_counter').remove();
            $('#chart_group_counter').append('<div id="chart_counter" style="width: 100%;height: 100%;"></div>');
            graph_object = JSON.parse(data)
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
            graph_object.config = fig_config

            Plotly.plot("chart_counter", graph_object, {}, fig_config)
        },
        error: function (xhr, status, error) {
            console.log(error)
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