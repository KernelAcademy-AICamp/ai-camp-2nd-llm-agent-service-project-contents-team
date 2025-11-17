# OAuth2.0 소셜 로그인 설정 가이드

이 가이드는 Google, Kakao, Facebook 소셜 로그인을 설정하는 방법을 설명합니다.

## 1. Google OAuth 설정

### 1.1. Google Cloud Console에서 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" > "사용자 인증 정보" 메뉴로 이동

### 1.2. OAuth 2.0 클라이언트 ID 만들기

1. "사용자 인증 정보 만들기" > "OAuth 클라이언트 ID" 선택
2. 애플리케이션 유형: "웹 애플리케이션" 선택
3. 이름 입력 (예: "Contents Creator Local")
4. **승인된 리디렉션 URI 추가 (필수):**
   - 개발: `http://localhost:8000/api/oauth/google/callback`
   - 프로덕션: `https://yourdomain.com/api/oauth/google/callback`

   ⚠️ **중요**: 정확히 일치해야 합니다. 끝에 슬래시(/) 없이 입력하세요!

5. "만들기" 클릭
6. 클라이언트 ID와 클라이언트 시크릿 복사

### 1.3. .env 파일에 추가

```env
GOOGLE_CLIENT_ID=123456789-abcdefghijk.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456
GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback
```

**프로덕션 배포 시:**
```env
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/oauth/google/callback
```

---

## 2. Kakao OAuth 설정

### 2.1. Kakao Developers에서 앱 생성

1. [Kakao Developers](https://developers.kakao.com/) 접속 및 로그인
2. "내 애플리케이션" > "애플리케이션 추가하기"
3. 앱 이름, 사업자명 입력 후 저장

### 2.2. 플랫폼 설정

1. 생성한 앱 선택
2. "플랫폼" > "Web 플랫폼 등록"
3. 사이트 도메인 입력: `http://localhost:3000`

### 2.3. Redirect URI 설정

1. "카카오 로그인" 활성화
2. "Redirect URI" 등록:
   - `http://localhost:8000/api/oauth/kakao/callback`
   - 프로덕션: `https://yourdomain.com/api/oauth/kakao/callback`

### 2.4. 동의항목 설정

1. "동의항목" 메뉴 이동
2. 필수 동의: 닉네임, 프로필 이미지
3. 선택 동의: 카카오계정(이메일)

### 2.5. .env 파일에 추가

```env
KAKAO_CLIENT_ID=your-kakao-rest-api-key
KAKAO_CLIENT_SECRET=  # Kakao는 client secret이 선택사항
KAKAO_REDIRECT_URI=http://localhost:8000/api/oauth/kakao/callback
```

REST API 키는 "앱 설정" > "앱 키"에서 확인 가능합니다.

---

## 3. Facebook OAuth 설정

### 3.1. Facebook Developers에서 앱 생성

1. [Facebook Developers](https://developers.facebook.com/) 접속
2. "내 앱" > "앱 만들기"
3. 사용 사례: "소비자" 선택
4. 앱 유형: "비즈니스" 선택
5. 앱 이름 입력

### 3.2. Facebook 로그인 추가

1. 대시보드에서 "제품 추가" > "Facebook 로그인" 선택
2. 플랫폼: "웹" 선택
3. 사이트 URL: `http://localhost:3000`

### 3.3. 설정

1. "Facebook 로그인" > "설정" 메뉴
2. "유효한 OAuth 리디렉션 URI" 추가:
   - `http://localhost:8000/api/oauth/facebook/callback`
   - 프로덕션: `https://yourdomain.com/api/oauth/facebook/callback`

### 3.4. .env 파일에 추가

```env
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/oauth/facebook/callback
```

앱 ID와 시크릿은 "설정" > "기본 설정"에서 확인 가능합니다.

---

## 4. 테스트

### 4.1. 백엔드 재시작

```bash
# 가상환경 활성화
source backend/venv/bin/activate

# 새 의존성 설치
pip install -r backend/requirements.txt

# 서버 재시작
uvicorn app.main:app --reload
```

### 4.2. 프론트엔드 확인

```bash
npm start
```

http://localhost:3000/login 에서 소셜 로그인 버튼 확인

### 4.3. 각 플랫폼 테스트

1. 해당 소셜 로그인 버튼 클릭
2. OAuth 제공자 페이지로 리디렉션
3. 로그인 및 권한 승인
4. 콜백 URL로 리디렉션
5. 대시보드로 자동 로그인

---

## 5. 프로덕션 배포 시 주의사항

### 5.1. HTTPS 필수

모든 OAuth 제공자는 프로덕션 환경에서 HTTPS를 요구합니다.

### 5.2. Redirect URI 업데이트

각 플랫폼의 설정에서 프로덕션 URL 추가:
- `https://yourdomain.com/api/oauth/{provider}/callback`

### 5.3. .env 파일 보안

- `.env` 파일은 절대 Git에 커밋하지 마세요
- 프로덕션 서버에서 환경 변수로 설정하세요

### 5.4. CORS 설정

`backend/.env`에서 프로덕션 URL 추가:
```env
CORS_ORIGINS=https://yourdomain.com
```

---

## 6. 문제 해결

### 일반적인 오류

1. **"redirect_uri_mismatch"**: Redirect URI가 정확히 일치하는지 확인
2. **"invalid_client"**: Client ID/Secret이 올바른지 확인
3. **CORS 오류**: 백엔드 CORS 설정 확인
4. **"access_denied"**: 사용자가 권한을 거부함

### 디버깅

백엔드 로그 확인:
```bash
# OAuth 에러 메시지 확인
tail -f backend/logs/app.log
```

브라우저 개발자 도구:
- Network 탭에서 OAuth 요청/응답 확인
- Console 탭에서 JavaScript 에러 확인

---

## 7. 참고 링크

- [Google OAuth 문서](https://developers.google.com/identity/protocols/oauth2)
- [Kakao Developers 문서](https://developers.kakao.com/docs/latest/ko/kakaologin/common)
- [Facebook 로그인 문서](https://developers.facebook.com/docs/facebook-login)
