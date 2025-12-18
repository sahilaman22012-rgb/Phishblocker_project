chrome.runtime.onMessage.addListener((msg, sender) => {
    if (msg.action === "close_tab" && sender.tab?.id) {
        chrome.tabs.remove(sender.tab.id);
    }
});