"""
네이버 블로그 데이터 수집 서비스

법적 근거:
- 한국 저작권법 제35조의3 (정보분석을 위한 복제)
- 사용자 본인의 블로그에 대한 동의 기반 수집
- 공개된 데이터만 수집
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


class NaverBlogService:
    """네이버 블로그 RSS 및 공개 포스트 수집 서비스"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'ContentsTeam/1.0 (Brand Analysis Service; contact@example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        }
        self.delay = 2  # Rate limiting: 2초 대기

    def extract_blog_id(self, blog_url: str) -> Optional[str]:
        """
        블로그 URL에서 블로그 ID 추출

        지원 형식:
        - https://blog.naver.com/user123
        - https://blog.naver.com/user123/222xxx
        - https://user123.blog.me
        """
        try:
            # blog.naver.com 형식
            if 'blog.naver.com' in blog_url:
                path_parts = urlparse(blog_url).path.strip('/').split('/')
                if path_parts and path_parts[0]:
                    return path_parts[0]

            # *.blog.me 형식
            elif '.blog.me' in blog_url:
                domain = urlparse(blog_url).netloc
                blog_id = domain.split('.')[0]
                return blog_id

            return None
        except Exception as e:
            logger.error(f"블로그 ID 추출 실패: {e}")
            return None

    def get_rss_feed(self, blog_url: str, max_posts: int = 10) -> List[Dict[str, str]]:
        """
        네이버 블로그 RSS 피드에서 포스트 목록 가져오기

        Args:
            blog_url: 네이버 블로그 URL
            max_posts: 가져올 최대 포스트 수 (기본 10개)

        Returns:
            포스트 목록 [{'title': ..., 'link': ..., 'published': ...}]
        """
        blog_id = self.extract_blog_id(blog_url)
        if not blog_id:
            raise ValueError(f"유효하지 않은 네이버 블로그 URL입니다: {blog_url}")

        rss_url = f'https://rss.blog.naver.com/{blog_id}.xml'

        try:
            logger.info(f"RSS 피드 요청: {rss_url}")
            feed = feedparser.parse(rss_url)

            if feed.bozo:  # RSS 파싱 오류 체크
                logger.warning(f"RSS 피드 파싱 경고: {feed.bozo_exception}")

            posts = []
            for entry in feed.entries[:max_posts]:
                posts.append({
                    'title': entry.get('title', '제목 없음'),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')
                })

            logger.info(f"RSS에서 {len(posts)}개 포스트 발견")
            return posts

        except Exception as e:
            logger.error(f"RSS 피드 가져오기 실패: {e}")
            raise Exception(f"RSS 피드를 가져올 수 없습니다: {str(e)}")

    def fetch_post_content(self, post_url: str) -> Optional[str]:
        """
        개별 포스트의 본문 내용 수집 (공개 포스트만)

        Args:
            post_url: 포스트 URL

        Returns:
            포스트 본문 텍스트 (HTML 태그 제거)
        """
        try:
            time.sleep(self.delay)  # Rate limiting

            logger.info(f"포스트 본문 요청: {post_url}")
            response = requests.get(post_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 네이버 블로그 iframe 구조 처리
            # 실제 본문은 iframe 안에 있음
            content = None

            # 방법 1: mainFrame iframe의 src 가져오기
            iframe = soup.find('iframe', {'id': 'mainFrame'})
            if iframe and iframe.get('src'):
                iframe_url = iframe['src']
                if not iframe_url.startswith('http'):
                    iframe_url = f"https://blog.naver.com{iframe_url}"

                time.sleep(self.delay)
                iframe_response = requests.get(iframe_url, headers=self.headers, timeout=10)
                iframe_response.raise_for_status()
                iframe_soup = BeautifulSoup(iframe_response.text, 'html.parser')

                # 본문 컨테이너 찾기 (여러 클래스명 시도)
                content_div = (
                    iframe_soup.find('div', {'class': 'se-main-container'}) or  # 스마트에디터 ONE
                    iframe_soup.find('div', {'id': 'postViewArea'}) or  # 구버전
                    iframe_soup.find('div', {'class': 'post-view'})
                )

                if content_div:
                    # 스크립트, 스타일 태그 제거
                    for tag in content_div.find_all(['script', 'style', 'iframe']):
                        tag.decompose()

                    content = content_div.get_text(separator='\n', strip=True)

            if content:
                # 불필요한 공백 제거
                content = re.sub(r'\n\s*\n', '\n\n', content)
                content = content.strip()

                logger.info(f"본문 수집 완료 (길이: {len(content)}자)")
                return content
            else:
                logger.warning(f"본문을 찾을 수 없습니다: {post_url}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP 요청 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"본문 수집 중 오류: {e}")
            return None

    async def collect_blog_posts(self, blog_url: str, max_posts: int = 10) -> List[Dict[str, str]]:
        """
        블로그의 최근 포스트 수집 (RSS + 본문)

        Args:
            blog_url: 네이버 블로그 URL
            max_posts: 최대 수집 포스트 수 (기본 10개)

        Returns:
            수집된 포스트 목록 [{'title': ..., 'content': ..., 'date': ...}]
        """
        try:
            # 1. RSS로 포스트 목록 가져오기
            rss_posts = self.get_rss_feed(blog_url, max_posts)

            if not rss_posts:
                logger.warning("RSS 피드에서 포스트를 찾을 수 없습니다.")
                return []

            # 2. 각 포스트의 본문 수집
            collected_posts = []
            for i, post in enumerate(rss_posts, 1):
                logger.info(f"[{i}/{len(rss_posts)}] 포스트 수집 중: {post['title']}")

                content = self.fetch_post_content(post['link'])

                if content:
                    collected_posts.append({
                        'title': post['title'],
                        'content': content,
                        'date': post['published'],
                        'url': post['link']
                    })
                else:
                    # 본문을 가져오지 못한 경우 요약(summary)만 사용
                    logger.info(f"본문 수집 실패, 요약 사용: {post['title']}")
                    collected_posts.append({
                        'title': post['title'],
                        'content': post['summary'],
                        'date': post['published'],
                        'url': post['link']
                    })

            logger.info(f"총 {len(collected_posts)}개 포스트 수집 완료")
            return collected_posts

        except Exception as e:
            logger.error(f"블로그 포스트 수집 실패: {e}")
            raise Exception(f"블로그 데이터를 수집할 수 없습니다: {str(e)}")
