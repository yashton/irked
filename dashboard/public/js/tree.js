$(function() {
    var source = "tree.json";
    var target = $('#network_tree');
    var h = target.height(), w = target.width();
    var color = "#000000";

    var vis = d3.select("#network_tree").append("svg:svg")
        .attr("width", w)
        .attr("height", h);

    d3.json(source, function(json) {
        $('#tree_loading:visible').hide('fade', 'slow');
        $('#network_tree:hidden').show('fade', 'slow');
        var force = self.force = d3.layout.force()
            .nodes(json.nodes)
            .links(json.links)
            .gravity(.04)
            .distance(100)
            .charge(-100)
            .size([w, h])
            .start();

        var link = vis.selectAll("line.link")
            .data(json.links)
            .enter().append("svg:line")
            .attr("class", "link")
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        var node = vis.selectAll("g.node")
            .data(json.nodes)
            .enter().append("svg:g")
            .attr("class", "node")
            .call(force.drag);

        node.append("svg:circle")
            .attr("class", "node")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", 15)
            .style("fill", color)
            .call(force.drag);

        node.append("svg:text")
            .attr("class", "nodetext no-select")
            .attr("dx", 18)
            .attr("dy", ".35em")
            .style("fill", "white")
            .text(function(d) { return d.name });

        force.on("tick", function() {
            link.attr("x1", function(d) { return d.source.x; })
                .attr("y1", function(d) { return d.source.y; })
                .attr("x2", function(d) { return d.target.x; })
                .attr("y2", function(d) { return d.target.y; });

            node.attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
        });
    });
});
