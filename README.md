# CineBook - 영화 예매 사이트

DB 모델링을 기반으로 구현한 풀스택 영화 예매 웹 애플리케이션입니다.  
TMDB API와 연동하여 실제 현재 상영작 데이터를 24시간마다 자동으로 갱신합니다.

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.13 + Flask + Flask-CORS |
| Database | SQLite3 |
| Auth | JWT (PyJWT) + bcrypt |
| Frontend | Vanilla HTML / CSS / JavaScript |
| 영화 데이터 | TMDB API (자동 갱신) |
| 환경변수 | python-dotenv |

---

## 프로젝트 구조

```
movie-booking/
├── server.py           # Flask 백엔드 (API + 정적 파일 서빙)
├── start.bat           # 서버 시작 스크립트 (Windows 더블클릭)
├── .env                # 환경변수 (TMDB_API_KEY) - git 제외
├── db/
│   └── cinebook.db     # SQLite DB (서버 최초 실행 시 자동 생성)
└── public/             # 프론트엔드
    ├── index.html      # 메인 (영화 목록)
    ├── detail.html     # 영화 상세
    ├── booking.html    # 예매
    ├── payment.html    # 결제
    ├── mypage.html     # 마이페이지
    ├── css/
    │   └── style.css
    └── js/
        └── api.js      # API 헬퍼 + 인증 공통 로직
```

---

## 실행 방법

### 1. 패키지 설치

```bash
C:\Python313\python.exe -m pip install flask flask-cors PyJWT bcrypt python-dotenv
```

### 2. 환경변수 설정

프로젝트 루트에 `.env` 파일 생성:

```
TMDB_API_KEY=발급받은_키_입력
```

> TMDB API 키: [themoviedb.org](https://www.themoviedb.org/) 회원가입 → 설정 → API → 무료 발급  
> `.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.

### 3. 서버 시작

```bash
cd movie-booking
C:\Python313\python.exe server.py
```

또는 `start.bat` 더블클릭

### 4. 브라우저 접속

```
http://127.0.0.1:3000
```

> ⚠️ `localhost` 대신 `127.0.0.1` 사용  
> (WSL 환경에서 localhost가 IPv6로 라우팅되어 접속 불가)

---

## 테스트 계정

| 이메일 | 비밀번호 |
|--------|----------|
| test@cinebook.com | test1234 |

---

## 주요 기능

### 메인 페이지
- TMDB 현재 상영작 목록 (예매율 순 정렬)
- 장르 필터 (전체 / 액션 / 애니메이션 / 공포 / SF / 뮤지컬)
- 극장 안내

### 영화 상세
- TMDB 배경 이미지 히어로
- 영화 정보 (줄거리 / 출연진 / 감독 / 수상 이력)
- 관람평 (작성 / 좋아요 / 삭제)
- 날짜별 상영 일정
- 미디어

### 예매 (4단계 플로우)
1. 영화 선택
2. 극장 + 날짜 + 시간 선택
3. 좌석 선택 (일반석 / 특별석 / 장애인석, 실시간 예약 현황 반영)
4. 결제 페이지 이동

### 결제
- 결제 수단 선택 (신용카드 / 체크카드 / 카카오페이 / 네이버페이)
- 예매 생성 → 결제 처리 순차 API 호출
- 예매 번호 발급 완료 모달

### 마이페이지
- 예매 내역 조회 / 취소
- 나의 티켓 목록
- 나의 관람평 조회 / 삭제
- 기본 정보 수정 / 비밀번호 변경 / 회원 탈퇴

---

## TMDB 자동 갱신

서버 시작 시 TMDB `now_playing` API로 한국 현재 상영작 6편을 가져오고, 이후 **24시간마다 백그라운드에서 자동 갱신**합니다.

| 상황 | 처리 |
|------|------|
| 새 영화 등장 | DB 추가 + 14일치 스케줄 생성 |
| 기존 영화 업데이트 | 포스터 / 예매율 / 줄거리 갱신 |
| 내려간 영화 | `상영종료` 처리 (예매 데이터 보존) |
| 서버 시작 시 | 오늘 기준 14일치 스케줄 자동 보충 |

영화 목록을 즉시 초기화하려면 `db/cinebook.db`를 삭제하고 서버를 재시작하세요.

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
media              미디어
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
| GET | `/api/movies/:id/media` | 미디어 |

### 극장 / 상영관 / 좌석
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/theaters` | 극장 목록 (region 필터) |
| GET | `/api/theaters/:id` | 극장 상세 |
| GET | `/api/theaters/:id/screens` | 상영관 목록 |
| GET | `/api/screens/:id/seats` | 좌석 목록 |

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

> 🔒 = JWT 인증 필요 (`Authorization: Bearer {token}`)

---

## 시드 데이터

서버 최초 실행 시 자동 삽입되는 데이터:

- 극장 5개 (CGV 강남 / CGV 홍대 / CGV 부산해운대 / CGV 대구동성로 / CGV 인천)
- 상영관 8개 (일반관 / 특별관 / IMAX)
- 좌석 각 상영관 A~J × 1~10 (100석)
- 영화: TMDB 한국 현재 상영작 6편 (API 키 없을 시 기본 6편)
- 상영 일정: 오늘 기준 14일 × 전 극장 × 1일 2회
- 테스트 계정 1개
