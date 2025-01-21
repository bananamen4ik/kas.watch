import "../scss/styles.scss"
import * as bootstrap from "bootstrap"

import {
    Chart,
    LineController,
    LineElement,
    PointElement,
    LinearScale,
    TimeScale,
    Tooltip,
    Legend
} from 'chart.js'
import 'chartjs-adapter-date-fns'
import zoomPlugin from 'chartjs-plugin-zoom'

document.addEventListener("DOMContentLoaded", async function () {
    await initApp();
});

async function initApp() {
    Chart.register(
        LineController,
        LineElement,
        PointElement,
        LinearScale,
        TimeScale,
        Tooltip,
        Legend,
        zoomPlugin
    );

    const copyEls = document.querySelectorAll("[data-copy]");
    for (const el of copyEls) {
        await copyEl(el);
    }

    await initKasRatesChart();
    await listenWS();
}

async function initKasRatesChart() {
    const data = {
        datasets: [
            {
                label: "ByBit",
                data: [],
                borderColor: "#2F5BE1",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Kraken",
                data: [],
                borderColor: "#1F1F1F",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Kucoin",
                data: [],
                borderColor: "#00D1A7",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Mexc",
                data: [],
                borderColor: "#0C6EFF",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Coinex",
                data: [],
                borderColor: "#1DCE72",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Gate",
                data: [],
                borderColor: "#0D6EFD",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Digifinex",
                data: [],
                borderColor: "#FF6B6B",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Xeggex",
                data: [],
                borderColor: "#F7A800",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Uphold",
                data: [],
                borderColor: "#00C0D9",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Bitget",
                data: [],
                borderColor: "#3A87F7",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Lbank",
                data: [],
                borderColor: "#FF4C00",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Bydfi",
                data: [],
                borderColor: "#FF5B00",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            },
            {
                label: "Btse",
                data: [],
                borderColor: "#FF3366",
                borderWidth: 0.4,
                pointRadius: 2,
                fill: false
            }
        ]
    };

    const config = {
        type: "line",
        data: data,
        options: {
            animation: false,
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        title: function (tooltipItems) {
                            const timestamp = tooltipItems[0].parsed.x;
                            const date = new Date(timestamp);
                            return date.toISOString().slice(11, 19);
                        },
                        label: function (tooltipItem) {
                            const value = tooltipItem.raw;
                            return tooltipItem.dataset.label + ": $" + value.y.toFixed(5);
                        }
                    }
                },
                legend: {
                    display: false
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: "xy",
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true,
                        },
                        mode: "x"
                    }
                }
            },
            scales: {
                x: {
                    type: "time",
                    time: {
                        unit: "second",
                        displayFormats: {
                            second: "mm:ss",
                        }
                    },
                    ticks: {
                        maxTicksLimit: 12
                    }
                },
                y: {
                    position: "right",
                    beginAtZero: false,
                    ticks: {
                        stepSize: 0.0001
                    }
                }
            }
        }
    };

    kasRatesChart = new Chart(document.getElementById("kasRatesChart").getContext("2d"), config);
}

async function addLastKRC20Transaction(transaction) {
    await addKRC20Transaction({
        idSource: Number(await escapeHTML(transaction["id_source"])),
        ticker: await escapeHTML(transaction["ticker"]),
        krc20Amount: Number(await escapeHTML(transaction["krc20_amount"])),
        kasAmount: Number(await escapeHTML(transaction["kas_amount"])),
        createdAt: Number(await escapeHTML(transaction["created_at"]))
    });
}

async function updateKASRates(rates) {
    for (const rate of rates["data"]) {
        const dataset = kasRatesChart.data.datasets.find(ds => ds.label.toLowerCase() === rate[0]);
        dataset.data.push({
            x: rates["timestamp"],
            y: rate[1]
        });
    }
    const allRates = rates["data"].flatMap(dataset => dataset[1]);
    const minRate = Math.min(...allRates);
    const maxRate = Math.max(...allRates);

    const range = maxRate - minRate;
    const padding = range * 0.05;

    const suggestedMin = minRate - padding;
    const suggestedMax = maxRate + padding;

    kasRatesChart.options.scales.y.suggestedMin = suggestedMin;
    kasRatesChart.options.scales.y.suggestedMax = suggestedMax;

    const totalPoints = kasRatesChart.data.datasets[0].data.length;
    if (totalPoints > 25) {
        kasRatesChart.data.datasets.forEach((dataset) => {
            dataset.data.shift();
        });
    }

    kasRatesChart.update();

    const minRateEl = document.getElementById("kas-live__title-minRate");
    const maxRateEl = document.getElementById("kas-live__title-maxRate");
    minRateEl.innerText = minRate.toFixed(5).toString();
    maxRateEl.innerText = maxRate.toFixed(5).toString();

    for (const rate of rates["data"]) {
        if (rate[1] === null) continue;
        const spanEl = document.getElementById(`kas-live__dropdown-${rate[0]}`);
        spanEl.innerText = "$" + rate[1].toFixed(5);
    }
}

