$(document).ready(function () {
    /** MAIN JAVASCRIPT **/


        // const host = "http://35.176.56.125:5000";
    const host = "http://localhost:5000";
    const socket = io(host);
    // Updates the current time every second
    setInterval(function () {
        var today = new Date();
        var time = today.getFullYear() + '-' + (today.getMonth() + 1) + '-' + today.getDate() + " " + today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
        $('#time').text(time);
    }, 1000);

    // Sends the update period to the RPi via the SocketServer
    $('#update_period_button').click(() => {
        socket.emit("set_update_period", $('#update_period').val());
    });

    // Ask the server for the temp when page is refreshed/loaded
    socket.emit("get_temp_from_pi");

    // Sends the required temperature to the Rpi via the SocketServer
    $('#required_temp_button').click(() => {
        socket.emit("set_required_temp", $('#required_temp').val());
    });

    // Sets the relays when the checkbox is clicked
    $('#relay2').change(function () {
        set_relays();
    });
    $('#relay3').change(function () {
        set_relays();
    });
    $('#relay4').change(function () {
        set_relays();
    });


    /** Sets the states of the relays and the timeout for them being on **/
    function set_relays() {
        let relay_states = {
            1: {"state": $('#relay1').prop("checked"), "timeout": ""},
            2: {"state": $('#relay2').prop("checked"), "timeout": $('#r2_timeout').val()},
            3: {"state": $('#relay3').prop("checked"), "timeout": $('#r3_timeout').val()},
            4: {"state": $('#relay4').prop("checked"), "timeout": $('#r4_timeout').val()}
        }

        socket.emit('set_relay_state', relay_states);
    }

    // Receives the update period value that is stored in the SocketServer
    socket.on("update_req_period", (period) => {
        $('#update_period').val(period);
                $('#last_time_updated').val("ABC");

    });

    // Receives the required temp value that is stored in the Socket Server
    socket.on("set_required_temp", (temp) => {
        $('#required_temp').val(temp);
    });

    // Receives the last updated time from the Socket Server.
    socket.on("set_UI_last_updated", (time_val) => {
        $('#last_time_updated').text(time_val);
    });

    socket.on("update_temps", (temps) => {
        $('#temp1').text(temps.t1);
        $('#temp2').text(temps.t2);
    });

    // Receives the relay states that are stored in the SocketServer
    socket.on("update_relay_state", (states_json) => {
        $('#relay1').prop("checked", (states_json[1].state == true));
        $('#relay2').prop("checked", (states_json[2].state == true));
        $('#relay3').prop("checked", (states_json[3].state == true));
        $('#relay4').prop("checked", (states_json[4].state == true));
    });

    // Camera Control
    $('#photo1').click(() => {
        socket.emit("camera", "photo");
    });

    // $('#video1').click(() => {
    //     socket.emit("camera", "video");
    // });


    var day_count = 0;
    $('#update_graph').click(() => {
        day_count = 0;
        update_graph(0);
    });

    $('#back_day').click(() => {
        day_count--;
        update_graph(day_count);
    });

    $('#forward_day').click(() => {
        day_count++;
        update_graph(day_count);
    });

    // The parameter is the list position, this is either -1 0 or +1, 0 is current
    // the other values are used to go back and  forwards in the list of images
    $('#update_photo1').click(() => {
        socket.emit('get_latest_snap', 0);
    });

    $('#back_day_photo').click(() => {
        socket.emit('get_latest_snap', -1);
    });

    $('#forward_day_photo').click(() => {
        socket.emit('get_latest_snap', +1);
    });

    socket.on('set_latest_snap', (latest_snap) => {
        console.log("set_latest_snap");
        $('#photo_title').text(latest_snap)
        $('#snap').attr('src', latest_snap);
    });

    // $('#update_video1').click(() => {
    //     console.log("update_video1 button")
    //     socket.emit('get_latest_vid');
    // });
    // socket.on('set_latest_vid', (latest_vid) => {
    //     console.log("set_latest_vid " + latest_vid);
    //     $('#vid').attr('src', latest_vid);
    // });


    /** END MAIN JAVASCRIPT **/
});
