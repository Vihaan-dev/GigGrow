import React, { useEffect, useRef, useState } from "react";
import { api } from "../api";

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
  english: ["How much did I earn yesterday?", "Can I afford a 22000 bike?", "Why is my fuel spend high?"],
  hindi: ["कल कितना कमाया?", "बाइक 22000 की ले सकता हूं?", "पेट्रोल खर्च ज्यादा क्यों है?"],
  kannada: ["ನಿನ್ನೆ ಎಷ್ಟು ಗಳಿಸಿದೆ?", "22000 ರೂ ಬೈಕ್ ಖರೀದಿಸಬಹುದೇ?", "ಪೆಟ್ರೋಲ್ ಖರ್ಚು ಯಾಕೆ ಜಾಸ್ತಿ?"]
};

export default function ChatPanel({ userId, defaultLanguage = "hindi" }) {
  const [message, setMessage] = useState("");
  const [language, setLanguage] = useState(defaultLanguage);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState("");
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
    rec.onerror = (event) => {
      setStatus(`Voice error: ${event.error}`);
    };
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
    if (!userId || !message.trim()) return;
    setStatus("");

    const userMessage = { role: "user", content: message };
    setHistory((prev) => [...prev, userMessage]);
    setMessage("");

    try {
      const response = await api.chat({
        user_id: userId,
        message: userMessage.content,
        language
      });
      setHistory((prev) => [...prev, { role: "assistant", content: response.response }]);
    } catch (err) {
      setStatus(err.message || "Failed to chat.");
    }
  };

  const handleSuggest = (text) => setMessage(text);

  return (
    <div className="form chat-form">
      <div className="form-row">
        <select value={language} onChange={(event) => setLanguage(event.target.value)}>
          <option value="english">English</option>
          <option value="hindi">हिंदी (Hindi)</option>
          <option value="kannada">ಕನ್ನಡ (Kannada)</option>
        </select>
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
            {item.content}
          </div>
        ))}
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
        <button type="submit" disabled={!message.trim()}>
          Send
        </button>
      </form>

      {!voiceSupported && (
        <div className="footer-note">
          Voice input needs Chrome/Edge; the rest works everywhere.
        </div>
      )}
      {status && <div className="footer-note">{status}</div>}
    </div>
  );
}
