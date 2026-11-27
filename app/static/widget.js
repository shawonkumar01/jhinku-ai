/*
 * Jhinku AI Chat Widget
 *
 * Usage:
 *   <script src="https://YOUR_API_DOMAIN/widget.js"
 *           data-chatbot-id="PUBLIC_WIDGET_ID" async></script>
 *
 * The widget talks only to the public chat API. No secrets are
 * exposed — domain allowlisting and rate limits are enforced
 * server-side.
 */
(function () {
  "use strict";

  // ---------- Bootstrap ----------
  // document.currentScript is null for dynamically-inserted scripts
  // (e.g. loaded via createElement), so fall back to scanning for
  // our own <script> tag.
  var scriptEl = document.currentScript;
  if (!scriptEl) {
    var scripts = document.getElementsByTagName("script");
    for (var i = scripts.length - 1; i >= 0; i--) {
      if (scripts[i].src && scripts[i].src.indexOf("widget.js") !== -1) {
        scriptEl = scripts[i];
        break;
      }
    }
  }
  if (!scriptEl) return;
  var chatbotId = scriptEl.getAttribute("data-chatbot-id");
  if (!chatbotId) {
    console.error("[Jhinku] Missing data-chatbot-id attribute");
    return;
  }

  // API base = origin of this script's src.
  var apiBase = new URL(scriptEl.src).origin + "/api/v1";

  // ---------- Customer identity (per browser, per chatbot) ----------
  var storageKey = "jhinku_cid_" + chatbotId;
  var customerId = localStorage.getItem(storageKey);
  if (!customerId) {
    customerId =
      (window.crypto && crypto.randomUUID && crypto.randomUUID()) ||
      "v-" + Date.now().toString(36) + Math.random().toString(36).slice(2);
    localStorage.setItem(storageKey, customerId);
  }

  var state = {
    config: null,
    conversationId: null,
    open: false,
  };

  // ---------- DOM ----------
  var primaryColor = "#4f46e5";

  var launcher = document.createElement("button");
  launcher.id = "jhinku-launcher";
  launcher.setAttribute("aria-label", "Open chat");
  launcher.innerHTML =
    '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
  launcher.style.cssText =
    "position:fixed;bottom:20px;right:20px;width:56px;height:56px;" +
    "border-radius:50%;border:none;cursor:pointer;color:#fff;" +
    "background:" + primaryColor + ";box-shadow:0 4px 12px rgba(0,0,0,.25);" +
    "z-index:2147483000;display:flex;align-items:center;justify-content:center;";

  var panel = document.createElement("div");
  panel.id = "jhinku-panel";
  panel.style.cssText =
    "position:fixed;bottom:88px;right:20px;width:360px;max-width:calc(100vw - 40px);" +
    "height:520px;max-height:calc(100vh - 120px);background:#fff;" +
    "border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.2);" +
    "display:none;flex-direction:column;overflow:hidden;z-index:2147483000;" +
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;";

  panel.innerHTML =
    '<div id="jhinku-header" style="padding:14px 16px;color:#fff;' +
    "background:" + primaryColor + ';font-weight:600;font-size:15px;">Chat</div>' +
    '<div id="jhinku-messages" style="flex:1;overflow-y:auto;padding:12px;' +
    'display:flex;flex-direction:column;gap:8px;background:#f8f9fa;"></div>' +
    '<div id="jhinku-typing" style="display:none;padding:0 16px 4px;' +
    'font-size:12px;color:#888;">Assistant is typing…</div>' +
    '<form id="jhinku-form" style="display:flex;gap:8px;padding:10px;' +
    'border-top:1px solid #eee;background:#fff;">' +
    '<input id="jhinku-input" type="text" placeholder="Type a message…" ' +
    'autocomplete="off" style="flex:1;border:1px solid #ddd;border-radius:20px;' +
    'padding:9px 14px;font-size:14px;outline:none;">' +
    '<button type="submit" style="border:none;border-radius:20px;padding:9px 16px;' +
    "color:#fff;background:" + primaryColor + ';font-size:14px;cursor:pointer;">Send</button>' +
    "</form>";

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  var messagesEl = panel.querySelector("#jhinku-messages");
  var formEl = panel.querySelector("#jhinku-form");
  var inputEl = panel.querySelector("#jhinku-input");
  var typingEl = panel.querySelector("#jhinku-typing");
  var headerEl = panel.querySelector("#jhinku-header");

  // ---------- Helpers ----------
  function api(path, options) {
    options = options || {};
    options.headers = Object.assign(
      { "Content-Type": "application/json" },
      options.headers
    );
    return fetch(apiBase + path, options).then(function (res) {
      if (!res.ok) {
        return res.json().then(function (body) {
          throw new Error(body.detail || "Request failed (" + res.status + ")");
        });
      }
      return res.status === 204 ? null : res.json();
    });
  }

  function bubble(text, who) {
    var div = document.createElement("div");
    var isCustomer = who === "customer";
    div.style.cssText =
      "max-width:80%;padding:9px 13px;border-radius:14px;font-size:14px;" +
      "line-height:1.4;white-space:pre-wrap;word-wrap:break-word;" +
      (isCustomer
        ? "align-self:flex-end;background:" + primaryColor + ";color:#fff;"
        : "align-self:flex-start;background:#fff;color:#222;" +
          "border:1px solid #eee;");
    div.textContent = text; // textContent = XSS-safe
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function bubbleTyping() {
    typingEl.style.display = "block";
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
  function hideTyping() {
    typingEl.style.display = "none";
  }

  function errorBubble() {
    var div = document.createElement("div");
    div.style.cssText =
      "align-self:center;font-size:12px;color:#c00;padding:4px;";
    div.textContent = "Sorry, something went wrong. Please try again.";
    messagesEl.appendChild(div);
  }

  // ---------- Conversation lifecycle ----------
  function ensureConversation() {
    if (state.conversationId) return Promise.resolve();
    return api("/public/chatbots/" + chatbotId + "/conversations", {
      method: "POST",
      body: JSON.stringify({ customer_identifier: customerId }),
    }).then(function (data) {
      state.conversationId = data.public_id;
      if (data.welcome_message) bubble(data.welcome_message, "ai");
    });
  }

  function loadHistory() {
    api(
      "/public/conversations/" + state.conversationId +
        "/messages?customer_identifier=" + encodeURIComponent(customerId)
    ).then(function (msgs) {
      messagesEl.innerHTML = "";
      msgs.forEach(function (m) {
        bubble(m.content, m.sender_type === "customer" ? "customer" : "ai");
      });
      if (!msgs.length && state.config && state.config.welcome_message) {
        bubble(state.config.welcome_message, "ai");
      }
    }).catch(function () {});
  }

  function openPanel() {
    if (state.open) return;
    state.open = true;
    panel.style.display = "flex";
    launcher.style.display = "none";
    ensureConversation()
      .then(function () {
        if (state.conversationId) loadHistory();
      })
      .catch(errorBubble);
    inputEl.focus();
  }

  function closePanel() {
    state.open = false;
    panel.style.display = "none";
    launcher.style.display = "flex";
  }

  // ---------- Send message ----------
  function send(text) {
    text = (text || "").trim();
    if (!text || !state.conversationId) return;

    bubble(text, "customer");
    inputEl.value = "";
    bubbleTyping();

    api("/public/conversations/" + state.conversationId + "/messages", {
      method: "POST",
      body: JSON.stringify({
        content: text,
        customer_identifier: customerId,
      }),
    })
      .then(function (msg) {
        hideTyping();
        bubble(msg.content, "ai");
      })
      .catch(function () {
        hideTyping();
        errorBubble();
      });
  }

  // ---------- Events ----------
  launcher.addEventListener("click", openPanel);

  formEl.addEventListener("submit", function (e) {
    e.preventDefault();
    send(inputEl.value);
  });

  // Esc closes the panel.
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && state.open) closePanel();
  });

  // ---------- Init: fetch public config ----------
  api("/public/chatbots/" + chatbotId)
    .then(function (config) {
      state.config = config;
      if (config.branding && config.branding.primary_color) {
        primaryColor = config.branding.primary_color;
        launcher.style.background = primaryColor;
        headerEl.style.background = primaryColor;
        panel.querySelector("#jhinku-form button").style.background =
          primaryColor;
      }
      if (config.name) headerEl.textContent = config.name;
      if (config.welcome_message) {
        // Shown on first open if no history exists.
      }
    })
    .catch(function () {
      headerEl.textContent = "Chat unavailable";
    });
})();
