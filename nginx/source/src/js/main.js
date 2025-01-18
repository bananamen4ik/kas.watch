import "../scss/styles.scss"
import * as bootstrap from "bootstrap"

document.addEventListener("DOMContentLoaded", async function () {
    await initApp();
});

async function initApp() {
    await listenWS();
}

async function listenWS() {
    try {
        const url = await getWebSocketURL();
        const socket = new WebSocket(url);

        socket.addEventListener("message", async (event) => {
            const transaction = JSON.parse(event.data);
            await addKRC20Transaction({
                idSource: Number(await escapeHTML(transaction["id_source"])),
                ticker: await escapeHTML(transaction["ticker"]),
                krc20Amount: Number(await escapeHTML(transaction["krc20_amount"])),
                kasAmount: Number(await escapeHTML(transaction["kas_amount"])),
                createdAt: Number(await escapeHTML(transaction["created_at"]))
            });
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
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "'": "&apos;",
            "\"": "&quot;"
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
        sourceName = "KSPR Bot";
    }

    transaction.className = "krc20-live__transaction mt-3 p-2 p-md-3";
    transaction.innerHTML = `
        <div class="d-flex justify-content-between mb-1">
            <h5 class="mb-0 text-warning"><span data-copy="">${ticker}</span></h5>
            <small class="text-body-secondary"><a class="krc20-live__link-tooltip" href="#" data-bs-toggle="tooltip" data-bs-placement="left" data-bs-title="Price Per Unit (KAS/KRC20)">PPU</a>: <span data-copy="">${ppu.toFixed(8)}</span></small>
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