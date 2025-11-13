import React from 'react';
import './Settings.css';

function Settings() {
  return (
    <div className="settings-page">
      <h2>설정</h2>

      <div className="settings-section">
        <h3>플랫폼 연동</h3>
        <div className="platform-list">
          <div className="platform-item">
            <span className="platform-name">Instagram</span>
            <button className="btn-connect">연결하기</button>
          </div>
          <div className="platform-item">
            <span className="platform-name">Facebook</span>
            <button className="btn-connect">연결하기</button>
          </div>
          <div className="platform-item">
            <span className="platform-name">YouTube</span>
            <button className="btn-connect">연결하기</button>
          </div>
        </div>
      </div>

      <div className="settings-section">
        <h3>프로필 정보</h3>
        <div className="form-group">
          <label>비즈니스 이름</label>
          <input type="text" placeholder="비즈니스 이름 입력" />
        </div>
        <div className="form-group">
          <label>이메일</label>
          <input type="email" placeholder="이메일 입력" />
        </div>
      </div>

      <div className="settings-section">
        <h3>알림 설정</h3>
        <div className="toggle-item">
          <span>이메일 알림</span>
          <label className="toggle">
            <input type="checkbox" />
            <span className="slider"></span>
          </label>
        </div>
        <div className="toggle-item">
          <span>발행 알림</span>
          <label className="toggle">
            <input type="checkbox" defaultChecked />
            <span className="slider"></span>
          </label>
        </div>
      </div>

      <button className="btn-save">변경사항 저장</button>
    </div>
  );
}

export default Settings;
