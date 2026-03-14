/**
 * chatbot.js — ARIA Chatbot Frontend Logic
 * ==========================================
 * Handles:
 *  - Toggle open/close of chat window
 *  - Sending messages to /chatbot/ask via fetch()
 *  - Rendering bot + user messages
 *  - Typing indicator animation
 *  - Suggestion chips (quick prompts)
 *  - Enter key support, char count, auto-scroll
 */

document.addEventListener("DOMContentLoaded", () => {

  // ── DOM References ─────────────────────────────────────────────────
  const toggleBtn = document.getElementById("chat-toggle-btn");
  const chatWindow = document.getElementById("chat-window");
  const chatIcon = document.getElementById("chat-icon");
  const chatCloseIcon = document.getElementById("chat-close-icon");
  const chatBadge = document.getElementById("chat-badge");
  const messagesDiv = document.getElementById("chat-messages");
  const inputField = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send-btn");
  const suggestionsDiv = document.getElementById("chat-suggestions");
  const charCount = document.getElementById("chat-char-count");
  const minimizeBtn = document.getElementById("chat-minimize");

  let isOpen = false;
  let isWaiting = false;  // Prevents sending while AI is responding
  let hasOpened = false;  // Tracks if user has opened chat before

  // ── Toggle Chat Window ──────────────────────────────────────────────
  toggleBtn.addEventListener("click", () => {
    isOpen = !isOpen;

    if (isOpen) {
      setTimeout(() => { chatWindow.classList.add("chat-window-open"); }, 10);
      chatWindow.style.display = "flex";
    } else {
      chatWindow.classList.remove("chat-window-open");
      setTimeout(() => { chatWindow.style.display = "none"; }, 500);
    }
    
    chatIcon.style.display = isOpen ? "none" : "flex";
    chatCloseIcon.style.display = isOpen ? "block" : "none";
    chatBadge.style.display = "none";

    if (isOpen && !hasOpened) {
      hasOpened = true;
      sessionStorage.setItem('aria_welcomed', 'true'); // mark as seen
      
      // Immediately hide halos if user opens it
      const halo1 = document.getElementById("aria-halo-1");
      const halo2 = document.getElementById("aria-halo-2");
      if(halo1) halo1.style.display = "none";
      if(halo2) halo2.style.display = "none";

      showWelcomeMessage();
      loadSuggestions();
    }

    if (isOpen) inputField.focus();
  });

  minimizeBtn.addEventListener("click", () => {
    isOpen = false;
    chatWindow.classList.remove("chat-window-open");
    setTimeout(() => { chatWindow.style.display = "none"; }, 500);
    chatIcon.style.display = "flex";
    chatCloseIcon.style.display = "none";
  });

  // ── Welcome Message ─────────────────────────────────────────────────
  function showWelcomeMessage() {
    const greeting = getTimeGreeting();
    addBotMessage(
      `${greeting} 👋 I'm **ARIA**, your personal Academic Advisor!\n\n` +
      `I can help you with:\n` +
      `📊 Attendance & detention risk\n` +
      `📝 Marks & study tips\n` +
      `🕒 Today's timetable\n` +
      `💼 Placement readiness\n` +
      `📋 Grievance status\n\n` +
      `What would you like to know?`
    );
  }

  function getTimeGreeting() {
    const h = new Date().getHours();
    if (h < 12) return "Good morning!";
    if (h < 17) return "Good afternoon!";
    return "Good evening!";
  }

  // ── Load Suggestion Chips ───────────────────────────────────────────
  async function loadSuggestions() {
    try {
      const res = await fetch("/chatbot/suggestions");
      const data = await res.json();

      suggestionsDiv.innerHTML = "";
      data.suggestions.forEach(text => {
        const chip = document.createElement("button");
        chip.className = "whitespace-nowrap bg-white/80 backdrop-blur-sm text-indigo-700 px-4 py-2 mt-1 mb-2 rounded-xl text-xs font-bold cursor-pointer hover:bg-gradient-to-r hover:from-indigo-600 hover:to-purple-600 hover:text-white hover:-translate-y-1 shadow-[0_4px_10px_-2px_rgba(79,70,229,0.2)] hover:shadow-[0_8px_20px_-5px_rgba(79,70,229,0.5)] transition-all duration-300 border border-indigo-100/50";
        chip.textContent = text;
        chip.addEventListener("click", () => {
          inputField.value = text;
          sendMessage();
        });
        suggestionsDiv.appendChild(chip);
      });
    } catch (e) {
      suggestionsDiv.style.display = "none";
    }
  }

  // ── Send Message ────────────────────────────────────────────────────
  async function sendMessage() {
    const message = inputField.value.trim();
    if (!message || isWaiting) return;

    // Show user message
    addUserMessage(message);
    inputField.value = "";
    charCount.textContent = "0 / 500";

    // Hide suggestions after first real message with a fade out
    if (suggestionsDiv.children.length > 0) {
      suggestionsDiv.style.opacity = "0";
      setTimeout(() => { suggestionsDiv.style.display = "none"; }, 300);
    }

    // Show typing indicator
    isWaiting = true;
    sendBtn.disabled = true;
    const typingEl = addTypingIndicator();

    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || document.querySelector('input[name="csrf_token"]')?.value || '';
      const response = await fetch("/chatbot/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ message })
      });

      const data = await response.json();
      removeTypingIndicator(typingEl);

      if (data.status === "unauthorized") {
        addBotMessage("🔒 Please log in to use ARIA.");
      } else {
        addBotMessage(data.reply || "Sorry, I couldn't get a response. Please try again.");
      }

    } catch (err) {
      removeTypingIndicator(typingEl);
      addBotMessage("⚠️ Connection error. Please check your internet and try again.");
    }

    isWaiting = false;
    sendBtn.disabled = false;
    inputField.focus();
  }

  // ── Message Renderers ───────────────────────────────────────────────
  function addUserMessage(text) {
    const el = document.createElement("div");
    el.className = "chat-msg user max-w-[85%] px-5 py-3.5 rounded-[1.25rem] rounded-br-[0.25rem] text-[13px] sm:text-sm font-medium leading-relaxed shadow-[0_5px_15px_-5px_rgba(79,70,229,0.4)] bg-gradient-to-br from-indigo-500 to-indigo-600 text-white self-end animate-msg border border-indigo-400/30";
    el.textContent = text;
    messagesDiv.appendChild(el);
    scrollToBottom();
  }

  function addBotMessage(text) {
    const el = document.createElement("div");
    el.className = "chat-msg bot max-w-[85%] px-5 py-3.5 rounded-[1.25rem] rounded-bl-[0.25rem] text-[13px] sm:text-sm font-medium leading-relaxed shadow-[0_8px_20px_-6px_rgba(0,0,0,0.08)] bg-white text-slate-700 border border-slate-100/80 self-start animate-msg relative";

    // Convert **bold** markdown to <strong> and newlines to <br>
    el.innerHTML = formatBotText(text);

    messagesDiv.appendChild(el);
    scrollToBottom();
  }

  function formatBotText(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")  // **bold**
      .replace(/\*(.*?)\*/g, "<em>$1</em>")               // *italic*
      .replace(/\n/g, "<br>");                             // newlines
  }

  // ── Typing Indicator ────────────────────────────────────────────────
  function addTypingIndicator() {
    const el = document.createElement("div");
    el.className = "chat-msg typing bg-white/80 backdrop-blur-sm self-start px-6 py-4 border border-slate-100/80 shadow-[0_5px_15px_-5px_rgba(0,0,0,0.05)] rounded-3xl rounded-bl-sm flex gap-1 items-center animate-msg";
    el.innerHTML = '<div class="flex items-center gap-1.5"><div class="w-2 h-2 rounded-full typing-dot"></div><div class="w-2 h-2 rounded-full typing-dot"></div><div class="w-2 h-2 rounded-full typing-dot"></div></div>';
    messagesDiv.appendChild(el);
    scrollToBottom();
    return el;
  }

  function removeTypingIndicator(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
  }

  // ── Auto Scroll ──────────────────────────────────────────────────────
  function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  // ── Event Listeners ──────────────────────────────────────────────────
  sendBtn.addEventListener("click", sendMessage);

  inputField.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  inputField.addEventListener("input", () => {
    const len = inputField.value.length;
    charCount.textContent = `${len} / 500`;
    charCount.style.color = len > 450 ? "#f43f5e" : "#94a3b8";
  });

  // ── Show notification badge and pulsing halos only once per session ──────
  if (!sessionStorage.getItem('aria_welcomed')) {
    const halo1 = document.getElementById("aria-halo-1");
    const halo2 = document.getElementById("aria-halo-2");
    
    // Show halos
    if (halo1) halo1.classList.remove("hidden");
    if (halo2) halo2.classList.remove("hidden");

    setTimeout(() => {
      if (!hasOpened) {
        chatBadge.style.display = "flex";
      }
    }, 3000);

    // Hide halos and mark as welcomed after 15 seconds to avoid annoyance
    setTimeout(() => {
      if (halo1) halo1.style.display = "none";
      if (halo2) halo2.style.display = "none";
      sessionStorage.setItem('aria_welcomed', 'true');
    }, 15000);
  }

});
