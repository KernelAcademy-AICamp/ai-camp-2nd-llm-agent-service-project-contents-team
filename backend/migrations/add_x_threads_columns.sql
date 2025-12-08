-- AI Generated Contents 테이블에 X 및 Threads 컬럼 추가
-- 실행: psql -d your_database -f add_x_threads_columns.sql

-- X 콘텐츠 컬럼 추가
ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS x_content TEXT;
ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS x_hashtags JSONB;

-- Threads 콘텐츠 컬럼 추가
ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS threads_content TEXT;
ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS threads_hashtags JSONB;

-- 확인
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ai_generated_contents'
AND column_name IN ('x_content', 'x_hashtags', 'threads_content', 'threads_hashtags');
