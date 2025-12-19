-- 카드뉴스 콘텐츠 테이블 생성
-- 실행: psql -d your_database -f 002_add_cardnews_table.sql
-- 또는: PGPASSWORD='your_password' psql -h host -U user -d database -f 002_add_cardnews_table.sql

-- 1. generated_cardnews_contents 테이블 생성
CREATE TABLE IF NOT EXISTS generated_cardnews_contents (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES content_generation_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- 카드뉴스 기본 정보
    title VARCHAR NOT NULL,
    prompt TEXT NOT NULL,
    purpose VARCHAR(20),  -- promotion, menu, info, event
    page_count INTEGER NOT NULL,

    -- 카드뉴스 페이지 이미지 URL (Cloudinary)
    card_image_urls JSONB NOT NULL,  -- ["https://...", "https://..."]

    -- AI 분석 결과
    analysis_data JSONB,  -- Orchestrator 분석 결과
    pages_data JSONB,  -- 각 페이지별 title, content, layout 등

    -- 디자인 설정
    design_settings JSONB,  -- bg_color, text_color, font_pair, style 등

    -- 품질 점수
    quality_score FLOAT,  -- QA Agent 평가 점수 (0.0 ~ 1.0)
    score INTEGER,  -- 품질 점수 (0-100, 다른 콘텐츠와 일관성)

    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_cardnews_session_id ON generated_cardnews_contents(session_id);
CREATE INDEX IF NOT EXISTS idx_cardnews_user_id ON generated_cardnews_contents(user_id);
CREATE INDEX IF NOT EXISTS idx_cardnews_created_at ON generated_cardnews_contents(created_at DESC);

-- 3. 테이블 생성 확인
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'generated_cardnews_contents'
ORDER BY ordinal_position;

-- 4. 코멘트 추가
COMMENT ON TABLE generated_cardnews_contents IS '생성된 카드뉴스 콘텐츠 저장 테이블';
COMMENT ON COLUMN generated_cardnews_contents.card_image_urls IS 'Cloudinary에 업로드된 카드뉴스 페이지 이미지 URL 배열';
COMMENT ON COLUMN generated_cardnews_contents.pages_data IS '각 페이지별 제목, 내용, 레이아웃 등 메타데이터';
COMMENT ON COLUMN generated_cardnews_contents.design_settings IS '배경색, 텍스트색, 폰트 등 디자인 설정';
