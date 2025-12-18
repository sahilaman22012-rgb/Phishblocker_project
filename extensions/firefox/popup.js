// PhishBlocker Popup Script for Firefox

const browser = window.browser || window.chrome // Declare the browser variable

document.addEventListener("DOMContentLoaded", async () => {
  // Get current tab
  const tabs = await browser.tabs.query({ active: true, currentWindow: true })
  const tab = tabs[0]

  if (tab && tab.url) {
    document.getElementById("currentUrl").textContent = tab.url
    checkCurrentURL(tab.url)
  } else {
    document.getElementById("currentUrl").textContent = "Unable to access current page"
    document.getElementById("status").innerHTML = "<span>❌</span><span>No URL</span>"
  }

  loadStats()

  document.getElementById("checkAgain").addEventListener("click", () => {
    if (tab && tab.url) {
      checkCurrentURL(tab.url)
    }
  })

  document.getElementById("openDashboard").addEventListener("click", () => {
    browser.tabs.create({ url: "http://localhost:3000" })
  })
})

async function checkCurrentURL(url) {
  const statusEl = document.getElementById("status")
  statusEl.className = "status checking"
  statusEl.innerHTML = '<span class="loading">⏳</span><span>Checking...</span>'

  try {
    const response = await browser.runtime.sendMessage({
      action: "checkURL",
      url: url,
    })

    if (response && !response.error) {
      if (response.prediction === "phishing") {
        statusEl.className = "status danger"
        statusEl.innerHTML = `<span>🚨</span><span>Phishing Detected! (${response.risk_score}%)</span>`
      } else {
        statusEl.className = "status safe"
        statusEl.innerHTML = "<span>✅</span><span>Safe Website</span>"
      }

      setTimeout(loadStats, 500)
    } else {
      statusEl.className = "status"
      statusEl.innerHTML = "<span>⚠️</span><span>Check Failed</span>"
    }
  } catch (error) {
    console.error("Error checking URL:", error)
    statusEl.className = "status"
    statusEl.innerHTML = "<span>❌</span><span>Error</span>"
  }
}

async function loadStats() {
  try {
    const stats = await browser.runtime.sendMessage({ action: "getStats" })

    if (stats) {
      document.getElementById("totalChecked").textContent = stats.totalChecked || 0
      document.getElementById("phishingBlocked").textContent = stats.phishingBlocked || 0
    }
  } catch (error) {
    console.error("Error loading stats:", error)
  }
}
