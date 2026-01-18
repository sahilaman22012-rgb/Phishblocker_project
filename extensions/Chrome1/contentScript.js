(async function () {
    try {
        const backendURL = "http://127.0.0.1:5000/api/check-url";

        const payload = {
            url: location.href,
            hostname: location.hostname
        };

        const res = await fetch(backendURL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await res.json();
        // expected:
        // { status, risk_score, prediction, reasons }

        if (result.status === "safe") return;

        const overlay = document.createElement("div");
        overlay.id = "url-warning-overlay";

        const box = document.createElement("div");
        box.id = "url-warning-box";

        let theme = {
            suspicious: {
                icon: "⚠️",
                title: "Suspicious Website",
                color: "#f39c12"
            },
            malicious: {
                icon: "⛔",
                title: "Malicious Website",
                color: "#e74c3c"
            }
        }[result.status];

        box.innerHTML = `
            <div class="warning-header" style="background:${theme.color}">
                <span class="icon">${theme.icon}</span>
                <h2>${theme.title}</h2>
            </div>

            <div class="warning-body">
                <p class="url">${location.hostname}</p>

                <div class="risk-meter">
                    <div class="risk-fill" style="width:${result.risk_score}%; background:${theme.color}"></div>
                </div>
                <small>Risk Score: ${result.risk_score}%</small>

                <p class="desc">
                    Our AI model predicts this website as
                    <b>${result.prediction}</b>.
                </p>

                <div class="actions">
                    <button class="btn danger" id="closeTabBtn">Close Tab</button>
                    <button class="btn safe" id="continueBtn">Continue</button>
                </div>
            </div>
        `;

        overlay.appendChild(box);
        document.body.appendChild(overlay);

        document.getElementById("closeTabBtn").onclick = () => {
            chrome.runtime.sendMessage({ action: "close_tab" });
        };

        document.getElementById("continueBtn").onclick = () => {
            overlay.remove();
        };

    } catch (e) {
        console.error("Extension error:", e);
    }
})();
