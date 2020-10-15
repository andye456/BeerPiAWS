// set the dimensions and margins of the graph


update_graph = function () {
    d3.select('#svg').remove();
    show_graph();
}
show_graph = function () {
    var margin = {top: 10, right: 100, bottom: 120, left: 30},
        width = 1000 - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;

// append the svg object to the body of the page
    var svg = d3.select("#graph1")
        .append("svg")
        // .attr("width", width + margin.left + margin.right)
        .attr("id", "svg")
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    today = getDateTime()
//Read the data
    d3.csv("Receiver/temp_files/temp_data_" + today + ".csv",
        function (d) {
            // format date fields
            return {time: d3.timeParse("%d-%m-%Y_%H-%M-%S")(d.time), temp1: d.temp1, temp2: d.temp2, relay1: d.relay1}
        },

        function (data) {
            const xwidth = data.length * 4 + margin.left + margin.right;

            d3.select('#svg').attr("width", xwidth + 200);
            console.log(data);
            // List of groups (here I have one group per column)
            var allGroup = ["temp1", "temp2", "relay1"]

            // Reformat the data: we need an array of arrays of {x, y} tuples
            var dataReady = allGroup.map(function (grpName) { // .map allows to do something for each element of the list
                return {
                    name: grpName,
                    values: data.map(function (d) {
                        return {time: d.time, value: +d[grpName]};
                    })
                };
            });
            // I strongly advise to have a look to dataReady with
            // console.log(dataReady)

            // A color scale: one color for each group
            var myColor = d3.scaleOrdinal()
                .domain(allGroup)
                .range(d3.schemeSet2);

            // Add X axis --> it is a date format

            var x = d3.scaleTime()
                .domain(d3.extent(data, function (d) {
                    return d.time;
                }))
                .range([0, xwidth]);
            xAxis = d3.axisBottom(x)
            svg.append("g")
                .attr("transform", "translate(0," + height + ")")
                .call(xAxis.ticks(d3.timeMinute))
                .selectAll("text")
                .attr("transform", "rotate(90)")
                .style("text-anchor", "start")
            ;

            // Add Y axis
            var y = d3.scaleLinear()
                .domain([0, 35])
                .range([height, 0]);
            svg.append("g")
                .call(d3.axisLeft(y));

            // Add the lines
            var line = d3.line()
                .x(function (d) {
                    return x(+d.time)
                })
                .y(function (d) {
                    return y(+d.value)
                });
            svg.selectAll("myLines")
                .data(dataReady)
                .enter()
                .append("path")
                .attr("d", function (d) {
                    return line(d.values)
                })
                .attr("stroke", function (d) {
                    return myColor(d.name)
                })
                .style("stroke-width", 1)
                .style("fill", "none");

            var tooltip = d3.select("#graph1")
                .append("div")
                .style("opacity", 0)
                .attr("class", "tooltip")
                .style("background-color", "white")
                .style("border", "solid")
                .style("border-width", "1px")
                .style("border-radius", "5px")
                .style("padding", "10px");

            var mouseover = function (d) {
                tooltip
                    .style("opacity", 1)
            }

            var mousemove = function (d) {
                tooltip
                    .html("Temperature: " + d.value+"<br>Time: "+('0'+d.time.getHours()).slice(-2)+":"+('0'+d.time.getMinutes()).slice(-2)+":"+('0'+d.time.getSeconds()).slice(-2))
                    .style("left", (d3.mouse(this)[0] + 90) + "px") // It is important to put the +90: other wise the tooltip is exactly where the point is an it creates a weird effect
                    .style("top", (d3.mouse(this)[1]) + "px")
            }

            // A function that change this tooltip when the leaves a point: just need to set opacity to 0 again
            var mouseleave = function (d) {
                tooltip
                    .transition()
                    .duration(200)
                    .style("opacity", 0)
            }

            // Add the points
            svg
                // First we need to enter in a group
                .selectAll("myDots")
                .data(dataReady)
                .enter()
                .append('g')
                .style("fill", function (d) {
                    return myColor(d.name)
                })
                // Second we need to enter in the 'values' part of this group
                .selectAll("myPoints")
                .data(function (d) {
                    return d.values
                })
                .enter()
                .append("circle")
                .attr("cx", function (d) {
                    return x(d.time)
                })
                .attr("cy", function (d) {
                    return y(d.value)
                })
                .attr("r", 3)
                .attr("stroke", "white")
                .on("mouseover", mouseover)
                .on("mousemove", mousemove)
                .on("mouseleave", mouseleave)
            ;

            // Add a legend at the end of each line
            svg
                .selectAll("myLabels")
                .data(dataReady)
                .enter()
                .append('g')
                .append("text")
                .datum(function (d) {
                    return {name: d.name, value: d.values[d.values.length - 1]};
                }) // keep only the last value of each time series
                .attr("transform", function (d) {
                    return "translate(" + x(d.value.time) + "," + y(d.value.value) + ")";
                }) // Put the text at the position of the last point
                .attr("x", 12) // shift the text a bit more right
                .text(function (d) {
                    return d.name;
                })
                .style("fill", function (d) {
                    return myColor(d.name)
                })
                .style("font-size", 15)

        })
}

function getDateTime() {

    var date = new Date();

    var hour = date.getHours();
    hour = (hour < 10 ? "0" : "") + hour;

    var min = date.getMinutes();
    min = (min < 10 ? "0" : "") + min;

    var sec = date.getSeconds();
    sec = (sec < 10 ? "0" : "") + sec;

    var year = date.getFullYear();

    var month = date.getMonth() + 1;
    month = (month < 10 ? "0" : "") + month;

    var day = date.getDate();
    day = (day < 10 ? "0" : "") + day;

    // return year + "-" + month + "-" + day + "T" + hour + ":" + imn + ":" + sec;
    return day + "-" + month + "-" + year;

}