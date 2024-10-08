window.onload = function () {
    var chartDom = document.getElementById('chart');
    var myChart = echarts.init(chartDom);
    var option;

    option = {
        tooltip: {
            trigger: "axis",
            position: function (pt) {
                return [pt[0], "10%"];
            }
        },
        title: {
            left: "center",
            text: "Historical Prices",
            textStyle: {
                color: "#fff",
                fontStyle: "normal"
            }
        },
        xAxis: {
            type: "category",
            boundaryGap: false,
            // data: priceData["dates"]
        },
        yAxis: {
            type: "value",
            boundaryGap: [0, "100%"]
        },
        dataZoom: [
            {
                type: "inside",
                start: 90,
                end: 100
            },
            {
                start: 0,
                end: 10,
                handleIcon:
                    "M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z",
                handleSize: "80%",
                handleStyle: {
                    color: "#fff",
                    shadowBlur: 3,
                    shadowColor: "rgba(0, 0, 0, 0.6)",
                    shadowOffsetX: 2,
                    shadowOffsetY: 2
                }
            }
        ],
        series: [
            {
                name: "Historical Prices",
                type: "line",
                smooth: true,
                symbol: "none",
                sampling: "average",
                itemStyle: {
                    color: "#f2d024"
                },
                areaStyle: {
                    color: "#f2d024"
                },
                data: data
            }
        ],
        textStyle: {
            color: "#fff"
        }
    }

    option && myChart.setOption(option);
}


