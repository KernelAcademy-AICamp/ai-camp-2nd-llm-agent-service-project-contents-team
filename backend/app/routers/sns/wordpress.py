"""
WordPress API 라우터
- WordPress REST API를 사용한 Application Password 연동
- 게시물 작성, 조회, 수정, 삭제, 미디어 업로드
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, List
import httpx
import base64
import os

from ...database import get_db
from ...models import User, WordPressConnection, WordPressPost
from ... import auth

router = APIRouter(prefix="/api/wordpress", tags=["WordPress"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# Pydantic 모델
class WordPressConnectRequest(BaseModel):
    site_url: str
    username: str
    app_password: str


class WordPressPostCreate(BaseModel):
    title: str
    content: str
    status: str = "draft"  # draft, publish, pending, private
    categories: Optional[List[int]] = None
    tags: Optional[List[int]] = None
    featured_image_id: Optional[int] = None
    excerpt: Optional[str] = None


class WordPressPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    categories: Optional[List[int]] = None
    tags: Optional[List[int]] = None
    featured_image_id: Optional[int] = None
    excerpt: Optional[str] = None


def get_current_user(user_id: int, db: Session) -> User:
    """사용자 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_wp_auth_header(username: str, app_password: str) -> str:
    """WordPress Basic Auth 헤더 생성"""
    credentials = f"{username}:{app_password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def normalize_site_url(url: str) -> str:
    """사이트 URL 정규화"""
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


