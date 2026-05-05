import React, { useState } from "react";
import { api } from "../api";

export default function ChatPanel({ userId }) {
  const [message, setMessage] = useState("");
  const [language, setLanguage] = useState("hindi");
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState("");

  const send = async (event) => {
    event.preventDefault();
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

  return (
    <div className="form">
      <div className="form-row">
        <select value={language} onChange={(event) => setLanguage(event.target.value)}>
          <option value="english">English</option>
          <option value="hindi">Hindi</option>
          <option value="kannada">Kannada</option>
        </select>
      </div>
      <div className="chat-window">
        {history.length === 0 && <div className="footer-note">No messages yet.</div>}
        {history.map((item, index) => (
          <div
            key={`${item.role}-${index}`}
            className={`chat-bubble ${item.role === "user" ? "user" : ""}`}
          >
            {item.content}
          </div>
        ))}
      </div>
      <form onSubmit={send} className="form">
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask a question"
        />
        <button type="submit">Send</button>
      </form>
      {status && <div className="footer-note">{status}</div>}
    </div>
  );
}
