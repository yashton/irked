$(function () {
    var data_source = 'data.json';
    var users_source = 'users.json';
    var messages_source = 'messages.json';

    var update_interval = 1000;

    var options = {
        series: { shadowSize: 0 }, // drawing is faster without shadows
        xaxis: { mode: "time", ticks: 3, color: "#FFF" },
        yaxis: { color: "#FFF" }
    };

    $.plot($("#data_graph"),
           [ { label: "Received", data: [] },
             { label: "Sent", data: [] }],
           options);
    $.plot($("#users_graph"),
           [ { label: "Users", data: [] } ],
           options);
    $.plot($("#messages_graph"),
           [ { label: "Messages", data: [] } ],
           options);

    function update_plot(canvas, loading, source)
    {
        function update_applied() {
            $.ajax({
                url: source,
                dataType: 'json',
                success: function(data) {
                    $(loading + ':visible').hide('fade', 'slow');
                    $(canvas + ':hidden').show('fade', 'slow');
                    if (data)
                        $.plot($(canvas), data, options);
                    setTimeout(update_applied, update_interval);
                },
                error: function() {
                    console.log(arguments);
                    setTimeout(update_applied, update_interval);
                }
            });
        }
        update_applied();
    }

    update_plot('#data_graph', '#data_loading', data_source);
    update_plot('#users_graph', '#users_loading', users_source);
    update_plot('#messages_graph', '#messages_loading', messages_source);
});
