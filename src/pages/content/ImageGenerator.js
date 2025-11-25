import React, { useState } from 'react';
import './ImageGenerator.css';

function ImageGenerator() {
  const [aiModel, setAiModel] = useState('whisk');
  const [imagePrompt, setImagePrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [referenceImage, setReferenceImage] = useState(null);
  const [generationMode, setGenerationMode] = useState('text'); // 'text' or 'image'

  const aiModels = [
    { id: 'whisk', label: '✨ Whisk AI (무료)', provider: 'Pollinations' },
    { id: 'nanovana', label: '나노바나나 (Nanovana)', provider: 'Anthropic' },
    { id: 'gemini', label: '제미나이 (Gemini)', provider: 'Google' },
  ];

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setReferenceImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) {
      alert('이미지 생성을 위한 프롬프트를 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    try {
      const requestBody = {
        prompt: imagePrompt,
        model: aiModel,
      };

      // 레퍼런스 이미지가 있으면 추가
      if (generationMode === 'image' && referenceImage) {
        requestBody.referenceImage = referenceImage;
      }

      const response = await fetch('http://localhost:8000/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const responseText = await response.text();

      if (!response.ok) {
        let errorMessage = '이미지 생성에 실패했습니다.';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          errorMessage = `서버 오류: ${response.status}`;
        }
        alert(errorMessage);
        console.error('Image generation failed:', responseText);
        return;
      }

      const data = JSON.parse(responseText);
      setGeneratedImage(data.imageUrl);

      if (data.optimizedPrompt) {
        console.log('최적화된 프롬프트:', data.optimizedPrompt);
      }
    } catch (error) {
      console.error('Image generation error:', error);
      alert('이미지 생성 중 오류가 발생했습니다. 콘솔을 확인해주세요.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadImage = () => {
    if (!generatedImage) return;

    const link = document.createElement('a');
    link.href = generatedImage;
    link.download = `generated_image_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = () => {
    setGeneratedImage(null);
    setImagePrompt('');
    setReferenceImage(null);
  };

  return (
    <div className="image-generator">
      <div className="page-header">
        <h1>🎨 AI 이미지 생성</h1>
        <p className="page-description">
          텍스트 설명 또는 레퍼런스 이미지로 AI가 이미지를 생성합니다.
        </p>
      </div>

      <div className="image-generator-content">
        <div className="form-section">
          {/* AI 모델 선택 */}
          <div className="section">
            <h3>🤖 AI 모델 선택</h3>
            <select
              className="model-select"
              value={aiModel}
              onChange={(e) => setAiModel(e.target.value)}
            >
              {aiModels.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.label}
                </option>
              ))}
            </select>
            <p className="model-provider">
              {aiModels.find(m => m.id === aiModel)?.provider} 제공
            </p>
          </div>

          {/* 생성 모드 선택 */}
          <div className="section">
            <h3>📐 생성 모드 선택</h3>
            <div className="mode-buttons">
              <button
                className={`mode-button ${generationMode === 'text' ? 'active' : ''}`}
                onClick={() => {
                  setGenerationMode('text');
                  setReferenceImage(null);
                }}
              >
                <div className="mode-icon">📝</div>
                <div className="mode-title">텍스트 → 이미지</div>
                <div className="mode-desc">텍스트 설명으로 이미지 생성</div>
              </button>
              <button
                className={`mode-button ${generationMode === 'image' ? 'active' : ''}`}
                onClick={() => setGenerationMode('image')}
              >
                <div className="mode-icon">🖼️</div>
                <div className="mode-title">이미지 → 이미지</div>
                <div className="mode-desc">레퍼런스 이미지 기반 생성</div>
              </button>
            </div>

            {/* 레퍼런스 이미지 업로드 */}
            {generationMode === 'image' && (
              <div className="reference-upload">
                <label htmlFor="reference-image-upload" className="upload-label">
                  <input
                    id="reference-image-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    style={{ display: 'none' }}
                  />
                  {referenceImage ? (
                    <div className="uploaded-preview">
                      <img src={referenceImage} alt="Reference" />
                      <p className="upload-success">✅ 레퍼런스 이미지 업로드됨 (클릭하여 변경)</p>
                    </div>
                  ) : (
                    <div className="upload-placeholder">
                      <div className="upload-icon">📁</div>
                      <p className="upload-title">레퍼런스 이미지 업로드</p>
                      <p className="upload-hint">클릭하여 이미지 파일 선택</p>
                    </div>
                  )}
                </label>
              </div>
            )}
          </div>

          {/* 프롬프트 입력 */}
          <div className="section">
            <h3>이미지 프롬프트</h3>
            <textarea
              className="prompt-textarea"
              placeholder={
                generationMode === 'text'
                  ? '생성할 이미지를 설명해주세요. 예: 해질녘의 평화로운 호숫가 풍경, 수채화 스타일'
                  : '레퍼런스 이미지를 어떻게 변경할지 설명해주세요.'
              }
              value={imagePrompt}
              onChange={(e) => setImagePrompt(e.target.value)}
              rows={5}
            />
          </div>

          {/* 생성 버튼 */}
          <button
            className="btn-generate"
            onClick={handleGenerateImage}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <span className="spinner"></span>
                이미지 생성 중...
              </>
            ) : (
              <>
                <span>🎨</span>
                이미지 생성하기
              </>
            )}
          </button>

          {/* 안내 사항 */}
          <div className="info-box">
            <h4>💡 AI 모델 안내</h4>
            <ul>
              <li><strong>Whisk AI</strong>: 무료, Pollinations 기반 (FLUX 모델)</li>
              <li><strong>Nanovana</strong>: Gemini 2.5 Flash Image (Text/Image-to-Image)</li>
              <li><strong>Gemini</strong>: Gemini + Stable Diffusion 2.1 조합</li>
            </ul>
          </div>
        </div>

        {/* 생성 결과 */}
        <div className="result-section">
          {generatedImage ? (
            <div className="result-container">
              <div className="result-header">
                <h3>✅ 이미지 생성 완료!</h3>
                <div className="result-actions">
                  <button onClick={handleDownloadImage} className="btn-download">
                    ⬇️ 다운로드
                  </button>
                  <button onClick={handleReset} className="btn-reset">
                    🔄 새로 만들기
                  </button>
                </div>
              </div>
              <div className="generated-image-wrapper">
                <img src={generatedImage} alt="Generated" className="generated-image" />
              </div>
            </div>
          ) : (
            <div className="placeholder-result">
              <div className="placeholder-icon">🎨</div>
              <p>이미지를 생성하면 여기에 결과가 표시됩니다</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ImageGenerator;
