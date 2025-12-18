// PhishBlocker Background Service Worker
const API_URL = "http://localhost:5000/api/check-url"
const chrome = window.chrome // Declare the chrome variable

// Cache for checked URLs (expires after 1 hour)
const urlCache = new Map()
const CACHE_DURATION = 60 * 60 * 1000 // 1 hour

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "loading" && tab.url) {
    checkURL(tab.url, tabId)
  }
})

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "checkURL") {
    checkURL(request.url, sender.tab?.id).then(sendResponse)
    return true // Keep channel open for async response
  }

  if (request.action === "getStats") {
    getStats().then(sendResponse)
    return true
  }
})

// Check URL against API
async function checkURL(url, tabId) {
  try {
    // Skip chrome:// and extension:// URLs
    if (
      url.startsWith("chrome://") ||
      url.startsWith("chrome-extension://") ||
      url.startsWith("about:") ||
      url.startsWith("edge://") ||
      url.startsWith("brave://")
    ) {
      return null
    }

    // Check cache first
    const cached = urlCache.get(url)
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      console.log("Using cached result for:", url)
      handleResult(cached.result, tabId)
      return cached.result
    }

    console.log("Checking URL:", url)

    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    })

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`)
    }

    const result = await response.json()
    result.timestamp = new Date().toISOString()

    // Cache the result
    urlCache.set(url, {
      result,
      timestamp: Date.now(),
    })

    // Store in storage for stats
    await updateStats(result)

    // Handle the result (show warning if phishing)
    handleResult(result, tabId)

    return result
  } catch (error) {
    console.error("Error checking URL:", error)
    return {
      error: error.message,
      url: url,
    }
  }
}

// Handle check result
function handleResult(result, tabId) {
  if (!result || result.error) return

  // Update badge
  if (result.prediction === "phishing") {
    chrome.action.setBadgeBackgroundColor({ color: "#DC2626", tabId })
    chrome.action.setBadgeText({ text: "⚠️", tabId })

    // Show notification
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icons/icon128.png",
      title: "🚨 Phishing Website Detected!",
      message: `This website may be dangerous. Risk score: ${result.risk_score}%`,
      priority: 2,
    })

    // Send message to content script to show warning
    if (tabId) {
      chrome.tabs
        .sendMessage(tabId, {
          action: "showWarning",
          result: result,
        })
        .catch((err) => console.log("Could not send message to content script:", err))
    }
  } else {
    chrome.action.setBadgeBackgroundColor({ color: "#10B981", tabId })
    chrome.action.setBadgeText({ text: "✓", tabId })
  }
}

// Update statistics
async function updateStats(result) {
  const stats = await chrome.storage.local.get(["stats"])
  const currentStats = stats.stats || {
    totalChecked: 0,
    phishingBlocked: 0,
    safeSites: 0,
    lastCheck: null,
  }

  currentStats.totalChecked++
  if (result.prediction === "phishing") {
    currentStats.phishingBlocked++
  } else {
    currentStats.safeSites++
  }
  currentStats.lastCheck = result.timestamp

  await chrome.storage.local.set({ stats: currentStats })
}

// Get statistics
async function getStats() {
  const stats = await chrome.storage.local.get(["stats"])
  return (
    stats.stats || {
      totalChecked: 0,
      phishingBlocked: 0,
      safeSites: 0,
      lastCheck: null,
    }
  )
}

console.log("PhishBlocker background service worker loaded")
