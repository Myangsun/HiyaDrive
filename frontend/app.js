const agentSteps = [
  { id: "welcome", label: "Welcome", state: "pending" },
  { id: "intent", label: "Intent", state: "pending" },
  { id: "calendar", label: "Calendar", state: "pending" },
  { id: "search", label: "Search", state: "pending" },
  { id: "selector", label: "Select", state: "pending" },
  { id: "script", label: "Script", state: "pending" },
  { id: "caller", label: "Call", state: "pending" },
  { id: "convo", label: "Chat", state: "pending" },
  { id: "finalize", label: "Finish", state: "pending" },
];

const demoTimeline = [
  {
    status: "Greeting you",
    subtitle: "LLM voice greets and gets ready.",
    agentId: "welcome",
    turns: [
      {
        speaker: "assistant",
        text: "Hey there! I'm HiyaDrive. Ready for a dinner booking?",
      },
    ],
  },
  {
    status: "Understanding the request",
    subtitle: "Matching OpenAI voice confirmation flow.",
    agentId: "intent",
    turns: [
      {
        speaker: "user",
        text: "Need a table for two at an Italian spot tomorrow 7 PM.",
      },
      {
        speaker: "assistant",
        text: "Italian dinner tomorrow at 7 PM for two—sound right?",
      },
      { speaker: "user", text: "Yes please." },
    ],
  },
  {
    status: "Checking your calendar",
    subtitle: "Back-end verifies availability.",
    agentId: "calendar",
    turns: [
      {
        speaker: "assistant",
        text: "You're free then. I'll find a great restaurant.",
      },
    ],
  },
  {
    status: "Finding options",
    subtitle: "Google Places ranked nearby results.",
    agentId: "search",
    turns: [
      {
        speaker: "assistant",
        text: "Bella Notte leads with 4.8 stars nearby. Want it?",
      },
      { speaker: "user", text: "Book Bella Notte." },
    ],
  },
  {
    status: "Calling the restaurant",
    subtitle: "Twilio call script preview, then dial.",
    agentId: "caller",
    turns: [
      {
        speaker: "assistant",
        text: "Calling Bella Notte now and patching the audio to the cabin.",
      },
    ],
  },
  {
    status: "Wrapping up",
    subtitle: "Calendar event dropped in and confirmation spoken.",
    agentId: "finalize",
    turns: [
      {
        speaker: "assistant",
        text: "Reserved for two at 7 PM. Reference BN-2471. Need anything else?",
      },
    ],
  },
];

const el = {
  transcript: document.getElementById("transcript"),
  primaryStatus: document.getElementById("primaryStatus"),
  subtitle: document.getElementById("stageSubtitle"),
  micButton: document.getElementById("micButton"),
  chips: document.getElementById("statusChips"),
  demoBtn: document.getElementById("demoBtn"),
  resetBtn: document.getElementById("resetBtn"),
  typeBtn: document.getElementById("typeBtn"),
  clock: document.getElementById("clock"),
};

let recognition;
let listening = false;
let demoTimers = [];

function renderChips() {
  el.chips.innerHTML = "";
  agentSteps.forEach((step) => {
    const chip = document.createElement("span");
    chip.className = `chip chip--${step.state}`;
    chip.textContent = step.label;
    el.chips.appendChild(chip);
  });
}

function addBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble bubble--${role}`;
  bubble.textContent = text;
  el.transcript.appendChild(bubble);
  el.transcript.scrollTop = el.transcript.scrollHeight;
}

function setPrimaryStatus(text) {
  el.primaryStatus.textContent = text;
}

function setSubtitle(text) {
  el.subtitle.textContent = text;
}

function setAgentState(agentId, state) {
  const target = agentSteps.find((step) => step.id === agentId);
  if (!target) return;
  target.state = state;
  renderChips();
}

function resetAgents() {
  agentSteps.forEach((step) => (step.state = "pending"));
  renderChips();
}

function resetUI() {
  stopDemo();
  resetAgents();
  el.transcript.innerHTML = "";
  setPrimaryStatus('Say “hiya” to begin');
  setSubtitle("Tap once, speak naturally, release to stop.");
  addBubble(
    "assistant",
    "Welcome to HiyaDrive Voice Mode. Tap the mic or run the demo to preview the booking flow."
  );
  setListening(false);
}

function setListening(state) {
  listening = state;
  el.micButton.setAttribute("aria-pressed", String(state));
  if (state) {
    setPrimaryStatus("Listening…");
    setSubtitle("Release when you’re done speaking.");
  } else if (!demoTimers.length) {
    setPrimaryStatus("Ready when you are");
    setSubtitle("Tap the mic to speak or run the scripted demo.");
  }
}

function stopDemo() {
  demoTimers.forEach((timer) => clearTimeout(timer));
  demoTimers = [];
}

function runDemo(index = 0) {
  if (index === 0) {
    stopDemo();
    resetAgents();
    el.transcript.innerHTML = "";
  }

  if (index >= demoTimeline.length) {
    setPrimaryStatus("All set. Want another reservation?");
    setSubtitle("Tap the mic to start a fresh request.");
    return;
  }

  const step = demoTimeline[index];
  setPrimaryStatus(step.status);
  setSubtitle(step.subtitle);
  setAgentState(step.agentId, "active");

  let delay = 0;
  step.turns.forEach((turn) => {
    const timer = setTimeout(() => {
      addBubble(turn.speaker, turn.text);
    }, delay);
    demoTimers.push(timer);
    delay += 1500;
  });

  const wrap = setTimeout(() => {
    setAgentState(step.agentId, "done");
    runDemo(index + 1);
  }, delay + 400);
  demoTimers.push(wrap);
}

function handleUserUtterance(text) {
  if (!text.trim()) return;
  addBubble("user", text);
  setPrimaryStatus("Working on it…");
  setSubtitle("This prototype simulates OpenAI-style voice replies.");

  const next =
    agentSteps.find((step) => step.state === "active") ||
    agentSteps.find((step) => step.state === "pending");

  if (next) {
    setAgentState(next.id, "active");
    const timer = setTimeout(() => {
      addBubble(
        "assistant",
        `Routing through ${next.label} agent and responding in voice.`
      );
      setAgentState(next.id, "done");
      setPrimaryStatus(`${next.label} handled.`);
      setSubtitle("You can keep talking or tap Reset to start fresh.");
    }, 1200);
    demoTimers.push(timer);
  } else {
    addBubble("assistant", "Session complete. Tap reset to start again.");
  }
}

function setupSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    setSubtitle("Browser mic APIs unavailable. Use the Type button instead.");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => setListening(true);
  recognition.onend = () => setListening(false);
  recognition.onerror = (event) => {
    setListening(false);
    addBubble("assistant", `Mic error: ${event.error}. Try typing instead.`);
  };
  recognition.onresult = (event) => {
    const transcript = event.results[0]?.[0]?.transcript || "";
    handleUserUtterance(transcript);
  };
}

function attachEvents() {
  el.micButton.addEventListener("click", () => {
    if (recognition) {
      listening ? recognition.stop() : recognition.start();
    } else {
      const manual = prompt("Mic not supported. Type your request:");
      if (manual) handleUserUtterance(manual);
    }
  });

  el.demoBtn.addEventListener("click", () => runDemo());
  el.resetBtn.addEventListener("click", () => resetUI());
  el.typeBtn.addEventListener("click", () => {
    const text = prompt("What should HiyaDrive handle?");
    if (text) handleUserUtterance(text);
  });
}

function startClock() {
  const tick = () => {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, "0");
    const minutes = now.getMinutes().toString().padStart(2, "0");
    el.clock.textContent = `${hours}:${minutes}`;
  };
  tick();
  setInterval(tick, 15_000);
}

function init() {
  renderChips();
  setupSpeechRecognition();
  attachEvents();
  startClock();
  resetUI();
}

init();
