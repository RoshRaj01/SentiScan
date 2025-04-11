// admin.js
document.addEventListener("DOMContentLoaded", () => {
  // Sample data (replace with real API calls)
  const adminData = {
    totalUsers: 125,
    predictedEmotions: {
      Happy: 45,
      Sad: 20,
      Neutral: 35
    },
    usageSummary: {
      avgSessions: 3.4,
      avgDuration: "5m 12s"
    }
  };

  // Update the DOM with admin data
  document.getElementById("total-users").innerText = adminData.totalUsers;
  document.getElementById("predicted-emotions").innerText =
    `Happy: ${adminData.predictedEmotions.Happy}% | Sad: ${adminData.predictedEmotions.Sad}% | Neutral: ${adminData.predictedEmotions.Neutral}%`;
  document.getElementById("usage-summary").innerText =
    `Avg. Sessions per User: ${adminData.usageSummary.avgSessions} | Avg. Session Duration: ${adminData.usageSummary.avgDuration}`;

  // If Chart.js is loaded, initialize sample charts
  if (typeof Chart !== "undefined") {
    // Chart 1: User Growth (Line Chart)
    const ctx1 = document.getElementById("chart1").getContext("2d");
    new Chart(ctx1, {
      type: "line",
      data: {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        datasets: [{
          label: "User Growth",
          data: [50, 70, 90, 110, 125, 140],
          backgroundColor: "rgba(106, 193, 151, 0.2)",
          borderColor: "rgba(106, 193, 151, 1)",
          borderWidth: 2,
          fill: true,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      }
    });

    // Chart 2: Emotion Distribution (Pie Chart)
    const ctx2 = document.getElementById("chart2").getContext("2d");
    new Chart(ctx2, {
      type: "pie",
      data: {
        labels: ["Happy", "Sad", "Neutral"],
        datasets: [{
          data: [
            adminData.predictedEmotions.Happy,
            adminData.predictedEmotions.Sad,
            adminData.predictedEmotions.Neutral
          ],
          backgroundColor: [
            "rgba(75, 192, 192, 0.6)",
            "rgba(255, 99, 132, 0.6)",
            "rgba(255, 206, 86, 0.6)"
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      }
    });

    // Chart 3: Usage Statistics (Bar Chart)
    // For demonstration, converting "5m 12s" to seconds = 312 seconds.
    const ctx3 = document.getElementById("chart3").getContext("2d");
    new Chart(ctx3, {
      type: "bar",
      data: {
        labels: ["Avg Sessions", "Avg Duration (s)"],
        datasets: [{
          label: "Usage Stats",
          data: [adminData.usageSummary.avgSessions, 312],
          backgroundColor: [
            "rgba(153, 102, 255, 0.6)",
            "rgba(255, 159, 64, 0.6)"
          ],
          borderColor: [
            "rgba(153, 102, 255, 1)",
            "rgba(255, 159, 64, 1)"
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  } else {
    console.warn("Chart.js library is not loaded. Charts will not be displayed.");
  }
});
