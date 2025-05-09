document.addEventListener('DOMContentLoaded', function () {
	Highcharts.chart('emotionChart', {
		chart: { type: 'column' },
		title: { text: 'Emotion Distribution' },
		xAxis: { categories: window.chartData.emotions.labels },
		series: [{ name: 'Emotions', data: window.chartData.emotions.values }]
	});

	Highcharts.chart('polarityChart', {
		chart: { type: 'pie' },
		title: { text: 'Polarity Distribution' },
		series: [{
			name: 'Polarity',
			colorByPoint: true,
			data: window.chartData.polarities
		}]
	});

	Highcharts.chart('scoreChart', {
		chart: { type: 'bar' },
		title: { text: 'Average Scores' },
		xAxis: { categories: ['Confidence Score', 'Sentiment Score'] },
		series: [{
			name: 'Scores',
			data: window.chartData.scores
		}]
	});

	Highcharts.chart('keywordChart', {
		chart: { type: 'column' },
		title: { text: 'Top Keywords' },
		xAxis: { categories: window.chartData.keywords.labels },
		series: [{
			name: 'Count',
			data: window.chartData.keywords.values
		}]
	});
});

function toggleUserDropdown() {
    const dropdown = document.getElementById("userDropdown");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

window.onclick = function(event) {
    if (!event.target.matches('#userBtn')) {
        const dropdown = document.getElementById("userDropdown");
        if (dropdown && dropdown.style.display === "block") {
            dropdown.style.display = "none";
        }
    }
}
function logout() {
    sessionStorage.removeItem('apiKey');
    window.location.href = "/logout";
}