@router.post("/connect")
async def connect_wordpress(
    request: WordPressConnectRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 사이트 연동
    - Application Password 방식
    """

    site_url = normalize_site_url(request.site_url)
    auth_header = get_wp_auth_header(request.username, request.app_password)

    # 연결 테스트 - 사용자 정보 조회
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 현재 사용자 정보 조회
            user_response = await client.get(
                f"{site_url}/wp-json/wp/v2/users/me",
                headers={"Authorization": auth_header}
            )

            if user_response.status_code == 401:
                raise HTTPException(status_code=401, detail="인증 실패: 사용자명 또는 Application Password를 확인하세요")
            elif user_response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"WordPress 연결 실패: {user_response.status_code}")

            wp_user = user_response.json()

            # 사이트 정보 조회
            site_response = await client.get(f"{site_url}/wp-json")
            site_info = {}
            if site_response.status_code == 200:
                site_info = site_response.json()

    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"WordPress 사이트에 연결할 수 없습니다: {str(e)}")

    # 기존 연동 확인
    existing_connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id
    ).first()

    if existing_connection:
        # 업데이트
        existing_connection.site_url = site_url
        existing_connection.site_name = site_info.get("name")
        existing_connection.site_description = site_info.get("description")
        existing_connection.site_icon_url = site_info.get("site_icon_url")
        existing_connection.wp_user_id = wp_user.get("id")
        existing_connection.wp_username = request.username
        existing_connection.wp_display_name = wp_user.get("name")
        existing_connection.wp_email = wp_user.get("email")
        existing_connection.wp_avatar_url = wp_user.get("avatar_urls", {}).get("96")
        existing_connection.wp_app_password = request.app_password
        existing_connection.is_active = True
        existing_connection.last_synced_at = datetime.utcnow()
    else:
        # 새로 생성
        new_connection = WordPressConnection(
            user_id=current_user.id,
            site_url=site_url,
            site_name=site_info.get("name"),
            site_description=site_info.get("description"),
            site_icon_url=site_info.get("site_icon_url"),
            wp_user_id=wp_user.get("id"),
            wp_username=request.username,
            wp_display_name=wp_user.get("name"),
            wp_email=wp_user.get("email"),
            wp_avatar_url=wp_user.get("avatar_urls", {}).get("96"),
            wp_app_password=request.app_password,
            is_active=True,
            last_synced_at=datetime.utcnow()
        )
        db.add(new_connection)

    db.commit()

    return {
        "message": "WordPress connected successfully",
        "site_name": site_info.get("name"),
        "wp_username": request.username
    }


@router.get("/status")
async def get_wordpress_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 연동 상태 확인
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        return None

    return {
        "site_url": connection.site_url,
        "site_name": connection.site_name,
        "site_description": connection.site_description,
        "site_icon_url": connection.site_icon_url,
        "wp_user_id": connection.wp_user_id,
        "wp_username": connection.wp_username,
        "wp_display_name": connection.wp_display_name,
        "wp_avatar_url": connection.wp_avatar_url,
        "post_count": connection.post_count,
        "categories": connection.categories,
        "last_synced_at": connection.last_synced_at.isoformat() if connection.last_synced_at else None
    }


@router.delete("/disconnect")
async def disconnect_wordpress(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 연동 해제
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    db.delete(connection)
    db.commit()

    return {"message": "WordPress disconnected successfully"}


@router.post("/refresh")
async def refresh_wordpress_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 사이트 정보 새로고침
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    auth_header = get_wp_auth_header(connection.wp_username, connection.wp_app_password)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 사이트 정보 조회
            site_response = await client.get(f"{connection.site_url}/wp-json")
            if site_response.status_code == 200:
                site_info = site_response.json()
                connection.site_name = site_info.get("name", connection.site_name)
                connection.site_description = site_info.get("description", connection.site_description)

            # 카테고리 목록 조회
            cat_response = await client.get(
                f"{connection.site_url}/wp-json/wp/v2/categories",
                params={"per_page": 100},
                headers={"Authorization": auth_header}
            )
            if cat_response.status_code == 200:
                categories = cat_response.json()
                connection.categories = [
                    {"id": cat["id"], "name": cat["name"], "slug": cat["slug"]}
                    for cat in categories
                ]
                connection.category_count = len(categories)

            # 게시물 수 조회
            posts_response = await client.head(
                f"{connection.site_url}/wp-json/wp/v2/posts",
                headers={"Authorization": auth_header}
            )
            if "X-WP-Total" in posts_response.headers:
                connection.post_count = int(posts_response.headers["X-WP-Total"])

            connection.last_synced_at = datetime.utcnow()
            db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh: {str(e)}")

    return {
        "message": "WordPress info refreshed",
        "site_name": connection.site_name,
        "post_count": connection.post_count,
        "category_count": connection.category_count
    }


@router.get("/categories")
async def get_wordpress_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 카테고리 목록 조회
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    # 캐시된 카테고리 반환 또는 API 호출
    if connection.categories:
        return {"categories": connection.categories}

    auth_header = get_wp_auth_header(connection.wp_username, connection.wp_app_password)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{connection.site_url}/wp-json/wp/v2/categories",
            params={"per_page": 100},
            headers={"Authorization": auth_header}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch categories")

    categories = response.json()
    result = [{"id": cat["id"], "name": cat["name"], "slug": cat["slug"]} for cat in categories]

    # 캐시 업데이트
    connection.categories = result
    db.commit()

    return {"categories": result}


@router.get("/posts")
async def get_wordpress_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="Filter by status: publish, draft, pending, private"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 게시물 목록 조회 (DB에서)
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    query = db.query(WordPressPost).filter(
        WordPressPost.connection_id == connection.id
    )

    if status:
        query = query.filter(WordPressPost.status == status)

    posts = query.order_by(WordPressPost.published_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": post.id,
            "wp_post_id": post.wp_post_id,
            "title": post.title,
            "excerpt": post.excerpt,
            "status": post.status,
            "post_url": post.post_url,
            "featured_image_url": post.featured_image_url,
            "categories": post.categories,
            "tags": post.tags,
            "comment_count": post.comment_count,
            "published_at": post.published_at.isoformat() if post.published_at else None
        }
        for post in posts
    ]


@router.post("/posts/sync")
async def sync_wordpress_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress에서 게시물 목록 동기화
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    auth_header = get_wp_auth_header(connection.wp_username, connection.wp_app_password)
    synced_count = 0

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{connection.site_url}/wp-json/wp/v2/posts",
                params={
                    "per_page": 50,
                    "status": "any",
                    "_embed": "true"
                },
                headers={"Authorization": auth_header}
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch posts")

        posts = response.json()

        for post_data in posts:
            wp_post_id = post_data.get("id")

            existing_post = db.query(WordPressPost).filter(
                WordPressPost.wp_post_id == wp_post_id,
                WordPressPost.connection_id == connection.id
            ).first()

            published_at = None
            if post_data.get("date"):
                try:
                    published_at = datetime.fromisoformat(post_data["date"].replace("Z", "+00:00"))
                except:
                    pass

            modified_at = None
            if post_data.get("modified"):
                try:
                    modified_at = datetime.fromisoformat(post_data["modified"].replace("Z", "+00:00"))
                except:
                    pass

            # 카테고리/태그 정보 추출
            embedded = post_data.get("_embedded", {})
            categories = []
            tags = []

            if "wp:term" in embedded:
                for term_group in embedded["wp:term"]:
                    for term in term_group:
                        if term.get("taxonomy") == "category":
                            categories.append({"id": term["id"], "name": term["name"]})
                        elif term.get("taxonomy") == "post_tag":
                            tags.append({"id": term["id"], "name": term["name"]})

            # 대표 이미지
            featured_image_url = None
            if "wp:featuredmedia" in embedded and embedded["wp:featuredmedia"]:
                featured_image_url = embedded["wp:featuredmedia"][0].get("source_url")

            if existing_post:
                existing_post.title = post_data.get("title", {}).get("rendered", existing_post.title)
                existing_post.content = post_data.get("content", {}).get("rendered", existing_post.content)
                existing_post.excerpt = post_data.get("excerpt", {}).get("rendered", existing_post.excerpt)
                existing_post.slug = post_data.get("slug", existing_post.slug)
                existing_post.post_url = post_data.get("link", existing_post.post_url)
                existing_post.status = post_data.get("status", existing_post.status)
                existing_post.featured_image_url = featured_image_url
                existing_post.categories = categories
                existing_post.tags = tags
                existing_post.published_at = published_at
                existing_post.modified_at = modified_at
                existing_post.last_synced_at = datetime.utcnow()
            else:
                new_post = WordPressPost(
                    connection_id=connection.id,
                    user_id=current_user.id,
                    wp_post_id=wp_post_id,
                    title=post_data.get("title", {}).get("rendered", ""),
                    content=post_data.get("content", {}).get("rendered", ""),
                    excerpt=post_data.get("excerpt", {}).get("rendered", ""),
                    slug=post_data.get("slug"),
                    post_url=post_data.get("link"),
                    status=post_data.get("status"),
                    featured_image_url=featured_image_url,
                    categories=categories,
                    tags=tags,
                    published_at=published_at,
                    modified_at=modified_at,
                    last_synced_at=datetime.utcnow()
                )
                db.add(new_post)
                synced_count += 1

        connection.last_synced_at = datetime.utcnow()
        db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync posts: {str(e)}")

    return {"message": "Posts synced successfully", "synced_count": synced_count}


@router.post("/posts/create")
async def create_wordpress_post(
    post_data: WordPressPostCreate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress에 새 게시물 작성
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    auth_header = get_wp_auth_header(connection.wp_username, connection.wp_app_password)

    post_payload = {
        "title": post_data.title,
        "content": post_data.content,
        "status": post_data.status
    }

    if post_data.categories:
        post_payload["categories"] = post_data.categories
    if post_data.tags:
        post_payload["tags"] = post_data.tags
    if post_data.featured_image_id:
        post_payload["featured_media"] = post_data.featured_image_id
    if post_data.excerpt:
        post_payload["excerpt"] = post_data.excerpt

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{connection.site_url}/wp-json/wp/v2/posts",
                json=post_payload,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                }
            )

        if response.status_code not in [200, 201]:
            error_detail = response.json() if response.content else "Unknown error"
            raise HTTPException(status_code=response.status_code, detail=f"Failed to create post: {error_detail}")

        created_post = response.json()

        # DB에 저장
        new_post = WordPressPost(
            connection_id=connection.id,
            user_id=current_user.id,
            wp_post_id=created_post["id"],
            title=created_post.get("title", {}).get("rendered", post_data.title),
            content=created_post.get("content", {}).get("rendered", post_data.content),
            excerpt=created_post.get("excerpt", {}).get("rendered"),
            slug=created_post.get("slug"),
            post_url=created_post.get("link"),
            status=created_post.get("status"),
            last_synced_at=datetime.utcnow()
        )
        db.add(new_post)
        db.commit()

        return {
            "message": "Post created successfully",
            "wp_post_id": created_post["id"],
            "post_url": created_post.get("link"),
            "status": created_post.get("status")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


@router.put("/posts/{wp_post_id}")
async def update_wordpress_post(
    wp_post_id: int,
    post_data: WordPressPostUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 게시물 수정
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    auth_header = get_wp_auth_header(connection.wp_username, connection.wp_app_password)

    post_payload = {}
    if post_data.title is not None:
        post_payload["title"] = post_data.title
    if post_data.content is not None:
        post_payload["content"] = post_data.content
    if post_data.status is not None:
        post_payload["status"] = post_data.status
    if post_data.categories is not None:
        post_payload["categories"] = post_data.categories
    if post_data.tags is not None:
        post_payload["tags"] = post_data.tags
    if post_data.featured_image_id is not None:
        post_payload["featured_media"] = post_data.featured_image_id
    if post_data.excerpt is not None:
        post_payload["excerpt"] = post_data.excerpt

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{connection.site_url}/wp-json/wp/v2/posts/{wp_post_id}",
                json=post_payload,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                }
            )

        if response.status_code != 200:
            error_detail = response.json() if response.content else "Unknown error"
            raise HTTPException(status_code=response.status_code, detail=f"Failed to update post: {error_detail}")

        updated_post = response.json()

        # DB 업데이트
        local_post = db.query(WordPressPost).filter(
            WordPressPost.wp_post_id == wp_post_id,
            WordPressPost.connection_id == connection.id
        ).first()

        if local_post:
            if post_data.title:
                local_post.title = post_data.title
            if post_data.content:
                local_post.content = post_data.content
            if post_data.status:
                local_post.status = post_data.status
            local_post.post_url = updated_post.get("link", local_post.post_url)
            local_post.last_synced_at = datetime.utcnow()
            db.commit()

        return {
            "message": "Post updated successfully",
            "wp_post_id": wp_post_id,
            "post_url": updated_post.get("link")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update post: {str(e)}")


@router.delete("/posts/{wp_post_id}")
async def delete_wordpress_post(
    wp_post_id: int,
    force: bool = Query(False, description="Permanently delete (bypass trash)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 게시물 삭제
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    auth_header = get_wp_auth_header(connection.wp_username, connection.wp_app_password)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{connection.site_url}/wp-json/wp/v2/posts/{wp_post_id}",
                params={"force": str(force).lower()},
                headers={"Authorization": auth_header}
            )

        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=response.status_code, detail="Failed to delete post")

        # DB에서도 삭제
        local_post = db.query(WordPressPost).filter(
            WordPressPost.wp_post_id == wp_post_id,
            WordPressPost.connection_id == connection.id
        ).first()

        if local_post:
            db.delete(local_post)
            db.commit()

        return {"message": "Post deleted successfully", "wp_post_id": wp_post_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")


@router.post("/media/upload")
async def upload_wordpress_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress에 미디어(이미지) 업로드
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    auth_header = get_wp_auth_header(connection.wp_username, connection.wp_app_password)

    try:
        file_content = await file.read()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{connection.site_url}/wp-json/wp/v2/media",
                content=file_content,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": file.content_type or "image/jpeg",
                    "Content-Disposition": f'attachment; filename="{file.filename}"'
                }
            )

        if response.status_code not in [200, 201]:
            error_detail = response.json() if response.content else "Unknown error"
            raise HTTPException(status_code=response.status_code, detail=f"Failed to upload media: {error_detail}")

        media = response.json()

        return {
            "message": "Media uploaded successfully",
            "media_id": media["id"],
            "source_url": media.get("source_url"),
            "media_details": media.get("media_details", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload media: {str(e)}")


@router.get("/analytics")
async def get_wordpress_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    WordPress 기본 분석 데이터
    """
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == current_user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="WordPress connection not found")

    # DB에서 통계 집계
    post_stats = db.query(
        func.count(WordPressPost.id).label("total_posts"),
        func.sum(WordPressPost.comment_count).label("total_comments")
    ).filter(WordPressPost.connection_id == connection.id).first()

    status_counts = db.query(
        WordPressPost.status,
        func.count(WordPressPost.id)
    ).filter(
        WordPressPost.connection_id == connection.id
    ).group_by(WordPressPost.status).all()

    return {
        "site": {
            "name": connection.site_name,
            "url": connection.site_url,
            "post_count": connection.post_count,
            "category_count": connection.category_count
        },
        "posts": {
            "synced_count": post_stats.total_posts or 0,
            "total_comments": post_stats.total_comments or 0,
            "by_status": {status: count for status, count in status_counts}
        }
    }
