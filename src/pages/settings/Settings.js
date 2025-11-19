import React from 'react';
import './Settings.css';

function Settings() {
  return (
    <div className="settings-page">
      <div className="settings-header">
        <h2>⚙️ 설정</h2>
        <p>플랫폼 연동 및 계정 설정을 관리하세요</p>
      </div>

      {/* 기타 플랫폼 */}
      <div className="settings-section">
        <h3>🌐 소셜 미디어 플랫폼</h3>
        <p className="section-description">향후 소셜 미디어 자동 발행 기능이 추가될 예정입니다.</p>
        <div className="platform-list">
          <div className="platform-item disabled">
            <div className="platform-icon">📸</div>
            <div className="platform-info">
              <div className="platform-name">Instagram</div>
              <div className="platform-status">개발 예정</div>
            </div>
            <button className="btn-connect" disabled>준비 중</button>
          </div>
          <div className="platform-item disabled">
            <div className="platform-icon">📘</div>
            <div className="platform-info">
              <div className="platform-name">Facebook</div>
              <div className="platform-status">개발 예정</div>
            </div>
            <button className="btn-connect" disabled>준비 중</button>
          </div>
          <div className="platform-item disabled">
            <div className="platform-icon">🎥</div>
            <div className="platform-info">
              <div className="platform-name">YouTube</div>
              <div className="platform-status">개발 예정</div>
            </div>
            <button className="btn-connect" disabled>준비 중</button>
          </div>
          <div className="platform-item disabled">
            <div className="platform-icon">🐦</div>
            <div className="platform-info">
              <div className="platform-name">Twitter (X)</div>
              <div className="platform-status">개발 예정</div>
            </div>
            <button className="btn-connect" disabled>준비 중</button>
          </div>
        </div>
      </div>

      {/* AI API 설정 */}
      <div className="settings-section">
        <h3>🤖 AI 설정</h3>
        <div className="api-info">
          <p>현재 지원되는 AI 기능:</p>
          <ul>
            <li>✅ AI 이미지 생성 (Google Gemini, Stable Diffusion)</li>
            <li>✅ 프롬프트 최적화 (Claude, Gemini)</li>
            <li>🔄 AI 동영상 제작 (개발 중)</li>
          </ul>
          <p className="mt-3">API 키는 <code>.env</code> 파일에서 관리됩니다.</p>
        </div>
      </div>

      {/* 계정 정보 */}
      <div className="settings-section">
        <h3>👤 계정 정보</h3>
        <div className="api-info">
          <p>계정 설정은 프로필 메뉴에서 관리할 수 있습니다.</p>
        </div>
      </div>
    </div>
  );
}

export default Settings;
