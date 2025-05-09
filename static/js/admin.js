document.addEventListener("DOMContentLoaded", function () {

    Highcharts.chart('totalUsersChart', {
        chart: { type: 'column' },
        title: { text: 'Total Users' },
        xAxis: { categories: ['Users'] },
        yAxis: { title: { text: 'Number of Users' } },
        series: [{
            name: 'Users',
            data: [totalUsers]
        }]
    });

    Highcharts.chart('modelsChart', {
        chart: { type: 'pie' },
        title: { text: 'Models Used Distribution' },
        series: [{
            name: 'Users',
            colorByPoint: true,
            data: [
                { name: 'r1', y: modelCounts.r1 },
                { name: 'r2', y: modelCounts.r2 },
                { name: 'r3', y: modelCounts.r3 }
            ]
        }]
    });

    const sortedEmotions = Object.entries(emotions)
        .sort((a, b) => b[1] - a[1]);

    const sortedCategories = sortedEmotions.map(item => item[0]);
    const sortedData = sortedEmotions.map(item => item[1]);

    Highcharts.chart('emotionsChart', {
        chart: { type: 'column' },
        title: { text: 'Emotion Predictions' },
        xAxis: {
            categories: sortedCategories,
            title: { text: 'Emotions' }
        },
        yAxis: { title: { text: 'Count' } },
        series: [{
            name: 'Predictions',
            data: sortedData
        }]
    });

});
