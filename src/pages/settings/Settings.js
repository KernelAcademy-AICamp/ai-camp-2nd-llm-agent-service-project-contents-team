import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { youtubeAPI, facebookAPI } from '../../services/api';
import './Settings.css';

function Settings() {
  const [youtubeConnection, setYoutubeConnection] = useState(null);
  const [facebookConnection, setFacebookConnection] = useState(null);

  useEffect(() => {
    const fetchYoutubeStatus = async () => {
      try {
        const data = await youtubeAPI.getStatus();
        setYoutubeConnection(data);
      } catch (err) {
        console.error('Failed to fetch YouTube status:', err);
      }
    };

    const fetchFacebookStatus = async () => {
      try {
        const data = await facebookAPI.getStatus();
        setFacebookConnection(data);
      } catch (err) {
        console.error('Failed to fetch Facebook status:', err);
      }
    };

    fetchYoutubeStatus();
    fetchFacebookStatus();
  }, []);

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h2>설정</h2>
        <p>플랫폼 연동 및 계정 설정을 관리하세요</p>
      </div>

      {/* 기타 플랫폼 */}
      <div className="settings-section">
        <h3>소셜 미디어 플랫폼</h3>
        <p className="section-description">소셜 미디어 플랫폼을 연동하여 콘텐츠를 관리하세요.</p>
        <div className="platform-list">
          <Link to="/youtube" className={`platform-item ${youtubeConnection ? 'connected' : ''}`}>
            <div className="platform-icon">📺</div>
            <div className="platform-info">
              <div className="platform-name">YouTube</div>
              <div className="platform-status">
                {youtubeConnection
                  ? `연동됨 - ${youtubeConnection.channel_title}`
                  : '연동 가능'}
              </div>
            </div>
            <span className="btn-connect">
              {youtubeConnection ? '관리하기' : '연동하기'}
            </span>
          </Link>
          <Link to="/facebook" className={`platform-item ${facebookConnection ? 'connected' : ''}`}>
            <div className="platform-icon">📘</div>
            <div className="platform-info">
              <div className="platform-name">Facebook</div>
              <div className="platform-status">
                {facebookConnection
                  ? `연동됨 - ${facebookConnection.page_name || facebookConnection.facebook_user_name}`
                  : '연동 가능'}
              </div>
            </div>
            <span className="btn-connect">
              {facebookConnection ? '관리하기' : '연동하기'}
            </span>
          </Link>
          <div className="platform-item disabled">
            <div className="platform-icon">📸</div>
            <div className="platform-info">
              <div className="platform-name">Instagram</div>
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
