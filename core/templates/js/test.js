function show()
{

    var vertex = new vis.DataSet([
        {id:1, label:"vertex 1"},
        {id:2, label:"vertex 2"},
        {id:3, label:"vertex 3"},
        {id:4, label:"vertex 4"},
        {id:5, label:"vertex 5"},
        {id:6, label:"vertex 6"},
    ]);

    var relate = new vis.DataSet([
        {from:1, to:2},
        {from:1, to:3},
        {from:2, to:4},
        {from:2, to:5},
        {from:3, to:6},
        {from:4, to:5},
    ]);

    var myDiv = document.getElementById("media");

    var data = {
        nodes: vertex,
        edges: relate
    };

    var options = {};

    var network = new vis.Network(myDiv,data,options)
}