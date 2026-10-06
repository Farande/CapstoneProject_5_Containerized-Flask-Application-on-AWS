document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        if (!alert.classList.contains("alert-info") && !alert.classList.contains("alert-success") && !alert.classList.contains("alert-danger") && !alert.classList.contains("alert-warning")) {
            return;
        }

        setTimeout(function () {
            alert.classList.add("fade-out");
            setTimeout(function () {
                alert.remove();
            }, 300);
        }, 4000);
    });

    const navbarButtons = document.querySelectorAll(".btn");
    navbarButtons.forEach(function (button) {
        button.addEventListener("mouseenter", function () {
            button.style.transform = "translateY(-1px)";
        });

        button.addEventListener("mouseleave", function () {
            button.style.transform = "";
        });
    });
});
