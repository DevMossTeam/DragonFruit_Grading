function resizeGauge() {
    const box = document.getElementById("gaugeBox");
    const svg = document.getElementById("gaugeSVG");

    let size = box.clientWidth;

    svg.setAttribute("width", size);
    svg.setAttribute("height", size);

    const r = (size / 2) - 20;
    const c = 2 * Math.PI * r;

    const bg = document.getElementById("gBg");
    const fill = document.getElementById("gFill");

    bg.setAttribute("cx", size / 2);
    bg.setAttribute("cy", size / 2);
    bg.setAttribute("r", r);

    fill.setAttribute("cx", size / 2);
    fill.setAttribute("cy", size / 2);
    fill.setAttribute("r", r);
    fill.style.strokeDasharray = c;
    fill.style.strokeDashoffset = c;
}

window.addEventListener("load", resizeGauge);
window.addEventListener("resize", resizeGauge);

// EXAMPLE: update gauge value
function setGauge(value) {
    const fill = document.getElementById("gFill");
    const val = document.getElementById("gValue");

    value = Math.max(0, Math.min(100, value));

    const r = fill.getAttribute("r");
    const c = 2 * Math.PI * r;

    const offset = c - (value / 100) * c;

    fill.style.strokeDashoffset = offset;
    val.textContent = value;
}