async function listenWS() {
    try {
        const url = await getWebSocketURL();
        const socket = new WebSocket(url);

        socket.addEventListener("message", async (event) => {
            const data = JSON.parse(event.data);
            const dataContent = JSON.parse(data["data"]);

            if (data["method"] === "last_krc20_transaction") {
                await addLastKRC20Transaction(dataContent);
            } else if (data["method"] === "kas-rates") {
                await updateKASRates(dataContent);
            }
        });
    } catch (error) {
        console.error("ERROR WebSocket:", error);
    }
}

async function getWSProtocol() {
    if (window.location.protocol === "https:") {
        return "wss";
    } else {
        return "ws";
    }
}

async function getWebSocketURL() {
    const protocol = await getWSProtocol();

    if (window.location.hostname === "localhost") {
        return `${protocol}://localhost/ws`;
    } else {
        return `${protocol}://kas.watch/ws`;
    }
}

async function escapeHTML(str) {
    str = String(str);
    return str.replace(/[&<>'"]/g, function (char) {
        return {
            "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&apos;", "\"": "&quot;"
        }[char];
    });
}

async function tooltipEl(el) {
    new bootstrap.Tooltip(el);
}

async function copyEl(el) {
    el.addEventListener("click", function () {
        const textToCopy = this.innerText;

        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                bootstrap.Toast.getOrCreateInstance(document.getElementById("toastCopy")).show()
            });
    });
}

async function addKRC20Transaction({idSource, ticker, krc20Amount, kasAmount, createdAt}) {
    const transactionsContainer = document.getElementById("krc20Transactions");
    const transaction = document.createElement("div");
    const ppu = kasAmount / krc20Amount;
    let sourceName = "";

    const date = new Date(createdAt);
    const hours = String(date.getUTCHours()).padStart(2, "0");
    const minutes = String(date.getUTCMinutes()).padStart(2, "0");
    const seconds = String(date.getUTCSeconds()).padStart(2, "0");
    const time = `${hours}:${minutes}:${seconds}`;

    if (idSource === 1) {
        sourceName = "<a href=\"https://t.me/kspr_home_bot?start=AXGfUlw\" target=\"_blank\">KSPR Bot</a>";
    }

    transaction.className = "krc20-live__transaction mt-3 p-2 p-md-3";
    transaction.innerHTML = `
        <div class="d-flex justify-content-between mb-1">
            <h5 class="mb-0 text-warning"><span data-copy="">${ticker}</span></h5>
            <small class="text-body-secondary"><a class="krc20-live__link-tooltip" data-bs-toggle="tooltip" data-bs-placement="left" data-bs-title="Price Per Unit (KAS/KRC20)">PPU</a>: <span data-copy="">${ppu.toFixed(8)}</span></small>
        </div>
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <p class="mb-0">KRC20: <strong><span data-copy="">${krc20Amount.toLocaleString()}</span></strong></p>
                <p class="mb-0">KAS: <strong><span data-copy="">${kasAmount.toLocaleString()}</span></strong></p>
            </div>
            <div class="text-end">
                <p class="mb-0"><small class="text-body-secondary">${sourceName}</small></p>
                <p class="mb-0"><small class="text-body-secondary"><span>${time}</span> UTC</small></p>
            </div>
        </div>
    `;

    transactionsContainer.prepend(transaction);

    transaction.classList.add("krc20-live__transaction_highlight");
    setTimeout(() => transaction.classList.remove("krc20-live__transaction_highlight"), 2000);
    await tooltipEl(transaction.querySelector(".krc20-live__link-tooltip"));

    const copyEls = transaction.querySelectorAll("[data-copy]");
    for (const el of copyEls) {
        await copyEl(el);
    }
}

let kasRatesChart;