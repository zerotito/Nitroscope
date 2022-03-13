function update1(){
    node_type = document.getElementById('node_type').value
    temp_html = ""
    for (j = 0; j < clusters[node_type].length; j++) {
        text  = clusters[node_type][j]
        t = '<option class="form-control form-control-user" value="' + text + '">' + text + '</option>'
        temp_html = temp_html + t
        }
    document.getElementById("cluster").innerHTML = temp_html
    update2()
}

function update2(){

    var json_data = {
        "node type": document.getElementById('node_type').value,
        "cluster": document.getElementById('cluster').value
        }
    fetch_list_data(json_data, window.location.href + "/apiv1")
}