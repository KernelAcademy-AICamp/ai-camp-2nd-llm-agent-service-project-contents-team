import React, { useEffect, useState } from 'react';
import './LegalPage.css';

function PrivacyPolicy() {
  const [content, setContent] = useState('');

  useEffect(() => {
    // public/privacy.html 내용을 가져와서 표시
    fetch('/privacy.html')
      .then(res => res.text())
      .then(html => {
        // body 내용만 추출
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const bodyContent = doc.body.innerHTML;
        setContent(bodyContent);
      })
      .catch(err => console.error('Failed to load privacy policy:', err));
  }, []);

  return (
    <div className="legal-page">
      <div
        className="legal-content"
        dangerouslySetInnerHTML={{ __html: content }}
      />
    </div>
  );
}

export default PrivacyPolicy;
