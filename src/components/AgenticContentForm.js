import React, { useState, useEffect } from 'react';
import './AgenticContentForm.css';

function AgenticContentForm({ onGenerate, isGenerating, initialText = '' }) {
  const [textInput, setTextInput] = useState(initialText);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);

  // initialText가 변경되면 textInput 업데이트
  useEffect(() => {
    if (initialText) {
      setTextInput(initialText);
    }
  }, [initialText]);

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);

    if (uploadedImages.length + files.length > 5) {
      alert('이미지는 최대 5개까지 업로드 가능합니다.');
      return;
    }

    // 파일 객체 저장
    setUploadedImages([...uploadedImages, ...files]);

    // 미리보기 URL 생성
    const newPreviews = files.map(file => URL.createObjectURL(file));
    setImagePreviews([...imagePreviews, ...newPreviews]);
  };

  const handleRemoveImage = (index) => {
    const newImages = uploadedImages.filter((_, i) => i !== index);
    const newPreviews = imagePreviews.filter((_, i) => i !== index);

    // 메모리 해제
    URL.revokeObjectURL(imagePreviews[index]);

    setUploadedImages(newImages);
    setImagePreviews(newPreviews);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // 최소한 텍스트나 이미지 중 하나는 있어야 함
    if (!textInput.trim() && uploadedImages.length === 0) {
      alert('텍스트 또는 이미지를 최소 1개 이상 입력해주세요.');
      return;
    }

    onGenerate({
      textInput: textInput.trim(),
      images: uploadedImages
    });
  };

  const handleReset = () => {
    setTextInput('');
    setUploadedImages([]);
    imagePreviews.forEach(url => URL.revokeObjectURL(url));
    setImagePreviews([]);
  };

  return (
    <div className="agentic-content-form">
      <div className="form-header">
        <h3>AI 글 생성</h3>
        <p className="form-description">
          텍스트, 이미지 또는 둘 다 입력하면 AI가 자동으로 네이버 블로그와 SNS용 콘텐츠를 생성합니다.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <label className="form-label">
            텍스트 입력 <span className="optional">(선택)</span>
          </label>
          <textarea
            className="text-input"
            placeholder="예: 우리 카페에서 신메뉴 딸기라떼를 출시했어요! 상큼하고 달콤한 맛이 일품입니다."
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            rows={6}
            disabled={isGenerating}
          />
          <div className="input-hint">
            제품/서비스 정보, 홍보 내용, 이벤트 내용 등을 자유롭게 입력하세요.
          </div>
        </div>

        <div className="form-section">
          <label className="form-label">
            이미지 업로드 <span className="optional">(선택, 최대 5개)</span>
          </label>

          {uploadedImages.length < 5 && (
            <div className="image-upload-area">
              <input
                type="file"
                id="image-upload"
                accept="image/*"
                multiple
                onChange={handleImageUpload}
                disabled={isGenerating}
                style={{ display: 'none' }}
              />
              <label htmlFor="image-upload" className="upload-button">
                <span className="upload-icon">📸</span>
                <span>이미지 선택</span>
                <span className="upload-count">
                  ({uploadedImages.length}/5)
                </span>
              </label>
            </div>
          )}

          {imagePreviews.length > 0 && (
            <div className="image-preview-grid">
              {imagePreviews.map((preview, index) => (
                <div key={index} className="image-preview-item">
                  <img src={preview} alt={`업로드 ${index + 1}`} />
                  <button
                    type="button"
                    className="remove-image-btn"
                    onClick={() => handleRemoveImage(index)}
                    disabled={isGenerating}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="input-hint">
            제품, 장소, 분위기 등을 담은 이미지를 업로드하면 AI가 분석하여 콘텐츠에 반영합니다.
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn-reset"
            onClick={handleReset}
            disabled={isGenerating}
          >
            초기화
          </button>
          <button
            type="submit"
            className="btn-generate"
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <span className="spinner-small"></span>
                AI 생성 중...
              </>
            ) : (
              <>
                ✨ AI로 콘텐츠 생성하기
              </>
            )}
          </button>
        </div>
      </form>

      {isGenerating && (
        <div className="generation-progress">
          <div className="progress-message">
            AI가 콘텐츠를 분석하고 생성하고 있습니다. 잠시만 기다려주세요...
          </div>
        </div>
      )}
    </div>
  );
}

export default AgenticContentForm;
