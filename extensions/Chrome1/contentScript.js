(async function () {
    try {
        const urlObj = new URL(window.location.href);

        const data = {
            url: urlObj.href,
            hostname: urlObj.hostname,
            port: urlObj.port || (urlObj.protocol === "https:" ? "443" : "80")
        };

        // Your backend URL:
        const backendURL = "http://127.0.0.1:5000/api/check-url";

        const res = await fetch(backendURL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        // expected: { status: "safe" | "suspicious" | "malicious" }

        if (result.status === "safe") {
            return; // No popup
        }

        // Create overlay
        const overlay = document.createElement("div");
        overlay.id = "url-warning-overlay";

        const box = document.createElement("div");
        box.id = "url-warning-box";

        let title = "";
        let text = "";
        let color = "";

        if (result.status === "suspicious") {
            title = "⚠️ Suspicious Website";
            text = "Proceed with caution. This website seems suspicious.";
            color = "orange";
        } else {
            title = "⛔ Malicious Website!";
            text = "This website is marked as malicious. It may harm your system.";
            color = "red";
        }

        box.innerHTML = `
            <h2 style="color:${color};">${title}</h2>
            <p>${text}</p>

            <button class="warning-btn close-btn" id="closeTabBtn">
                Close This Tab
            </button>

            <button class="warning-btn continue-btn" id="continueBtn">
                Continue Browsing
            </button>
        `;

        overlay.appendChild(box);
        document.body.appendChild(overlay);

        // Button Actions
        document.getElementById("closeTabBtn").onclick = () => {
            chrome.runtime.sendMessage({ action: "close_tab" });
        };

        document.getElementById("continueBtn").onclick = () => {
            overlay.remove();
        };

    } catch (err) {
        console.error("Error in content script:", err);
    }
})();