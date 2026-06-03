window.dash_clientside = Object.assign({}, window.dash_clientside, {
    purchasing_dashboard: {
        toggle_save_message_visibility: function(message) {
            const el = document.getElementById("save-itemset-result-message");
            success = message && message.includes("Itemset saved successfully");
            el.classList.toggle("success", success);
            el.classList.toggle("failure", !success);
            if (success) timeout = 1000; else timeout = 3000;
            if (message && el) {
                el.classList.remove("hide-opacity"); // reset visibility
                // Force reflow to restart the transition
                void el.offsetWidth;
                setTimeout(() => {
                    el.classList.add("hide-opacity"); // trigger fade-out
                }, timeout);
            }
            return Array.from(el.classList).join(" ");
        }
    }
});