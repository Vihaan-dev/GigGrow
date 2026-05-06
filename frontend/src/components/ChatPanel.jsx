import React, { useEffect, useRef, useState } from "react";
import { api } from "../api";
import LlmStatusBadge from "./LlmStatusBadge";

const SPEECH_LANG = {
  english: "en-IN",
  hindi: "hi-IN",
  kannada: "kn-IN"
};

const PLACEHOLDER = {
  english: "Ask anything — earnings, spending, schemes…",
  hindi: "हिंदी में पूछें — कमाई, खर्च, योजना…",
  kannada: "ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ — ಆದಾಯ, ಖರ್ಚು, ಯೋಜನೆ…"
};

const SUGGESTIONS = {
  english: [
    "How much did I earn last week?",
    "Can I afford a 22000 bike?",
    "Why is my spend high?",
    "What schemes do I qualify for?"
  ],
  hindi: [
    "पिछले हफ्ते कितना कमाया?",
    "बाइक 22000 की ले सकता हूं?",
    "मेरा खर्च ज्यादा क्यों है?",
    "मैं किन योजनाओं के लिए योग्य हूं?"
  ],
  kannada: [
    "ಕಳೆದ ವಾರ ಎಷ್ಟು ಗಳಿಸಿದೆ?",
    "22000 ರೂ ಬೈಕ್ ಖರೀದಿಸಬಹುದೇ?",
    "ಖರ್ಚು ಯಾಕೆ ಜಾಸ್ತಿ?",
    "ಯಾವ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹನಾಗಿದ್ದೇನೆ?"
  ]
};

function ToolChip({ call }) {
  const argsStr = Object.entries(call.args || {})
    .map(([k, v]) => `${k}: ${typeof v === "string" ? `"${v}"` : v}`)
    .join(", ");
  return (
    <div className="tool-chip">
      <span className="tool-chip-icon">🔧</span>
      <code>{call.name}({argsStr})</code>
    </div>
  );
}

export default function ChatPanel({ userId, defaultLanguage = "hindi" }) {
  const [message, setMessage] = useState("");
  const [language, setLanguage] = useState(defaultLanguage);
  const [history, setHistory] = useState([]);  // [{role, content, toolCalls?, sources?}]
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const recognitionRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    setVoiceSupported(Boolean(SR));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history]);

  const startListening = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const rec = new SR();
    rec.lang = SPEECH_LANG[language] || "en-IN";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript || "";
      setMessage((prev) => (prev ? `${prev} ${transcript}` : transcript));
    };
    rec.onerror = (event) => setStatus(`Voice error: ${event.error}`);
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    rec.start();
    setListening(true);
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setListening(false);
  };

  const send = async (event) => {
    event?.preventDefault();
    if (!userId || !message.trim() || loading) return;
    setStatus("");
    setLoading(true);

    const userMessage = { role: "user", content: message };
    setHistory((prev) => [...prev, userMessage]);
    setMessage("");

    try {
      const r = await api.chat({
        user_id: userId,
        message: userMessage.content,
        language
      });
      setHistory((prev) => [...prev, {
        role: "assistant",
        content: r.answer || r.response,
        toolCalls: r.tool_calls || [],
        rationale: r.rationale,
        selectionSource: r.selection_source,
        answerSource: r.answer_source
      }]);
    } catch (err) {
      setStatus(err.message || "Failed to chat.");
    } finally {
      setLoading(false);
    }
  };

  const handleSuggest = (text) => setMessage(text);

  return (
    <div className="form chat-form">
      <div className="chat-header-row">
        <select value={language} onChange={(event) => setLanguage(event.target.value)}>
          <option value="english">English</option>
          <option value="hindi">हिंदी (Hindi)</option>
          <option value="kannada">ಕನ್ನಡ (Kannada)</option>
        </select>
        <LlmStatusBadge />
      </div>

      <div className="suggest-row">
        {(SUGGESTIONS[language] || []).map((s) => (
          <button key={s} type="button" className="ghost suggest" onClick={() => handleSuggest(s)}>
            {s}
          </button>
        ))}
      </div>

      <div className="chat-window" ref={scrollRef}>
        {history.length === 0 && <div className="footer-note">No messages yet.</div>}
        {history.map((item, index) => (
          <div
            key={`${item.role}-${index}`}
            className={`chat-bubble ${item.role === "user" ? "user" : "assistant"}`}
          >
            {item.role === "assistant" && item.toolCalls && item.toolCalls.length > 0 && (
              <div className="tool-trace">
                <div className="tool-trace-head">
                  <span className="briefing-tag">tool calls</span>
                  <span className="footer-note">
                    {item.selectionSource === "gemini" ? "selected by Gemini" : "selected by heuristic"}
                  </span>
                </div>
                <div className="tool-chips">
                  {item.toolCalls.map((c, i) => (
                    <ToolChip key={i} call={c} />
                  ))}
                </div>
                {item.rationale && (
                  <p className="footer-note">{item.rationale}</p>
                )}
              </div>
            )}
            <div className="chat-bubble-text">{item.content}</div>
          </div>
        ))}
        {loading && <div className="footer-note">selecting tools, fetching data…</div>}
      </div>

      <form onSubmit={send} className="form-row chat-input-row">
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder={PLACEHOLDER[language] || PLACEHOLDER.english}
        />
        {voiceSupported && (
          <button
            type="button"
            className={listening ? "secondary" : "ghost"}
            onClick={listening ? stopListening : startListening}
            title="Voice input"
          >
            {listening ? "● recording" : "🎤 speak"}
          </button>
        )}
        <button type="submit" disabled={!message.trim() || loading}>
          Send
        </button>
      </form>

      {!voiceSupported && (
        <div className="footer-note">
          Voice input needs Chrome/Edge; the rest works everywhere.
        </div>
      )}
      {status && <div className="footer-note">{status}</div>}

      <div className="footer-note">
        Each chat answer goes through a 2-pass tool-use loop: the model selects which
        backend tools to call, the backend runs them on real data, then the model
        composes the final answer. Tool selections are visible above so you can see
        what data informed the response.
      </div>
    </div>
  );
}
