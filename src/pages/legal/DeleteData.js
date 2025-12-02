import React, { useEffect, useState } from 'react';
import './LegalPage.css';

function DeleteData() {
  const [content, setContent] = useState('');

  useEffect(() => {
    // public/delete-data.html 내용을 가져와서 표시
    fetch('/delete-data.html')
      .then(res => res.text())
      .then(html => {
        // body 내용만 추출
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const bodyContent = doc.body.innerHTML;
        setContent(bodyContent);
      })
      .catch(err => console.error('Failed to load delete data page:', err));
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

export default DeleteData;
