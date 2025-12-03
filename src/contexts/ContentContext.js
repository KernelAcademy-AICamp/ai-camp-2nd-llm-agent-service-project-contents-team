import React, { createContext, useContext, useState } from 'react';

const ContentContext = createContext();

export function ContentProvider({ children }) {
  // AI 글 생성 결과 상태
  const [generatedContent, setGeneratedContent] = useState(null);

  // 콘텐츠 초기화
  const clearContent = () => {
    setGeneratedContent(null);
  };

  const value = {
    generatedContent,
    setGeneratedContent,
    clearContent
  };

  return (
    <ContentContext.Provider value={value}>
      {children}
    </ContentContext.Provider>
  );
}

export function useContent() {
  const context = useContext(ContentContext);
  if (!context) {
    throw new Error('useContent must be used within a ContentProvider');
  }
  return context;
}
