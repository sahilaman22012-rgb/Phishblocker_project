// PhishBlocker Content Script
console.log("PhishBlocker content script loaded")

// Declare the chrome variable to fix lint/correctness/noUndeclaredVariables error
const chrome = window.chrome

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "showWarning") {
    showPhishingWarning(request.result)
  }
})

// Show phishing warning overlay
function showPhishingWarning(result) {
  // Check if warning already exists
  if (document.getElementById("phishblocker-warning")) {
    return
  }

  const overlay = document.createElement("div")
  overlay.id = "phishblocker-warning"
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.95);
    z-index: 999999;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `

  const warningBox = document.createElement("div")
  warningBox.style.cssText = `
    background: white;
    padding: 40px;
    border-radius: 12px;
    max-width: 600px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  `

  const icon = document.createElement("div")
  icon.textContent = "⚠️"
  icon.style.cssText = `
    font-size: 64px;
    margin-bottom: 20px;
  `

  const title = document.createElement("h1")
  title.textContent = "Phishing Website Detected!"
  title.style.cssText = `
    color: #DC2626;
    font-size: 32px;
    margin: 0 0 16px 0;
    font-weight: 700;
  `

  const description = document.createElement("p")
  description.textContent = "Our AI has detected that this website may be attempting to steal your information."
  description.style.cssText = `
    color: #374151;
    font-size: 18px;
    margin: 0 0 24px 0;
    line-height: 1.6;
  `

  const riskScore = document.createElement("div")
  riskScore.textContent = `Risk Score: ${result.risk_score}%`
  riskScore.style.cssText = `
    background: #FEE2E2;
    color: #DC2626;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 20px;
    margin-bottom: 20px;
    display: inline-block;
  `

  const reasons = document.createElement("div")
  reasons.style.cssText = `
    text-align: left;
    background: #F3F4F6;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
    max-height: 200px;
    overflow-y: auto;
  `

  const reasonsTitle = document.createElement("strong")
  reasonsTitle.textContent = "Reasons:"
  reasonsTitle.style.cssText = `
    display: block;
    margin-bottom: 12px;
    color: #1F2937;
  `
  reasons.appendChild(reasonsTitle)

  const reasonsList = document.createElement("ul")
  reasonsList.style.cssText = `
    margin: 0;
    padding-left: 20px;
    color: #4B5563;
  `

  result.reasons.forEach((reason) => {
    const li = document.createElement("li")
    li.textContent = reason
    li.style.marginBottom = "8px"
    reasonsList.appendChild(li)
  })
  reasons.appendChild(reasonsList)

  const buttonContainer = document.createElement("div")
  buttonContainer.style.cssText = `
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 24px;
  `

  const backButton = document.createElement("button")
  backButton.textContent = "Go Back to Safety"
  backButton.style.cssText = `
    background: #DC2626;
    color: white;
    border: none;
    padding: 14px 28px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  `
  backButton.onmouseover = () => (backButton.style.background = "#B91C1C")
  backButton.onmouseout = () => (backButton.style.background = "#DC2626")
  backButton.onclick = () => window.history.back()

  const proceedButton = document.createElement("button")
  proceedButton.textContent = "Proceed Anyway (Not Recommended)"
  proceedButton.style.cssText = `
    background: transparent;
    color: #6B7280;
    border: 2px solid #D1D5DB;
    padding: 14px 28px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  `
  proceedButton.onmouseover = () => {
    proceedButton.style.borderColor = "#9CA3AF"
    proceedButton.style.color = "#374151"
  }
  proceedButton.onmouseout = () => {
    proceedButton.style.borderColor = "#D1D5DB"
    proceedButton.style.color = "#6B7280"
  }
  proceedButton.onclick = () => overlay.remove()

  buttonContainer.appendChild(backButton)
  buttonContainer.appendChild(proceedButton)

  warningBox.appendChild(icon)
  warningBox.appendChild(title)
  warningBox.appendChild(description)
  warningBox.appendChild(riskScore)
  warningBox.appendChild(reasons)
  warningBox.appendChild(buttonContainer)

  overlay.appendChild(warningBox)
  document.body.appendChild(overlay)
}
