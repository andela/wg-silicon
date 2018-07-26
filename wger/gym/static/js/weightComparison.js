members_weight_entries = JSON.parse(members_weight_entries.replace(/&quot;/g, '"'));
const dates = members_weight_entries.dates;
const user_weights = members_weight_entries.user_weights;
const plot_dataset = [];
const usernames = Object.keys(members_weight_entries.user_weights);

type = type;

const ctx = document.getElementById('weightChart');

// generate a random color 
const getRandomColor = () => {
    let length = 6;
    let chars = '0123456789ABCDEF';
    let color = '#';
    while (length--) color += chars[(Math.random() * 16) | 0];
    return color;
}

for (const [key, value] of Object.entries(user_weights)) {
    color = getRandomColor()
    plot_dataset.push({
        label: key,
        data: value,
        backgroundColor: color,
        borderColor: color,
        lineTension: 0.3,
        fill: false,
    },
)
}
Chart.defaults.line.spanGaps = true;
const chart = new Chart(ctx, {
    // The type of chart we want to create
    type: type,

    // The data for our dataset
    data: {
        labels: dates,
        datasets: plot_dataset
    },

    // Configuration options for the chart
    options: {
        legend: {
            display: true,
            position: 'right',
            spanGaps: true,
            labels: {
                text: 'Users',
                boxWidth: 20,
                fontColor: 'black'
            },
            title:{
                text: 'Users'
            }
        },
        scales: {
            yAxes: [{
                scaleLabel: {
                    display: true,
                    labelString: 'Weight in Kgs'
                }
            }],
            xAxes: [{
                scaleLabel: {
                    display: true,
                    labelString: 'Dates'
                }
            }]
        }
    }
});

$('.plot-type').click(function(){
    var type = $(this).data('type');
    chart.config.type = type;
    chart.update();
})

$('button').on('click', function(){
    $('button').removeClass('selected');
    $(this).addClass('selected');
});