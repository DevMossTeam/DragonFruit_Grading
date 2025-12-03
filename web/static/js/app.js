function updateGauge(grade) {
    const gauge = document.querySelector(".gauge-progress");
    const gradeText = document.getElementById("gauge-grade");

    let percent = 0;

    if (grade === "A") percent = 100;
    else if (grade === "B") percent = 70;
    else if (grade === "C") percent = 40;
    else percent = 0;

    const maxDash = 565; // untuk r=90
    const offset = maxDash - (maxDash * percent / 100);

    gauge.style.strokeDashoffset = offset;
    gradeText.textContent = grade;
}

// // Tombol test
// document.getElementById("testA").addEventListener("click", () => {
//     updateGauge("A");
// });
