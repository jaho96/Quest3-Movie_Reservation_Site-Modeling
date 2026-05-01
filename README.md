# CineBook - 영화 예매 사이트

DB 모델링을 기반으로 구현한 풀스택 영화 예매 웹 애플리케이션입니다.

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.13 + Flask + Flask-CORS |
| Database | SQLite3 |
| Auth | JWT (PyJWT) + bcrypt |
| Frontend | Vanilla HTML/CSS/JavaScript |

---

## 프로젝트 구조

```
movie-booking/
├── server.py           # Flask 백엔드 (API + 정적 파일 서빙)
├── start.bat           # 서버 시작 스크립트 (Windows)
├── db/
│   └── cinebook.db     # SQLite 데이터베이스 (자동 생성)
└── public/             # 프론트엔드 정적 파일
    ├── index.html      # 메인 (영화 목록)
    ├── detail.html     # 영화 상세
    ├── booking.html    # 예매
    ├── payment.html    # 결제
    ├── mypage.html     # 마이페이지
    ├── css/
    │   └── style.css   # 공통 스타일
    └── js/
        └── api.js      # API 헬퍼 + 인증 공통 로직
```

---

## 실행 방법

### 요구사항

- Python 3.13 이상
- pip 패키지: `flask`, `flask-cors`, `PyJWT`, `bcrypt`

### 패키지 설치

```bash
C:\Python313\python.exe -m pip install flask flask-cors PyJWT bcrypt
```

### 서버 시작

```bash
cd movie-booking
C:\Python313\python.exe server.py
```

또는 `start.bat` 더블클릭

### 접속

> **http://127.0.0.1:3000**
>
> ⚠️ `localhost` 대신 `127.0.0.1` 사용 (WSL 환경에서 localhost가 IPv6로 라우팅되는 문제)

---

## 테스트 계정

| 이메일 | 비밀번호 |
|--------|----------|
| test@cinebook.com | test1234 |

---

## DB 스키마 (13개 테이블)

```
address            주소
customer           회원
movie              영화
theater            극장
screen             상영관
seat               좌석
movie_schedule     상영 일정
reservation        예매
reservation_detail 예매 상세
ticket             티켓
payment            결제
review             관람평
media              미디어 (예고편 등)
```

### 모델링 한계 및 우회 처리

| 한계 | 우회 방법 |
|------|-----------|
| `movie_schedule`에 `screen_id` 없음 | 좌석 조회 시 해당 극장의 첫 번째 상영관 사용 |
| `review`에 `movie_id` 없음 | 영화 상세 페이지에서 전체 관람평 표시 |

---

## API 엔드포인트

### 인증
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/customers/register` | 회원가입 |
| POST | `/api/customers/login` | 로그인 (JWT 발급) |
| GET | `/api/customers/me` | 내 정보 조회 🔒 |
| PUT | `/api/customers/me` | 내 정보 수정 🔒 |
| PUT | `/api/customers/me/password` | 비밀번호 변경 🔒 |
| DELETE | `/api/customers/me` | 회원 탈퇴 🔒 |

### 영화
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/movies` | 영화 목록 (status, genre, search 필터) |
| GET | `/api/movies/:id` | 영화 상세 |
| GET | `/api/movies/:id/media` | 영화 미디어 |

### 극장 / 상영관 / 좌석
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/theaters` | 극장 목록 (region 필터) |
| GET | `/api/theaters/:id` | 극장 상세 |
| GET | `/api/theaters/:id/screens` | 극장 상영관 목록 |
| GET | `/api/screens/:id/seats` | 상영관 좌석 목록 |

### 상영 일정
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/schedules` | 상영 일정 (movieId, theaterId, date 필터) |
| GET | `/api/schedules/:id` | 일정 상세 |
| GET | `/api/schedules/:id/reserved-seats` | 예약된 좌석 번호 목록 |

### 예매 / 결제 / 티켓
| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/reservations` | 예매 생성 🔒 |
| GET | `/api/reservations` | 내 예매 내역 🔒 |
| GET | `/api/reservations/:id` | 예매 상세 🔒 |
| PUT | `/api/reservations/:id/cancel` | 예매 취소 🔒 |
| POST | `/api/payments` | 결제 처리 🔒 |
| GET | `/api/payments/:id` | 결제 조회 🔒 |
| GET | `/api/tickets` | 내 티켓 목록 🔒 |

### 관람평 / 미디어
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/reviews` | 관람평 목록 |
| POST | `/api/reviews` | 관람평 작성 🔒 |
| POST | `/api/reviews/:id/like` | 좋아요 🔒 |
| DELETE | `/api/reviews/:id` | 관람평 삭제 🔒 |
| GET | `/api/media` | 미디어 목록 |

> 🔒 = JWT 인증 필요 (Authorization: Bearer {token})

---

## 주요 기능

### 메인 페이지 (`index.html`)
- 상영 중인 영화 목록 (예매율 순 정렬)
- 장르 필터 (전체 / 액션 / 애니메이션 / 공포 / SF / 뮤지컬)
- 극장 안내

### 영화 상세 (`detail.html`)
- 영화 정보, 출연진, 수상 이력
- 관람평 (작성 / 좋아요 / 삭제)
- 상영 일정 (날짜별)
- 미디어

### 예매 (`booking.html`)
4단계 플로우:
1. 영화 선택
2. 극장 + 날짜 + 시간 선택
3. 좌석 선택 (일반석 / 특별석, 실시간 예약 현황 반영)
4. 결제 페이지 이동

### 결제 (`payment.html`)
- 결제 수단 선택 (신용카드 / 체크카드 / 카카오페이 / 네이버페이)
- 예매 생성 → 결제 처리 순차 API 호출
- 예매 번호 발급 완료 모달

### 마이페이지 (`mypage.html`)
- 예매 내역 조회 / 취소
- 나의 티켓 목록
- 나의 관람평 조회 / 삭제
- 기본 정보 수정 / 비밀번호 변경 / 회원 탈퇴

---

## 시드 데이터

서버 최초 실행 시 자동으로 샘플 데이터가 삽입됩니다.

- 영화 6편 (베테랑 2, 인사이드 아웃 2, 파묘, 듄: 파트 2, 하이재킹, 위키드)
- 극장 5개 (CGV 강남, CGV 홍대, CGV 부산해운대, CGV 대구동성로, CGV 인천)
- 상영 일정: 6개 영화 × 5개 극장 × 7일 × 2회
- 테스트 계정 1개

---

## 포스터 이미지

현재 장르별 CSS 그라디언트로 표시됩니다.
TMDB API 키 발급 후 `server.py`의 각 영화 `poster` 필드를 실제 이미지 URL로 교체하면 실제 포스터 사용 가능합니다.

```python
# server.py seed_db() 내부 - poster= 값을 URL로 교체
m1 = movie(..., poster='https://image.tmdb.org/t/p/w500/{poster_path}')
```
