document.addEventListener("DOMContentLoaded", function () {
    const chartContainer = document.getElementById("department-data");

    if (!chartContainer || typeof Chart === "undefined") {
        return;
    }

    try {
        const departmentData = JSON.parse(chartContainer.dataset.departments || "[]");

        if (!Array.isArray(departmentData) || departmentData.length === 0) {
            return;
        }

        const departments = departmentData.map(function (item) {
            return item.department_name;
        });

        const resolved = departmentData.map(function (item) {
            return Number(item.resolved_complaints ?? 0);
        });

        const pending = departmentData.map(function (item) {
            return Number(item.pending_complaints ?? 0);
        });

        const inProgress = departmentData.map(function (item) {
            return Number(item.in_progress_complaints ?? 0);
        });

        new Chart(document.getElementById("resolvedChart"), {
            type: "bar",
            data: {
                labels: departments,
                datasets: [
                    {
                        label: "Resolved Complaints",
                        data: resolved,
                        backgroundColor: "#2563eb",
                        borderRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        new Chart(document.getElementById("statusChart"), {
            type: "bar",
            data: {
                labels: departments,
                datasets: [
                    {
                        label: "Resolved",
                        data: resolved,
                        backgroundColor: "#22c55e"
                    },
                    {
                        label: "Pending",
                        data: pending,
                        backgroundColor: "#f59e0b"
                    },
                    {
                        label: "In Progress",
                        data: inProgress,
                        backgroundColor: "#3b82f6"
                    }
                ]
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
    } catch (error) {
        console.error("Analytics chart data failed to load:", error);
    }
});
