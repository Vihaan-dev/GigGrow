import React from "react";

export default function NoticeList({ items }) {
  if (!items || items.length === 0) {
    return <div className="footer-note">No notices right now.</div>;
  }

  return (
    <div>
      {items.map((notice, index) => (
        <div className={`notice tone-${notice.tone || "neutral"}`} key={`${notice.title}-${index}`}>
          <h4>{notice.title}</h4>
          <p>{notice.detail}</p>
        </div>
      ))}
    </div>
  );
}
