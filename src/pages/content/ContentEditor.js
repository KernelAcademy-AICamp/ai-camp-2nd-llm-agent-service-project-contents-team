import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiCopy, FiSend, FiCheck, FiEdit3, FiSave, FiClock, FiX, FiUpload, FiImage, FiTrash2, FiYoutube, FiInstagram, FiFacebook } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';
import { publishedContentAPI, youtubeAPI, instagramAPI, facebookAPI } from '../../services/api';
import './ContentEditor.css';

// 플랫폼 설정
const PLATFORM_CONFIG = {
  blog: {
    name: '블로그',
    icon: '📝',
    maxLength: null,
    hasTitle: true,
    canPublish: false  // 블로그는 직접 발행 불가
  },
  sns: {
    name: 'Instagram / Facebook',
    icon: '📷',
    maxLength: 2200,
    hasTitle: false,
    canPublish: true
  },
  x: {
    name: 'X',
    icon: '𝕏',
    maxLength: 280,
    hasTitle: false,
    canPublish: true
  },
  threads: {
    name: 'Threads',
    icon: '🧵',
    maxLength: 500,
    hasTitle: false,
    canPublish: true
  },
};

function ContentEditor() {
  const location = useLocation();
  const navigate = useNavigate();
  const { result, topic, sessionId, isVideo } = location.state || {};

  // 편집 상태
  const [editedContent, setEditedContent] = useState({});
  const [activePlatform, setActivePlatform] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingField, setEditingField] = useState(null); // 'title' | 'content' | 'tags'

  // 저장 상태
  const [isSaved, setIsSaved] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savedContentIds, setSavedContentIds] = useState({}); // 플랫폼별 저장된 콘텐츠 ID
  const initialContentRef = useRef(null);

  // 발행 상태
  const [publishingPlatform, setPublishingPlatform] = useState(null);
  const [publishResults, setPublishResults] = useState({});

  // 예약 발행 모달
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [isScheduling, setIsScheduling] = useState(false);

  // 이미지 ID 목록 (세션에서 가져온 경우)
  const [imageIds, setImageIds] = useState([]);

  // 이미지 업로드 상태
  const [uploadedImages, setUploadedImages] = useState([]); // 직접 업로드한 이미지들
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  // 카드뉴스 발행 모달
  const [showCardnewsPublishModal, setShowCardnewsPublishModal] = useState(false);
  const [cardnewsCaption, setCardnewsCaption] = useState('');
  const [selectedPublishPlatform, setSelectedPublishPlatform] = useState('instagram');
  const [isPublishingCardnews, setIsPublishingCardnews] = useState(false);

  // SNS 플랫폼 선택 모달 (Instagram/Facebook)
  const [showSnsSelectModal, setShowSnsSelectModal] = useState(false);
  const [snsSelectMode, setSnsSelectMode] = useState('publish'); // 'publish' | 'schedule'
  const [cardnewsPublishResult, setCardnewsPublishResult] = useState(null);

  // 카드뉴스 저장 상태 (자동 저장 비활성화로 현재 미사용)
  // const [cardnewsContentId, setCardnewsContentId] = useState(null);
  // const [isCardnewsSaved, setIsCardnewsSaved] = useState(false);

  // YouTube 발행 상태
  const [showYouTubeModal, setShowYouTubeModal] = useState(false);
  const [youtubeStatus, setYoutubeStatus] = useState(null);
  const [isPublishingYouTube, setIsPublishingYouTube] = useState(false);
  const [youtubeForm, setYoutubeForm] = useState({
    title: '',
    description: '',
    tags: '',
    privacyStatus: 'private'
  });
  const [youtubePublishResult, setYoutubePublishResult] = useState(null);

  // Instagram Reels 발행 상태
  const [showInstagramReelsModal, setShowInstagramReelsModal] = useState(false);
  const [instagramStatus, setInstagramStatus] = useState(null);
  const [isPublishingInstagram, setIsPublishingInstagram] = useState(false);
  const [instagramForm, setInstagramForm] = useState({
    caption: '',
    shareToFeed: true
  });
  const [instagramPublishResult, setInstagramPublishResult] = useState(null);

  // Facebook 비디오 발행 상태
  const [showFacebookVideoModal, setShowFacebookVideoModal] = useState(false);
  const [facebookStatus, setFacebookStatus] = useState(null);
  const [isPublishingFacebook, setIsPublishingFacebook] = useState(false);
  const [facebookForm, setFacebookForm] = useState({
    title: '',
    description: ''
  });
  const [facebookPublishResult, setFacebookPublishResult] = useState(null);

  // 초기 데이터 설정
  useEffect(() => {
    if (result?.text) {
      const initialContent = {};
      const platforms = [];

      if (result.text.blog) {
        initialContent.blog = {
          title: result.text.blog.title || '',
          content: result.text.blog.content || '',
          tags: result.text.blog.tags || [],
        };
        platforms.push('blog');
      }
      if (result.text.sns) {
        initialContent.sns = {
          content: result.text.sns.content || '',
          tags: result.text.sns.tags || result.text.sns.hashtags || [],
        };
        platforms.push('sns');
      }
      if (result.text.x) {
        initialContent.x = {
          content: result.text.x.content || '',
          tags: result.text.x.tags || result.text.x.hashtags || [],
        };
        platforms.push('x');
      }
      if (result.text.threads) {
        initialContent.threads = {
          content: result.text.threads.content || '',
          tags: result.text.threads.tags || result.text.threads.hashtags || [],
        };
        platforms.push('threads');
      }

      setEditedContent(initialContent);
      initialContentRef.current = JSON.stringify(initialContent);
      if (platforms.length > 0) {
        setActivePlatform(platforms[0]);
      }

      // 이미지 ID 설정
      if (result.images?.length > 0) {
        // 이미지에 id가 있으면 사용, 없으면 빈 배열
        const ids = result.images.map(img => img.id).filter(Boolean);
        setImageIds(ids);
      }
    }
  }, [result]);

  // 데이터가 없으면 리다이렉트
  useEffect(() => {
    if (!result) {
      navigate('/content/create');
    }
  }, [result, navigate]);

  // 카드뉴스 자동 저장 비활성화
  // 카드뉴스는 사용자가 직접 "SNS 발행하기" 버튼을 클릭했을 때만 발행됨
  // (이전에는 편집 페이지 진입 시 자동으로 draft 저장되었으나,
  //  글+이미지 모드에서도 카드뉴스로 잘못 저장되는 문제가 있었음)

  // 변경 감지
  useEffect(() => {
    if (initialContentRef.current) {
      const currentContent = JSON.stringify(editedContent);
      setIsSaved(currentContent === initialContentRef.current);
    }
  }, [editedContent]);

  // 페이지 이탈 경고 (브라우저 새로고침/닫기)
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (!isSaved) {
        e.preventDefault();
        e.returnValue = '저장하지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isSaved]);

  const availablePlatforms = Object.keys(editedContent);

  // 콘텐츠 수정 핸들러
  const handleContentChange = (platform, field, value) => {
    setEditedContent(prev => ({
      ...prev,
      [platform]: {
        ...prev[platform],
        [field]: value,
      },
    }));
  };

  // 태그 수정 핸들러
  const handleTagsChange = (platform, tagsString) => {
    const tags = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
    handleContentChange(platform, 'tags', tags);
  };

  // 임시저장 핸들러
  const handleSave = useCallback(async () => {
    if (isSaved || isSaving) return;

    setIsSaving(true);
    try {
      const data = editedContent[activePlatform];
      if (!data) {
        throw new Error('저장할 콘텐츠가 없습니다.');
      }

      // 이미지 URL 결정: 직접 업로드 > AI 생성 이미지 > 세션 이미지 ID
      let imageUrl = null;
      if (uploadedImages.length > 0) {
        imageUrl = uploadedImages[0].url;
      } else if (result?.images?.length > 0) {
        const firstImg = result.images[0].url || result.images[0].image_url;
        if (firstImg && !firstImg.startsWith('data:')) {
          imageUrl = firstImg;
        }
      }

      const savedContent = await publishedContentAPI.saveDraft({
        id: savedContentIds[activePlatform] || null,  // 기존 ID가 있으면 전달 (업데이트)
        session_id: sessionId || null,
        platform: activePlatform,
        title: data.title || null,
        content: data.content,
        tags: data.tags,
        image_ids: imageIds.length > 0 ? imageIds : null,
        uploaded_image_url: imageUrl,
      });

      // 저장된 콘텐츠 ID 업데이트
      setSavedContentIds(prev => ({
        ...prev,
        [activePlatform]: savedContent.id,
      }));

      initialContentRef.current = JSON.stringify(editedContent);
      setIsSaved(true);
      alert('임시저장되었습니다.');
    } catch (error) {
      console.error('저장 실패:', error);
      alert('저장에 실패했습니다: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsSaving(false);
    }
  }, [editedContent, activePlatform, sessionId, imageIds, isSaved, isSaving, savedContentIds, uploadedImages, result]);

  // 뒤로가기 핸들러 (저장 확인)
  const handleGoBack = useCallback(() => {
    if (!isSaved) {
      const confirmed = window.confirm('저장하지 않은 변경사항이 있습니다. 저장하시겠습니까?');
      if (confirmed) {
        handleSave().then(() => navigate(-1));
        return;
      }
    }
    navigate(-1);
  }, [isSaved, handleSave, navigate]);

  // 복사 핸들러
  const handleCopy = (platform) => {
    const data = editedContent[platform];
    if (!data) return;

    let text = '';
    if (data.title) text += `${data.title}\n\n`;
    text += data.content;
    if (data.tags?.length > 0) {
      text += '\n\n' + data.tags.map(tag => tag.startsWith('#') ? tag : `#${tag}`).join(' ');
    }

    navigator.clipboard.writeText(text);
    alert(`${PLATFORM_CONFIG[platform].name} 콘텐츠가 복사되었습니다.`);
  };

  // 예약 발행 모달 열기
  const openScheduleModal = () => {
    // 기본값: 내일 오전 9시
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);

    setScheduleDate(tomorrow.toISOString().split('T')[0]);
    setScheduleTime('09:00');
    setShowScheduleModal(true);
  };

  // 예약 발행 핸들러
  const handleSchedule = async () => {
    if (!scheduleDate || !scheduleTime) {
      alert('예약 날짜와 시간을 선택해주세요.');
      return;
    }

    const scheduledAt = new Date(`${scheduleDate}T${scheduleTime}`);
    if (scheduledAt <= new Date()) {
      alert('예약 시간은 현재 시간 이후여야 합니다.');
      return;
    }

    setIsScheduling(true);
    try {
      const data = editedContent[activePlatform];
      if (!data) {
        throw new Error('예약할 콘텐츠가 없습니다.');
      }

      // 이미지 URL 결정: 직접 업로드 > AI 생성 이미지 > 세션 이미지 ID
      let imageUrl = null;
      if (uploadedImages.length > 0) {
        imageUrl = uploadedImages[0].url;
      } else if (result?.images?.length > 0) {
        const firstImg = result.images[0].url || result.images[0].image_url;
        if (firstImg && !firstImg.startsWith('data:')) {
          imageUrl = firstImg;
        }
      }

      await publishedContentAPI.schedule({
        id: savedContentIds[activePlatform] || null,  // 기존 ID가 있으면 전달
        session_id: sessionId || null,
        platform: activePlatform,
        title: data.title || null,
        content: data.content,
        tags: data.tags,
        image_ids: imageIds.length > 0 ? imageIds : null,
        uploaded_image_url: imageUrl,
        scheduled_at: scheduledAt.toISOString(),
      });

      setShowScheduleModal(false);
      setPublishResults(prev => ({
        ...prev,
        [activePlatform]: {
          success: true,
          message: `${scheduledAt.toLocaleString('ko-KR')}에 발행 예약되었습니다.`,
          scheduled: true,
        },
      }));

      // 저장 상태 업데이트
      initialContentRef.current = JSON.stringify(editedContent);
      setIsSaved(true);
    } catch (error) {
      console.error('예약 실패:', error);
      alert('예약에 실패했습니다: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsScheduling(false);
    }
  };

  // base64 이미지를 서버에 업로드하고 공개 URL 반환
  const uploadBase64Image = async (base64DataUrl) => {
    // base64 데이터를 Blob으로 변환
    const response = await fetch(base64DataUrl);
    const blob = await response.blob();

    // Blob을 File 객체로 변환
    const ext = blob.type.split('/')[1] || 'png';
    const file = new File([blob], `ai-generated-${Date.now()}.${ext}`, { type: blob.type });

    // 서버에 업로드
    const uploadResponse = await publishedContentAPI.uploadImage(file);
    return uploadResponse.image_url;
  };

  // 즉시 발행 핸들러
  const handlePublish = async (platform) => {
    // instagram/facebook은 sns 콘텐츠를 사용
    const contentKey = (platform === 'instagram' || platform === 'facebook') ? 'sns' : platform;

    // 저장되지 않은 변경사항이 있으면 먼저 저장
    if (!isSaved) {
      const confirmed = window.confirm('발행 전에 변경사항을 저장해야 합니다. 저장하시겠습니까?');
      if (confirmed) {
        await handleSave();
      } else {
        return;
      }
    }

    // base64 이미지가 있으면 먼저 업로드 (Instagram/Facebook 발행 시 필수)
    let uploadedImageUrl = null;
    if ((platform === 'instagram' || platform === 'facebook') && result?.images?.length > 0) {
      const firstImg = result.images[0].url || result.images[0].image_url;
      if (firstImg && firstImg.startsWith('data:')) {
        try {
          setPublishingPlatform(platform); // 로딩 표시
          uploadedImageUrl = await uploadBase64Image(firstImg);
          console.log('AI 생성 이미지 업로드 완료:', uploadedImageUrl);
        } catch (uploadError) {
          console.error('이미지 업로드 실패:', uploadError);
          alert('이미지 업로드에 실패했습니다. 다시 시도해주세요.');
          setPublishingPlatform(null);
          return;
        }
      }
    }

    // 저장된 콘텐츠 ID가 없으면 먼저 저장
    let contentId = savedContentIds[platform];
    if (!contentId) {
      try {
        // sns 콘텐츠를 사용하되 발행 플랫폼은 instagram/facebook으로 지정
        const data = editedContent[contentKey];

        // 이미지 URL 결정: 방금 업로드한 이미지 > 직접 업로드 > AI 생성 이미지 URL
        let imageUrl = uploadedImageUrl;
        if (!imageUrl && uploadedImages.length > 0) {
          imageUrl = uploadedImages[0].url;
        } else if (!imageUrl && result?.images?.length > 0) {
          const firstImg = result.images[0].url || result.images[0].image_url;
          if (firstImg && !firstImg.startsWith('data:')) {
            imageUrl = firstImg;
          }
        }

        const savedContent = await publishedContentAPI.saveDraft({
          id: savedContentIds[platform] || null,  // 기존 ID가 있으면 전달
          session_id: sessionId || null,
          platform: platform,  // 실제 발행 플랫폼 (instagram/facebook)
          title: data.title || null,
          content: data.content,
          tags: data.tags,
          image_ids: imageIds.length > 0 ? imageIds : null,
          uploaded_image_url: imageUrl,
        });
        contentId = savedContent.id;
        setSavedContentIds(prev => ({ ...prev, [platform]: contentId }));
      } catch (error) {
        console.error('저장 실패:', error);
        alert('발행 전 저장에 실패했습니다.');
        setPublishingPlatform(null);
        return;
      }
    } else if (uploadedImageUrl) {
      // 이미 저장된 콘텐츠가 있지만 base64 이미지를 새로 업로드한 경우, 콘텐츠 업데이트
      try {
        await publishedContentAPI.update(contentId, {
          uploaded_image_url: uploadedImageUrl,
        });
        console.log('콘텐츠에 업로드된 이미지 URL 업데이트 완료');
      } catch (updateError) {
        console.error('콘텐츠 업데이트 실패:', updateError);
        // 업데이트 실패해도 발행 시도는 계속
      }
    }

    setPublishingPlatform(platform);

    try {
      await publishedContentAPI.publish(contentId);

      setPublishResults(prev => ({
        ...prev,
        [platform]: { success: true, message: '발행 완료!' },
      }));

      // 발행 성공 시 콘텐츠 관리 > 발행됨 탭으로 이동
      setTimeout(() => {
        navigate('/contents?status=published');
      }, 1000);
    } catch (error) {
      setPublishResults(prev => ({
        ...prev,
        [platform]: { success: false, message: error.response?.data?.detail || error.message },
      }));
    } finally {
      setPublishingPlatform(null);
    }
  };

  // 편집 모드 토글
  const startEditing = (field) => {
    setIsEditing(true);
    setEditingField(field);
  };

  const finishEditing = () => {
    setIsEditing(false);
    setEditingField(null);
  };

  // 이미지 업로드 핸들러
  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 파일 타입 검증
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      alert('지원하지 않는 파일 형식입니다. (JPEG, PNG, GIF, WebP만 가능)');
      return;
    }

    // 파일 크기 검증 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('파일 크기는 10MB 이하만 가능합니다.');
      return;
    }

    setIsUploading(true);
    try {
      const response = await publishedContentAPI.uploadImage(file);

      // 업로드된 이미지 추가
      setUploadedImages(prev => [...prev, {
        url: response.image_url,
        public_id: response.public_id,
        width: response.width,
        height: response.height,
      }]);

      // 저장 상태 변경
      setIsSaved(false);
    } catch (error) {
      console.error('이미지 업로드 실패:', error);
      alert('이미지 업로드에 실패했습니다: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
      // 파일 입력 초기화 (같은 파일 재선택 가능하도록)
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 업로드된 이미지 삭제 핸들러
  const handleRemoveUploadedImage = (index) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
    setIsSaved(false);
  };

  // Instagram/SNS 플랫폼에서 이미지가 필요한지 확인
  const needsImageUpload = (platform) => {
    if (platform !== 'sns' && platform !== 'instagram') return false;

    // 업로드된 이미지가 있으면 필요 없음
    if (uploadedImages.length > 0) return false;

    // AI 생성 이미지가 있고, base64가 아닌 URL이면 필요 없음
    if (result?.images?.length > 0) {
      const hasValidUrl = result.images.some(img => {
        const url = img.url || img.image_url;
        return url && !url.startsWith('data:');
      });
      if (hasValidUrl) return false;
    }

    return true;
  };

  // 현재 플랫폼에서 사용할 이미지 URL 가져오기
  const getImageUrlForPublish = () => {
    // 업로드된 이미지가 있으면 우선 사용
    if (uploadedImages.length > 0) {
      return uploadedImages[0].url;
    }
    // 세션에서 가져온 이미지가 있으면 사용 (AI 생성 이미지 포함)
    if (result?.images?.length > 0) {
      const imgUrl = result.images[0].url || result.images[0].image_url;
      // base64 이미지는 발행 전에 업로드해야 함
      if (imgUrl && !imgUrl.startsWith('data:')) {
        return imgUrl;
      }
    }
    return null;
  };

  // 발행에 사용할 모든 이미지 URL 가져오기 (AI 생성 이미지 포함)
  const getAllImageUrlsForPublish = () => {
    // 업로드된 이미지가 있으면 우선 사용
    if (uploadedImages.length > 0) {
      return uploadedImages.map(img => img.url);
    }
    // 세션에서 가져온 이미지가 있으면 사용 (AI 생성 이미지 포함)
    if (result?.images?.length > 0) {
      return result.images
        .map(img => img.url || img.image_url)
        .filter(url => url && !url.startsWith('data:')); // base64 제외
    }
    return [];
  };

  // 카드뉴스 발행 모달 열기
  const openCardnewsPublishModal = () => {
    setCardnewsCaption(`${topic || '카드뉴스'}\n\n#카드뉴스 #콘텐츠`);
    setShowCardnewsPublishModal(true);
    setCardnewsPublishResult(null);
  };

  // 카드뉴스 발행 핸들러
  const handlePublishCardnews = async () => {
    if (!result.images || result.images.length === 0) {
      alert('발행할 이미지가 없습니다.');
      return;
    }

    setIsPublishingCardnews(true);
    setCardnewsPublishResult(null);

    try {
      // 이미지 URL 배열 추출
      const imageUrls = result.images.map(img => img.url || img.image_url);

      // SNS 발행 API 호출
      const response = await publishedContentAPI.publishCardnews({
        platform: selectedPublishPlatform,
        image_urls: imageUrls,
        caption: cardnewsCaption,
      });

      const platformName = selectedPublishPlatform === 'instagram' ? 'Instagram' :
                          selectedPublishPlatform === 'facebook' ? 'Facebook' : 'Threads';

      // 발행 성공 - 알림 표시 후 콘텐츠 관리 > 발행됨 탭으로 이동
      alert(`${platformName}에 카드뉴스가 발행되었습니다!`);
      setShowCardnewsPublishModal(false);
      setCardnewsCaption('');
      setSelectedPublishPlatform('instagram');

      // 콘텐츠 관리 > 발행됨 탭으로 이동
      navigate('/contents?status=published');

    } catch (error) {
      console.error('카드뉴스 발행 실패:', error);
      setCardnewsPublishResult({
        success: false,
        message: error.response?.data?.detail || error.message || '발행에 실패했습니다.',
      });
    } finally {
      setIsPublishingCardnews(false);
    }
  };

  // YouTube 발행 모달 열기
  const openYouTubeModal = async () => {
    try {
      const status = await youtubeAPI.getStatus();
      setYoutubeStatus(status);

      // YouTube API는 연동된 경우 객체를 반환하고, 미연동 시 null 반환
      if (!status || !status.channel_id) {
        alert('YouTube 계정이 연동되어 있지 않습니다. 설정에서 YouTube를 연동해주세요.');
        return;
      }

      // 기본값 설정
      setYoutubeForm({
        title: topic || result?.video?.productName || '새 영상',
        description: '',
        tags: '',
        privacyStatus: 'private'
      });
      setYoutubePublishResult(null);
      setShowYouTubeModal(true);
    } catch (error) {
      console.error('YouTube 상태 확인 실패:', error);
      alert('YouTube 연동 상태를 확인할 수 없습니다.');
    }
  };

  // YouTube 발행 핸들러
  const handlePublishYouTube = async () => {
    const videoUrl = result?.video?.url;
    if (!videoUrl) {
      alert('발행할 영상이 없습니다.');
      return;
    }

    setIsPublishingYouTube(true);
    setYoutubePublishResult(null);

    try {
      const tagsArray = youtubeForm.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      const response = await youtubeAPI.uploadVideoFromUrl({
        video_url: videoUrl,
        title: youtubeForm.title,
        description: youtubeForm.description,
        tags: tagsArray,
        category_id: '22', // People & Blogs
        privacy_status: youtubeForm.privacyStatus
      });

      setYoutubePublishResult({
        success: true,
        message: `YouTube에 업로드 완료! 영상 ID: ${response.video_id}`,
        videoUrl: response.video_url
      });

      // 새 탭에서 YouTube 영상 열기
      if (response.video_url) {
        window.open(response.video_url, '_blank');
      }
    } catch (error) {
      console.error('YouTube 업로드 실패:', error);
      setYoutubePublishResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'YouTube 업로드에 실패했습니다.'
      });
    } finally {
      setIsPublishingYouTube(false);
    }
  };

  // Instagram Reels 모달 열기
  const openInstagramReelsModal = async () => {
    try {
      const status = await instagramAPI.getStatus();
      setInstagramStatus(status);

      if (!status || !status.instagram_account_id) {
        alert('Instagram 계정이 연동되어 있지 않습니다. 설정에서 Instagram을 연동해주세요.');
        return;
      }

      // 기본값 설정
      setInstagramForm({
        caption: topic || result?.video?.productName || '',
        shareToFeed: true
      });
      setInstagramPublishResult(null);
      setShowInstagramReelsModal(true);
    } catch (error) {
      console.error('Instagram 상태 확인 실패:', error);
      alert('Instagram 연동 상태를 확인할 수 없습니다.');
    }
  };

  // Instagram Reels 발행 핸들러
  const handlePublishInstagramReels = async () => {
    const videoUrl = result?.video?.url;
    if (!videoUrl) {
      alert('발행할 영상이 없습니다.');
      return;
    }

    setIsPublishingInstagram(true);
    setInstagramPublishResult(null);

    try {
      const response = await instagramAPI.uploadReelsFromUrl({
        video_url: videoUrl,
        caption: instagramForm.caption,
        share_to_feed: instagramForm.shareToFeed
      });

      setInstagramPublishResult({
        success: true,
        message: 'Instagram Reels에 업로드 완료!',
        instagramUrl: response.instagram_url
      });

      // 새 탭에서 Instagram 열기
      if (response.instagram_url) {
        window.open(response.instagram_url, '_blank');
      }
    } catch (error) {
      console.error('Instagram Reels 업로드 실패:', error);
      setInstagramPublishResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'Instagram Reels 업로드에 실패했습니다.'
      });
    } finally {
      setIsPublishingInstagram(false);
    }
  };

  // Facebook 비디오 모달 열기
  const openFacebookVideoModal = async () => {
    try {
      const status = await facebookAPI.getStatus();
      setFacebookStatus(status);

      if (!status || !status.page_id) {
        alert('Facebook 페이지가 연동되어 있지 않습니다. 설정에서 Facebook을 연동해주세요.');
        return;
      }

      // 기본값 설정
      setFacebookForm({
        title: topic || result?.video?.productName || '새 영상',
        description: ''
      });
      setFacebookPublishResult(null);
      setShowFacebookVideoModal(true);
    } catch (error) {
      console.error('Facebook 상태 확인 실패:', error);
      alert('Facebook 연동 상태를 확인할 수 없습니다.');
    }
  };

  // Facebook 비디오 발행 핸들러
  const handlePublishFacebookVideo = async () => {
    const videoUrl = result?.video?.url;
    if (!videoUrl) {
      alert('발행할 영상이 없습니다.');
      return;
    }

    setIsPublishingFacebook(true);
    setFacebookPublishResult(null);

    try {
      const response = await facebookAPI.uploadVideoFromUrl({
        video_url: videoUrl,
        title: facebookForm.title,
        description: facebookForm.description
      });

      setFacebookPublishResult({
        success: true,
        message: 'Facebook에 비디오 업로드 완료!',
        facebookUrl: response.facebook_url
      });

      // 새 탭에서 Facebook 열기
      if (response.facebook_url) {
        window.open(response.facebook_url, '_blank');
      }
    } catch (error) {
      console.error('Facebook 비디오 업로드 실패:', error);
      setFacebookPublishResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'Facebook 비디오 업로드에 실패했습니다.'
      });
    } finally {
      setIsPublishingFacebook(false);
    }
  };

  if (!result) return null;

  const currentData = editedContent[activePlatform];
  const currentConfig = PLATFORM_CONFIG[activePlatform];

  return (
    <div className="content-editor">
      {/* 헤더 */}
      <button className="btn-back" onClick={handleGoBack}>
        <FiArrowLeft /> 돌아가기
      </button>
      <div className="editor-header">
        <div className="editor-header-info">
          <h2>콘텐츠 편집 & 발행</h2>
          <p className="editor-subtitle">주제: {topic}</p>
        </div>
        <button
          className={`btn-save ${isSaved ? 'saved' : 'unsaved'}`}
          onClick={handleSave}
          disabled={isSaved || isSaving}
        >
          {isSaving ? (
            <>저장 중...</>
          ) : isSaved ? (
            <><FiCheck /> 저장됨</>
          ) : (
            <><FiSave /> 임시저장</>
          )}
        </button>
      </div>

      <div className="editor-layout">
        {/* 편집 영역 */}
        <div className="editor-main">
          {/* 플랫폼 탭 (상단) */}
          <div className="platform-tabs-horizontal">
            {availablePlatforms.map(platform => (
              <button
                key={platform}
                className={`platform-tab-h ${activePlatform === platform ? 'active' : ''} ${publishResults[platform]?.success ? 'published' : ''}`}
                onClick={() => setActivePlatform(platform)}
              >
                <span className="platform-tab-icon">{PLATFORM_CONFIG[platform].icon}</span>
                <span className="platform-tab-name">{PLATFORM_CONFIG[platform].name}</span>
                {publishResults[platform]?.success && (
                  <FiCheck className="published-icon" />
                )}
              </button>
            ))}
          </div>
          {currentData && (
            <>
              {/* 제목 (블로그만) */}
              {currentConfig?.hasTitle && (
                <div className="editor-section">
                  <div className="editor-section-header">
                    <label>제목</label>
                    {!isEditing || editingField !== 'title' ? (
                      <button className="btn-edit" onClick={() => startEditing('title')}>
                        <FiEdit3 /> 수정
                      </button>
                    ) : (
                      <button className="btn-done" onClick={finishEditing}>
                        <FiCheck /> 완료
                      </button>
                    )}
                  </div>
                  {editingField === 'title' ? (
                    <input
                      type="text"
                      className="editor-title-input"
                      value={currentData.title || ''}
                      onChange={(e) => handleContentChange(activePlatform, 'title', e.target.value)}
                      autoFocus
                    />
                  ) : (
                    <div className="editor-title-preview">{currentData.title}</div>
                  )}
                </div>
              )}

              {/* 본문 */}
              <div className="editor-section">
                <div className="editor-section-header">
                  <label>본문</label>
                  <div className="editor-section-actions">
                    {currentConfig?.maxLength && (
                      <span className={`char-count ${currentData.content.length > currentConfig.maxLength ? 'over' : ''}`}>
                        {currentData.content.length} / {currentConfig.maxLength}자
                      </span>
                    )}
                    {!isEditing || editingField !== 'content' ? (
                      <button className="btn-edit" onClick={() => startEditing('content')}>
                        <FiEdit3 /> 수정
                      </button>
                    ) : (
                      <button className="btn-done" onClick={finishEditing}>
                        <FiCheck /> 완료
                      </button>
                    )}
                  </div>
                </div>
                {editingField === 'content' ? (
                  <textarea
                    className="editor-content-textarea"
                    value={currentData.content}
                    onChange={(e) => handleContentChange(activePlatform, 'content', e.target.value)}
                    rows={15}
                    autoFocus
                  />
                ) : (
                  <div className="editor-content-preview">
                    {activePlatform === 'blog' ? (
                      <ReactMarkdown remarkPlugins={[remarkBreaks]}>
                        {currentData.content}
                      </ReactMarkdown>
                    ) : (
                      <div className="plain-text">{currentData.content}</div>
                    )}
                  </div>
                )}
              </div>

              {/* 태그 */}
              <div className="editor-section">
                <div className="editor-section-header">
                  <label>태그</label>
                  {!isEditing || editingField !== 'tags' ? (
                    <button className="btn-edit" onClick={() => startEditing('tags')}>
                      <FiEdit3 /> 수정
                    </button>
                  ) : (
                    <button className="btn-done" onClick={finishEditing}>
                      <FiCheck /> 완료
                    </button>
                  )}
                </div>
                {editingField === 'tags' ? (
                  <input
                    type="text"
                    className="editor-tags-input"
                    value={currentData.tags?.join(', ') || ''}
                    onChange={(e) => handleTagsChange(activePlatform, e.target.value)}
                    placeholder="쉼표로 구분하여 입력"
                    autoFocus
                  />
                ) : (
                  <div className="editor-tags-preview">
                    {currentData.tags?.map((tag, idx) => (
                      <span key={idx} className="editor-tag">
                        {tag.startsWith('#') ? tag : `#${tag}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* 액션 버튼 */}
              <div className="editor-actions">
                <button className="btn-copy" onClick={() => handleCopy(activePlatform)}>
                  <FiCopy /> 복사하기
                </button>
                {/* 블로그는 직접 발행 불가 - 예약/즉시 발행 버튼 숨김 */}
                {currentConfig?.canPublish !== false && (
                  <>
                    {/* SNS 플랫폼은 Instagram/Facebook 선택 팝업 */}
                    {activePlatform === 'sns' ? (
                      <>
                        <button
                          className="btn-schedule"
                          onClick={() => {
                            setSnsSelectMode('schedule');
                            setShowSnsSelectModal(true);
                          }}
                          disabled={publishResults[activePlatform]?.success}
                        >
                          <FiClock /> 예약 발행
                        </button>
                        <button
                          className={`btn-publish-platform ${publishResults[activePlatform]?.success ? 'published' : ''}`}
                          onClick={() => {
                            setSnsSelectMode('publish');
                            setShowSnsSelectModal(true);
                          }}
                          disabled={publishingPlatform === activePlatform || publishResults[activePlatform]?.success}
                        >
                          {publishingPlatform === activePlatform ? (
                            <>발행 중...</>
                          ) : publishResults[activePlatform]?.success ? (
                            <><FiCheck /> {publishResults[activePlatform]?.scheduled ? '예약됨' : '발행 완료'}</>
                          ) : (
                            <><FiSend /> 즉시 발행</>
                          )}
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          className="btn-schedule"
                          onClick={openScheduleModal}
                          disabled={publishResults[activePlatform]?.success}
                        >
                          <FiClock /> 예약 발행
                        </button>
                        <button
                          className={`btn-publish-platform ${publishResults[activePlatform]?.success ? 'published' : ''}`}
                          onClick={() => handlePublish(activePlatform)}
                          disabled={publishingPlatform === activePlatform || publishResults[activePlatform]?.success}
                        >
                          {publishingPlatform === activePlatform ? (
                            <>발행 중...</>
                          ) : publishResults[activePlatform]?.success ? (
                            <><FiCheck /> {publishResults[activePlatform]?.scheduled ? '예약됨' : '발행 완료'}</>
                          ) : (
                            <><FiSend /> 즉시 발행</>
                          )}
                        </button>
                      </>
                    )}
                  </>
                )}
              </div>

              {/* 발행 결과 메시지 */}
              {publishResults[activePlatform] && (
                <div className={`publish-result-message ${publishResults[activePlatform].success ? 'success' : 'error'}`}>
                  {publishResults[activePlatform].message}
                </div>
              )}

              {/* Instagram/SNS용 이미지 업로드 섹션 */}
              {(activePlatform === 'sns' || activePlatform === 'instagram') && (
                <div className="editor-images-section">
                  <h4>
                    <FiImage /> 이미지 {(activePlatform === 'sns' || activePlatform === 'instagram') && <span className="required-badge">필수</span>}
                  </h4>

                  {/* 기존 이미지 미리보기 */}
                  {result.images?.length > 0 && (
                    <div className="editor-images-grid-h">
                      {result.images.map((img, idx) => (
                        <div key={`existing-${idx}`} className="editor-image-item-h">
                          <img src={img.url || img.image_url} alt={`이미지 ${idx + 1}`} />
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 업로드된 이미지 미리보기 */}
                  {uploadedImages.length > 0 && (
                    <div className="uploaded-images-section">
                      <p className="uploaded-label">업로드된 이미지</p>
                      <div className="editor-images-grid-h">
                        {uploadedImages.map((img, idx) => (
                          <div key={`uploaded-${idx}`} className="editor-image-item-h uploaded">
                            <img src={img.url} alt={`업로드 이미지 ${idx + 1}`} />
                            <button
                              className="btn-remove-image"
                              onClick={() => handleRemoveUploadedImage(idx)}
                              title="이미지 삭제"
                            >
                              <FiTrash2 />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 이미지 업로드 UI (기존 이미지가 없을 때만 표시) */}
                  {(!result.images || result.images.length === 0) && (
                    <div className={`image-upload-zone ${needsImageUpload(activePlatform) ? 'required' : ''}`}>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/jpeg,image/png,image/gif,image/webp"
                        onChange={handleImageUpload}
                        style={{ display: 'none' }}
                        id="image-upload-input"
                      />
                      <label htmlFor="image-upload-input" className="upload-label">
                        {isUploading ? (
                          <div className="uploading-state">
                            <div className="upload-spinner"></div>
                            <span>업로드 중...</span>
                          </div>
                        ) : uploadedImages.length > 0 ? (
                          <div className="upload-more">
                            <FiUpload />
                            <span>추가 이미지 업로드</span>
                          </div>
                        ) : (
                          <div className="upload-empty">
                            <FiImage className="upload-icon" />
                            <span className="upload-title">이미지를 업로드하세요</span>
                            <span className="upload-desc">Instagram 발행에는 이미지가 필요합니다</span>
                            <span className="upload-hint">JPEG, PNG, GIF, WebP (최대 10MB)</span>
                          </div>
                        )}
                      </label>
                    </div>
                  )}

                  {/* 이미지 필수 경고 */}
                  {needsImageUpload(activePlatform) && (
                    <p className="image-required-warning">
                      ⚠️ Instagram 발행을 위해서는 최소 1개의 이미지가 필요합니다.
                    </p>
                  )}
                </div>
              )}

              {/* 블로그/X/Threads용 이미지 미리보기 (기존 이미지만) */}
              {activePlatform !== 'sns' && activePlatform !== 'instagram' && result.images?.length > 0 && (
                <div className="editor-images-section">
                  <h4>첨부 이미지</h4>
                  <div className="editor-images-grid-h">
                    {result.images.map((img, idx) => (
                      <div key={idx} className="editor-image-item-h">
                        <img src={img.url || img.image_url} alt={`이미지 ${idx + 1}`} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* 카드뉴스 이미지만 있는 경우 (텍스트 콘텐츠 없이) */}
          {!currentData && result?.images?.length > 0 && !isVideo && (
            <div className="editor-cardnews-only">
              <div className="cardnews-header">
                <h3>카드뉴스 이미지 ({result.images.length}장)</h3>
                <button className="btn-publish-cardnews" onClick={openCardnewsPublishModal}>
                  <FiSend /> SNS 발행하기
                </button>
              </div>
              <div className="editor-images-grid-h cardnews-grid">
                {result.images.map((img, idx) => (
                  <div key={idx} className="editor-image-item-h cardnews-item">
                    <img src={img.url || img.image_url} alt={`카드뉴스 ${idx + 1}페이지`} />
                    <span className="cardnews-page-label">{idx + 1}페이지</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 비디오 편집 & YouTube 발행 */}
          {isVideo && result?.video && (
            <div className="editor-video-section">
              <div className="video-editor-header">
                <h3>숏폼 영상 발행</h3>
                <div className="video-meta">
                  <span className="info-badge">🎬 {result.video.tier}</span>
                  <span className="info-badge">{result.video.duration}초</span>
                </div>
              </div>

              <div className="video-player-wrapper">
                <video
                  controls
                  src={result.video.url}
                  className="editor-video-player"
                >
                  <source src={result.video.url} type="video/mp4" />
                  브라우저가 비디오 재생을 지원하지 않습니다.
                </video>
              </div>

              <div className="video-publish-buttons">
                <button
                  className="btn-youtube-publish"
                  onClick={openYouTubeModal}
                >
                  <FiYoutube /> YouTube 발행
                </button>
                <button
                  className="btn-instagram-publish"
                  onClick={openInstagramReelsModal}
                >
                  <FiInstagram /> Instagram Reels
                </button>
                <button
                  className="btn-facebook-publish"
                  onClick={openFacebookVideoModal}
                >
                  <FiFacebook /> Facebook
                </button>
                <a
                  href={result.video.url}
                  download={`${result.video.productName || 'video'}.mp4`}
                  className="btn-download-video"
                >
                  다운로드
                </a>
              </div>

              {youtubePublishResult && (
                <div className={`publish-result-message ${youtubePublishResult.success ? 'success' : 'error'}`}>
                  {youtubePublishResult.success ? <FiCheck /> : null}
                  {youtubePublishResult.message}
                </div>
              )}
              {instagramPublishResult && (
                <div className={`publish-result-message ${instagramPublishResult.success ? 'success' : 'error'}`}>
                  {instagramPublishResult.success ? <FiCheck /> : null}
                  {instagramPublishResult.message}
                </div>
              )}
              {facebookPublishResult && (
                <div className={`publish-result-message ${facebookPublishResult.success ? 'success' : 'error'}`}>
                  {facebookPublishResult.success ? <FiCheck /> : null}
                  {facebookPublishResult.message}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 예약 발행 모달 */}
      {showScheduleModal && (
        <div className="schedule-modal-overlay" onClick={() => setShowScheduleModal(false)}>
          <div className="schedule-modal" onClick={(e) => e.stopPropagation()}>
            <div className="schedule-modal-header">
              <h3>예약 발행</h3>
              <button className="btn-close" onClick={() => setShowScheduleModal(false)}>
                <FiX />
              </button>
            </div>
            <div className="schedule-modal-body">
              <p className="schedule-modal-desc">
                <strong>{PLATFORM_CONFIG[activePlatform]?.name}</strong>에 발행할 시간을 선택하세요.
              </p>
              <div className="schedule-inputs">
                <div className="schedule-input-group">
                  <label>날짜</label>
                  <input
                    type="date"
                    value={scheduleDate}
                    onChange={(e) => setScheduleDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
                <div className="schedule-input-group">
                  <label>시간</label>
                  <input
                    type="time"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                  />
                </div>
              </div>
              {scheduleDate && scheduleTime && (
                <p className="schedule-preview">
                  {new Date(`${scheduleDate}T${scheduleTime}`).toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    weekday: 'long',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}에 발행됩니다.
                </p>
              )}
            </div>
            <div className="schedule-modal-footer">
              <button className="btn-cancel" onClick={() => setShowScheduleModal(false)}>
                취소
              </button>
              <button
                className="btn-confirm"
                onClick={handleSchedule}
                disabled={isScheduling || !scheduleDate || !scheduleTime}
              >
                {isScheduling ? '예약 중...' : '예약하기'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 카드뉴스 발행 모달 */}
      {showCardnewsPublishModal && (
        <div className="schedule-modal-overlay" onClick={() => setShowCardnewsPublishModal(false)}>
          <div className="schedule-modal cardnews-publish-modal" onClick={(e) => e.stopPropagation()}>
            <div className="schedule-modal-header">
              <h3>카드뉴스 SNS 발행</h3>
              <button className="btn-close" onClick={() => setShowCardnewsPublishModal(false)}>
                <FiX />
              </button>
            </div>
            <div className="schedule-modal-body">
              {/* 플랫폼 선택 */}
              <div className="publish-platform-selector">
                <label>발행 플랫폼</label>
                <div className="platform-options">
                  <button
                    className={`platform-option ${selectedPublishPlatform === 'instagram' ? 'active' : ''}`}
                    onClick={() => setSelectedPublishPlatform('instagram')}
                  >
                    <span className="platform-icon">📷</span>
                    <span>Instagram</span>
                  </button>
                  <button
                    className={`platform-option ${selectedPublishPlatform === 'facebook' ? 'active' : ''}`}
                    onClick={() => setSelectedPublishPlatform('facebook')}
                  >
                    <span className="platform-icon">📘</span>
                    <span>Facebook</span>
                  </button>
                  <button
                    className={`platform-option ${selectedPublishPlatform === 'threads' ? 'active' : ''}`}
                    onClick={() => setSelectedPublishPlatform('threads')}
                  >
                    <span className="platform-icon">🧵</span>
                    <span>Threads</span>
                  </button>
                </div>
              </div>

              {/* 캡션 입력 */}
              <div className="publish-caption-section">
                <label>캡션 / 설명</label>
                <textarea
                  className="publish-caption-input"
                  value={cardnewsCaption}
                  onChange={(e) => setCardnewsCaption(e.target.value)}
                  placeholder="카드뉴스와 함께 게시할 텍스트를 입력하세요..."
                  rows={5}
                />
              </div>

              {/* 이미지 미리보기 */}
              <div className="publish-images-preview">
                <label>발행할 이미지 ({result?.images?.length || 0}장)</label>
                <div className="publish-images-scroll">
                  {result?.images?.map((img, idx) => (
                    <div key={idx} className="publish-image-thumb">
                      <img src={img.url || img.image_url} alt={`${idx + 1}페이지`} />
                      <span>{idx + 1}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 발행 결과 메시지 */}
              {cardnewsPublishResult && (
                <div className={`publish-result-message ${cardnewsPublishResult.success ? 'success' : 'error'}`}>
                  {cardnewsPublishResult.success ? <FiCheck /> : null}
                  {cardnewsPublishResult.message}
                </div>
              )}
            </div>
            <div className="schedule-modal-footer">
              <button className="btn-cancel" onClick={() => setShowCardnewsPublishModal(false)}>
                {cardnewsPublishResult?.success ? '닫기' : '취소'}
              </button>
              {!cardnewsPublishResult?.success && (
                <button
                  className="btn-confirm"
                  onClick={handlePublishCardnews}
                  disabled={isPublishingCardnews || !cardnewsCaption.trim()}
                >
                  {isPublishingCardnews ? '발행 중...' : '발행하기'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SNS 플랫폼 선택 모달 (Instagram/Facebook) */}
      {showSnsSelectModal && (
        <div className="schedule-modal-overlay" onClick={() => setShowSnsSelectModal(false)}>
          <div className="schedule-modal sns-select-modal" onClick={(e) => e.stopPropagation()}>
            <div className="schedule-modal-header">
              <h3>{snsSelectMode === 'publish' ? '발행할 플랫폼 선택' : '예약 발행할 플랫폼 선택'}</h3>
              <button className="btn-close" onClick={() => setShowSnsSelectModal(false)}>
                <FiX />
              </button>
            </div>
            <div className="schedule-modal-body">
              <p className="sns-select-desc">어떤 플랫폼에 발행하시겠습니까?</p>
              <div className="sns-platform-buttons">
                <button
                  className="sns-platform-btn instagram"
                  onClick={async () => {
                    setShowSnsSelectModal(false);
                    if (snsSelectMode === 'publish') {
                      await handlePublish('instagram');
                    } else {
                      openScheduleModal();
                    }
                  }}
                  disabled={publishingPlatform}
                >
                  <span className="platform-icon">📷</span>
                  <span className="platform-name">Instagram</span>
                  <span className="platform-desc">사진/이미지 게시물</span>
                </button>
                <button
                  className="sns-platform-btn facebook"
                  onClick={async () => {
                    setShowSnsSelectModal(false);
                    if (snsSelectMode === 'publish') {
                      await handlePublish('facebook');
                    } else {
                      openScheduleModal();
                    }
                  }}
                  disabled={publishingPlatform}
                >
                  <span className="platform-icon">📘</span>
                  <span className="platform-name">Facebook</span>
                  <span className="platform-desc">페이지 게시물</span>
                </button>
              </div>
            </div>
            <div className="schedule-modal-footer">
              <button className="btn-cancel" onClick={() => setShowSnsSelectModal(false)}>
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* YouTube 발행 모달 */}
      {showYouTubeModal && (
        <div className="schedule-modal-overlay" onClick={() => setShowYouTubeModal(false)}>
          <div className="schedule-modal youtube-modal" onClick={(e) => e.stopPropagation()}>
            <div className="schedule-modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiYoutube color="#FF0000" /> YouTube 발행
              </h3>
              <button className="btn-close" onClick={() => setShowYouTubeModal(false)}>
                <FiX />
              </button>
            </div>
            <div className="schedule-modal-body">
              {youtubeStatus?.channel_title && (
                <div className="youtube-channel-info">
                  <strong>채널:</strong> {youtubeStatus.channel_title}
                </div>
              )}

              <div className="youtube-form">
                <div className="form-group">
                  <label>제목 *</label>
                  <input
                    type="text"
                    value={youtubeForm.title}
                    onChange={(e) => setYoutubeForm(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="영상 제목을 입력하세요"
                  />
                </div>

                <div className="form-group">
                  <label>설명</label>
                  <textarea
                    value={youtubeForm.description}
                    onChange={(e) => setYoutubeForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="영상 설명을 입력하세요"
                    rows={4}
                  />
                </div>

                <div className="form-group">
                  <label>태그 (쉼표로 구분)</label>
                  <input
                    type="text"
                    value={youtubeForm.tags}
                    onChange={(e) => setYoutubeForm(prev => ({ ...prev, tags: e.target.value }))}
                    placeholder="예: 일상, vlog, 여행"
                  />
                </div>

                <div className="form-group">
                  <label>공개 설정</label>
                  <select
                    value={youtubeForm.privacyStatus}
                    onChange={(e) => setYoutubeForm(prev => ({ ...prev, privacyStatus: e.target.value }))}
                  >
                    <option value="private">비공개</option>
                    <option value="unlisted">일부 공개</option>
                    <option value="public">전체 공개</option>
                  </select>
                </div>
              </div>

              {youtubePublishResult && (
                <div className={`publish-result-message ${youtubePublishResult.success ? 'success' : 'error'}`}>
                  {youtubePublishResult.success ? <FiCheck /> : null}
                  {youtubePublishResult.message}
                </div>
              )}
            </div>
            <div className="schedule-modal-footer">
              <button className="btn-cancel" onClick={() => setShowYouTubeModal(false)}>
                {youtubePublishResult?.success ? '닫기' : '취소'}
              </button>
              {!youtubePublishResult?.success && (
                <button
                  className="btn-confirm btn-youtube"
                  onClick={handlePublishYouTube}
                  disabled={isPublishingYouTube || !youtubeForm.title.trim()}
                >
                  {isPublishingYouTube ? '업로드 중...' : '업로드'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Instagram Reels 발행 모달 */}
      {showInstagramReelsModal && (
        <div className="schedule-modal-overlay" onClick={() => setShowInstagramReelsModal(false)}>
          <div className="schedule-modal instagram-modal" onClick={(e) => e.stopPropagation()}>
            <div className="schedule-modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiInstagram color="#E4405F" /> Instagram Reels 발행
              </h3>
              <button className="btn-close" onClick={() => setShowInstagramReelsModal(false)}>
                <FiX />
              </button>
            </div>
            <div className="schedule-modal-body">
              {instagramStatus?.instagram_username && (
                <div className="instagram-account-info">
                  <strong>계정:</strong> @{instagramStatus.instagram_username}
                </div>
              )}

              <div className="instagram-form">
                <div className="form-group">
                  <label>캡션</label>
                  <textarea
                    value={instagramForm.caption}
                    onChange={(e) => setInstagramForm(prev => ({ ...prev, caption: e.target.value }))}
                    placeholder="Reels와 함께 표시될 캡션을 입력하세요"
                    rows={4}
                  />
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={instagramForm.shareToFeed}
                      onChange={(e) => setInstagramForm(prev => ({ ...prev, shareToFeed: e.target.checked }))}
                    />
                    피드에도 공유하기
                  </label>
                </div>
              </div>

              {instagramPublishResult && (
                <div className={`publish-result-message ${instagramPublishResult.success ? 'success' : 'error'}`}>
                  {instagramPublishResult.success ? <FiCheck /> : null}
                  {instagramPublishResult.message}
                </div>
              )}
            </div>
            <div className="schedule-modal-footer">
              <button className="btn-cancel" onClick={() => setShowInstagramReelsModal(false)}>
                {instagramPublishResult?.success ? '닫기' : '취소'}
              </button>
              {!instagramPublishResult?.success && (
                <button
                  className="btn-confirm btn-instagram"
                  onClick={handlePublishInstagramReels}
                  disabled={isPublishingInstagram}
                >
                  {isPublishingInstagram ? '업로드 중...' : '업로드'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Facebook 비디오 발행 모달 */}
      {showFacebookVideoModal && (
        <div className="schedule-modal-overlay" onClick={() => setShowFacebookVideoModal(false)}>
          <div className="schedule-modal facebook-modal" onClick={(e) => e.stopPropagation()}>
            <div className="schedule-modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiFacebook color="#1877F2" /> Facebook 비디오 발행
              </h3>
              <button className="btn-close" onClick={() => setShowFacebookVideoModal(false)}>
                <FiX />
              </button>
            </div>
            <div className="schedule-modal-body">
              {facebookStatus?.page_name && (
                <div className="facebook-page-info">
                  <strong>페이지:</strong> {facebookStatus.page_name}
                </div>
              )}

              <div className="facebook-form">
                <div className="form-group">
                  <label>제목</label>
                  <input
                    type="text"
                    value={facebookForm.title}
                    onChange={(e) => setFacebookForm(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="비디오 제목을 입력하세요"
                  />
                </div>

                <div className="form-group">
                  <label>설명</label>
                  <textarea
                    value={facebookForm.description}
                    onChange={(e) => setFacebookForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="비디오 설명을 입력하세요"
                    rows={4}
                  />
                </div>
              </div>

              {facebookPublishResult && (
                <div className={`publish-result-message ${facebookPublishResult.success ? 'success' : 'error'}`}>
                  {facebookPublishResult.success ? <FiCheck /> : null}
                  {facebookPublishResult.message}
                </div>
              )}
            </div>
            <div className="schedule-modal-footer">
              <button className="btn-cancel" onClick={() => setShowFacebookVideoModal(false)}>
                {facebookPublishResult?.success ? '닫기' : '취소'}
              </button>
              {!facebookPublishResult?.success && (
                <button
                  className="btn-confirm btn-facebook"
                  onClick={handlePublishFacebookVideo}
                  disabled={isPublishingFacebook}
                >
                  {isPublishingFacebook ? '업로드 중...' : '업로드'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentEditor;
