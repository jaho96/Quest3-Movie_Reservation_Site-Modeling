"""
CineBook 영화 예매 사이트 - 백엔드
실행: python server.py
접속: http://localhost:3000
테스트 계정: test@cinebook.com / test1234
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, json, time, bcrypt, urllib.request, urllib.parse, threading
from dotenv import load_dotenv
load_dotenv()
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from functools import wraps

app = Flask(__name__, static_folder='public', static_url_path='')

TMDB_API_KEY   = os.environ.get('TMDB_API_KEY', '')
TMDB_IMG_W500  = 'https://image.tmdb.org/t/p/w500'
TMDB_IMG_W1280 = 'https://image.tmdb.org/t/p/w1280'

TMDB_GENRE_MAP = {
    28:'액션', 12:'모험', 16:'애니메이션', 35:'코미디', 80:'범죄',
    99:'다큐멘터리', 18:'드라마', 10751:'가족', 14:'판타지', 36:'역사',
    27:'공포', 10402:'음악', 9648:'미스터리', 10749:'로맨스', 878:'SF',
    53:'스릴러', 10752:'전쟁', 37:'서부',
}

GENRE_GRADIENT = {
    '액션':   'linear-gradient(160deg,#0d1b4b,#b71c1c)',
    '공포':   'linear-gradient(160deg,#0a0a0a,#4a7c4a)',
    'SF':     'linear-gradient(160deg,#3e1f00,#c9a84c)',
    '애니메이션':'linear-gradient(160deg,#1565c0,#e53935)',
    '뮤지컬': 'linear-gradient(160deg,#1a003e,#e91e8c)',
    '드라마':  'linear-gradient(160deg,#1a237e,#4fc3f7)',
    '로맨스':  'linear-gradient(160deg,#880e4f,#f06292)',
    '스릴러':  'linear-gradient(160deg,#1b1b2f,#e94560)',
}


def tmdb_get(path):
    sep = '&' if '?' in path else '?'
    url = f"https://api.themoviedb.org/3{path}{sep}api_key={TMDB_API_KEY}&language=ko-KR"
    with urllib.request.urlopen(url, timeout=8) as resp:
        return json.loads(resp.read())


def fetch_now_playing_movies(limit=6):
    """TMDB 현재 한국 상영작 상위 N편 반환"""
    data     = tmdb_get('/movie/now_playing?region=KR')
    results  = sorted(data.get('results', []), key=lambda x: x['popularity'], reverse=True)[:limit * 2]
    movies   = []
    for m in results:
        if len(movies) >= limit:
            break
        if not m.get('poster_path'):
            continue
        try:
            detail  = tmdb_get(f"/movie/{m['id']}")
            credits = tmdb_get(f"/movie/{m['id']}/credits")

            genres  = [TMDB_GENRE_MAP.get(g['id'], g['name']) for g in detail.get('genres', [])]
            genre   = genres[0] if genres else '드라마'
            cast    = ', '.join(c['name'] for c in credits.get('cast', [])[:4])
            director= next((c['name'] for c in credits.get('crew', []) if c['job'] == 'Director'), '-')
            prods   = [c['name'] for c in detail.get('production_companies', [])[:2]]
            countries = [c['iso_3166_1'] for c in detail.get('production_countries', [])]
            country = '한국' if 'KR' in countries else (detail.get('production_countries') or [{}])[0].get('name', '-')
            runtime = detail.get('runtime') or 120
            booking_rate = round(min(m['popularity'] / 5, 49.9), 1)

            movies.append({
                'original_title':     m['original_title'],
                'title':              m['title'],
                'content':            detail.get('overview') or m.get('overview', ''),
                'summary':            (m.get('overview') or '')[:80],
                'rating':             '15세' if detail.get('adult') else '전체관람가',
                'screening_rating':   '없음',
                'booking_rate':       booking_rate,
                'cum_audience':       m.get('vote_count', 0) * 500,
                'screen_type':        '2D',
                'genre':              genre,
                'runtime':            runtime,
                'release_date':       m.get('release_date', ''),
                'director':           director,
                'cast':               cast,
                'writer':             '-',
                'country':            country,
                'awards':             '',
                'production_company': ', '.join(prods),
                'distributor':        '-',
                'poster':             TMDB_IMG_W500  + m['poster_path'],
                'still_cut':          TMDB_IMG_W1280 + m['backdrop_path'] if m.get('backdrop_path') else '',
            })
            print(f"[TMDB] {m['title']} 로드 완료")
        except Exception as e:
            print(f"[TMDB] {m.get('title')} 실패: {e}")
    return movies
CORS(app)

SECRET_KEY = 'cinebook_secret_2026'
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
DB_PATH = os.path.join(DB_DIR, 'cinebook.db')


# ── DB 헬퍼 ──────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def qall(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]

def qone(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None


# ── 인증 미들웨어 ─────────────────────────────────────

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
        try:
            request.user = pyjwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except pyjwt.ExpiredSignatureError:
            return jsonify({'error': '세션이 만료되었습니다. 다시 로그인해주세요.'}), 401
        except Exception:
            return jsonify({'error': '유효하지 않은 토큰입니다.'}), 401
        return f(*args, **kwargs)
    return decorated


# ── 정적 페이지 ───────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    full = os.path.join('public', path)
    if os.path.isfile(full):
        return send_from_directory('public', path)
    return send_from_directory('public', 'index.html'), 404


# ══════════════════════════════════════════════════════
# 고객 (Customer)
# ══════════════════════════════════════════════════════

@app.route('/api/customers/register', methods=['POST'])
def register():
    d = request.json or {}
    if not d.get('name') or not d.get('email') or not d.get('password'):
        return jsonify({'error': '이름, 이메일, 비밀번호는 필수입니다.'}), 400

    with get_db() as conn:
        if qone(conn, 'SELECT customer_id FROM customer WHERE email=?', [d['email']]):
            return jsonify({'error': '이미 사용 중인 이메일입니다.'}), 409
        hashed = bcrypt.hashpw(d['password'].encode(), bcrypt.gensalt()).decode()
        r = conn.execute(
            "INSERT INTO customer (name,email,password,phone,birth_date,customer_type,status) VALUES (?,?,?,?,?,'회원','정상')",
            [d['name'], d['email'], hashed, d.get('phone'), d.get('birth_date')]
        )
        return jsonify({'message': '회원가입 완료', 'customer_id': r.lastrowid}), 201


@app.route('/api/customers/login', methods=['POST'])
def login():
    d = request.json or {}
    with get_db() as conn:
        customer = qone(conn, "SELECT * FROM customer WHERE email=? AND status='정상'", [d.get('email', '')])
        if not customer or not bcrypt.checkpw(d.get('password', '').encode(), customer['password'].encode()):
            return jsonify({'error': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401
        payload = {
            'customer_id': customer['customer_id'],
            'name': customer['name'],
            'email': customer['email'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }
        token = pyjwt.encode(payload, SECRET_KEY, algorithm='HS256')
        safe = {k: v for k, v in customer.items() if k != 'password'}
        return jsonify({'token': token, 'customer': safe})


@app.route('/api/customers/me', methods=['GET'])
@token_required
def get_me():
    with get_db() as conn:
        c = qone(conn,
            'SELECT customer_id,name,email,phone,birth_date,profile_photo,megamax_id,customer_type,status FROM customer WHERE customer_id=?',
            [request.user['customer_id']])
        return jsonify(c) if c else (jsonify({'error': '사용자 없음'}), 404)


@app.route('/api/customers/me', methods=['PUT'])
@token_required
def update_me():
    d = request.json or {}
    with get_db() as conn:
        conn.execute('UPDATE customer SET name=?,phone=?,birth_date=?,profile_photo=? WHERE customer_id=?',
                     [d.get('name'), d.get('phone'), d.get('birth_date'), d.get('profile_photo'),
                      request.user['customer_id']])
        return jsonify({'message': '수정 완료'})


@app.route('/api/customers/me/password', methods=['PUT'])
@token_required
def change_password():
    d = request.json or {}
    with get_db() as conn:
        customer = qone(conn, 'SELECT password FROM customer WHERE customer_id=?', [request.user['customer_id']])
        if not bcrypt.checkpw(d.get('current_password', '').encode(), customer['password'].encode()):
            return jsonify({'error': '현재 비밀번호가 올바르지 않습니다.'}), 400
        hashed = bcrypt.hashpw(d['new_password'].encode(), bcrypt.gensalt()).decode()
        conn.execute('UPDATE customer SET password=? WHERE customer_id=?', [hashed, request.user['customer_id']])
        return jsonify({'message': '비밀번호 변경 완료'})


@app.route('/api/customers/me', methods=['DELETE'])
@token_required
def withdraw():
    with get_db() as conn:
        conn.execute("UPDATE customer SET status='탈퇴' WHERE customer_id=?", [request.user['customer_id']])
        return jsonify({'message': '탈퇴 처리 완료'})


# ══════════════════════════════════════════════════════
# 영화 (Movie)
# ══════════════════════════════════════════════════════

@app.route('/api/movies', methods=['GET'])
def get_movies():
    genre = request.args.get('genre')
    status = request.args.get('status', '상영중')
    search = request.args.get('search')
    sql = 'SELECT * FROM movie WHERE 1=1'
    params = []
    if status:  sql += ' AND status=?';        params.append(status)
    if genre:   sql += ' AND genre=?';         params.append(genre)
    if search:  sql += ' AND title LIKE ?';    params.append(f'%{search}%')
    sql += ' ORDER BY booking_rate DESC'
    with get_db() as conn:
        return jsonify(qall(conn, sql, params))


@app.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    with get_db() as conn:
        m = qone(conn, 'SELECT * FROM movie WHERE movie_id=?', [movie_id])
        return jsonify(m) if m else (jsonify({'error': '영화를 찾을 수 없습니다.'}), 404)


@app.route('/api/movies/<int:movie_id>/media', methods=['GET'])
def get_movie_media(movie_id):
    with get_db() as conn:
        return jsonify(qall(conn, "SELECT * FROM media WHERE movie_id=? AND status='정상'", [movie_id]))


# ══════════════════════════════════════════════════════
# 극장 (Theater)
# ══════════════════════════════════════════════════════

@app.route('/api/theaters', methods=['GET'])
def get_theaters():
    region = request.args.get('region')
    sql = "SELECT t.*,a.road_address,a.postal_code FROM theater t LEFT JOIN address a ON t.address_id=a.address_id WHERE t.status='운영중'"
    params = []
    if region: sql += ' AND t.region=?'; params.append(region)
    with get_db() as conn:
        return jsonify(qall(conn, sql, params))


@app.route('/api/theaters/<int:theater_id>', methods=['GET'])
def get_theater(theater_id):
    with get_db() as conn:
        t = qone(conn,
            'SELECT t.*,a.road_address,a.detail_address,a.postal_code FROM theater t LEFT JOIN address a ON t.address_id=a.address_id WHERE t.theater_id=?',
            [theater_id])
        return jsonify(t) if t else (jsonify({'error': '극장 없음'}), 404)


@app.route('/api/theaters/<int:theater_id>/screens', methods=['GET'])
def get_theater_screens(theater_id):
    with get_db() as conn:
        return jsonify(qall(conn, "SELECT * FROM screen WHERE theater_id=? AND status='운영중'", [theater_id]))


# ══════════════════════════════════════════════════════
# 상영관 & 좌석 (Screen & Seat)
# ══════════════════════════════════════════════════════

@app.route('/api/screens/<int:screen_id>/seats', methods=['GET'])
def get_screen_seats(screen_id):
    with get_db() as conn:
        return jsonify(qall(conn, 'SELECT * FROM seat WHERE screen_id=? ORDER BY seat_row,seat_col', [screen_id]))


# ══════════════════════════════════════════════════════
# 영화 스케줄 (Movie Schedule)
# ══════════════════════════════════════════════════════

@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    movie_id   = request.args.get('movieId')
    theater_id = request.args.get('theaterId')
    date       = request.args.get('date')
    sql = '''SELECT s.*,m.title as movie_title,m.runtime,m.rating,m.screen_type,
                    t.name as theater_name,t.region
             FROM movie_schedule s
             JOIN movie m ON s.movie_id=m.movie_id
             JOIN theater t ON s.theater_id=t.theater_id
             WHERE 1=1'''
    params = []
    if movie_id:   sql += ' AND s.movie_id=?';   params.append(movie_id)
    if theater_id: sql += ' AND s.theater_id=?'; params.append(theater_id)
    if date:       sql += ' AND s.screen_date=?'; params.append(date)
    sql += ' ORDER BY s.start_time'
    with get_db() as conn:
        return jsonify(qall(conn, sql, params))


@app.route('/api/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    with get_db() as conn:
        s = qone(conn, '''
            SELECT s.*,m.title as movie_title,m.runtime,m.rating,m.screen_type,m.poster,
                   t.name as theater_name,t.region
            FROM movie_schedule s
            JOIN movie m ON s.movie_id=m.movie_id
            JOIN theater t ON s.theater_id=t.theater_id
            WHERE s.schedule_id=?''', [schedule_id])
        return jsonify(s) if s else (jsonify({'error': '스케줄 없음'}), 404)


@app.route('/api/schedules/<int:schedule_id>/reserved-seats', methods=['GET'])
def get_reserved_seats(schedule_id):
    with get_db() as conn:
        reserved = qall(conn, '''
            SELECT t.seat_no FROM ticket t
            JOIN reservation r ON t.reservation_id=r.reservation_id
            WHERE r.schedule_id=? AND r.status != '취소'
        ''', [schedule_id])
        return jsonify([r['seat_no'] for r in reserved])


# ══════════════════════════════════════════════════════
# 예매 (Reservation)
# ══════════════════════════════════════════════════════

@app.route('/api/reservations', methods=['GET'])
@token_required
def get_my_reservations():
    with get_db() as conn:
        result = qall(conn, '''
            SELECT r.*,m.title as movie_title,m.poster,
                   t.name as theater_name,
                   s.screen_date,s.start_time,s.end_time,s.time_slot
            FROM reservation r
            JOIN movie_schedule s ON r.schedule_id=s.schedule_id
            JOIN movie m ON s.movie_id=m.movie_id
            JOIN theater t ON s.theater_id=t.theater_id
            WHERE r.customer_id=?
            ORDER BY r.reservation_date DESC
        ''', [request.user['customer_id']])
        return jsonify(result)


@app.route('/api/reservations/<int:reservation_id>', methods=['GET'])
@token_required
def get_reservation(reservation_id):
    with get_db() as conn:
        res = qone(conn, '''
            SELECT r.*,m.title as movie_title,m.poster,m.runtime,m.rating,
                   t.name as theater_name,t.region,
                   s.screen_date,s.start_time,s.end_time,s.time_slot
            FROM reservation r
            JOIN movie_schedule s ON r.schedule_id=s.schedule_id
            JOIN movie m ON s.movie_id=m.movie_id
            JOIN theater t ON s.theater_id=t.theater_id
            WHERE r.reservation_id=? AND r.customer_id=?
        ''', [reservation_id, request.user['customer_id']])
        if not res:
            return jsonify({'error': '예매를 찾을 수 없습니다.'}), 404
        tickets = qall(conn, 'SELECT * FROM ticket WHERE reservation_id=?', [reservation_id])
        res['tickets'] = tickets
        return jsonify(res)


@app.route('/api/reservations', methods=['POST'])
@token_required
def create_reservation():
    d = request.json or {}
    seats = d.get('seats') or d.get('seat_numbers') or []
    if not d.get('schedule_id') or not seats:
        return jsonify({'error': 'schedule_id와 seats는 필수입니다.'}), 400

    reservation_no = 'CB' + str(int(time.time() * 1000))[-10:]
    today = datetime.now().strftime('%Y-%m-%d')
    viewer_count = len(seats)
    price = d.get('price', 0)
    seat_price = price // viewer_count if viewer_count else 0

    with get_db() as conn:
        r = conn.execute(
            "INSERT INTO reservation (schedule_id,customer_id,reservation_no,reservation_date,viewer_count,viewer_type,price,status) VALUES (?,?,?,?,?,?,?,'예매완료')",
            [d['schedule_id'], request.user['customer_id'], reservation_no, today,
             viewer_count, d.get('viewer_type', '성인'), price]
        )
        res_id = r.lastrowid

        # 예매 상세
        conn.execute(
            "INSERT INTO reservation_detail (reservation_no,reservation_date,viewer_count,viewer_type,price,status) VALUES (?,?,?,?,?,'예매완료')",
            [reservation_no, today, viewer_count, d.get('viewer_type', '성인'), price]
        )

        # 티켓 (좌석별)
        for seat_no in seats:
            conn.execute(
                "INSERT INTO ticket (reservation_id,reservation_date,seat_no,amount,issued_at,ticket_status) VALUES (?,?,?,?,?,'미사용')",
                [res_id, today, seat_no, seat_price, today]
            )

        return jsonify({'reservation_id': res_id, 'reservation_no': reservation_no}), 201


@app.route('/api/reservations/<int:reservation_id>/cancel', methods=['PUT'])
@token_required
def cancel_reservation(reservation_id):
    with get_db() as conn:
        res = qone(conn, 'SELECT * FROM reservation WHERE reservation_id=? AND customer_id=?',
                   [reservation_id, request.user['customer_id']])
        if not res:
            return jsonify({'error': '예매를 찾을 수 없습니다.'}), 404
        if res['status'] == '취소':
            return jsonify({'error': '이미 취소된 예매입니다.'}), 400
        conn.execute("UPDATE reservation SET status='취소' WHERE reservation_id=?", [reservation_id])
        conn.execute("UPDATE ticket SET ticket_status='취소' WHERE reservation_id=?", [reservation_id])
        return jsonify({'message': '취소 완료'})


# ══════════════════════════════════════════════════════
# 결제 (Payment)
# ══════════════════════════════════════════════════════

@app.route('/api/payments', methods=['POST'])
@token_required
def create_payment():
    d = request.json or {}
    if not d.get('reservation_id') or not d.get('pay_method'):
        return jsonify({'error': 'reservation_id, pay_method는 필수입니다.'}), 400
    payment_no = 'PAY' + str(int(time.time() * 1000))[-10:]
    with get_db() as conn:
        res = qone(conn, 'SELECT * FROM reservation WHERE reservation_id=? AND customer_id=?',
                   [d['reservation_id'], request.user['customer_id']])
        if not res:
            return jsonify({'error': '예매를 찾을 수 없습니다.'}), 404
        r = conn.execute(
            "INSERT INTO payment (reservation_id,payment_no,coupon,coupon_type,coupon_status,points,pay_method,card_company,amount,payment_status,payment_type,status) VALUES (?,?,?,?,?,?,?,?,?,'결제완료','결제','결제완료')",
            [d['reservation_id'], payment_no, d.get('coupon'), d.get('coupon_type'),
             '적용' if d.get('coupon') else None, d.get('points', 0),
             d['pay_method'], d.get('card_company'), d.get('amount', 0)]
        )
        return jsonify({'payment_id': r.lastrowid, 'payment_no': payment_no}), 201


@app.route('/api/payments/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(payment_id):
    with get_db() as conn:
        p = qone(conn, '''
            SELECT p.*,r.reservation_no,r.customer_id
            FROM payment p JOIN reservation r ON p.reservation_id=r.reservation_id
            WHERE p.payment_id=?
        ''', [payment_id])
        if not p or p['customer_id'] != request.user['customer_id']:
            return jsonify({'error': '결제 정보를 찾을 수 없습니다.'}), 404
        return jsonify(p)


@app.route('/api/payments/reservation/<int:reservation_id>', methods=['GET'])
@token_required
def get_payment_by_reservation(reservation_id):
    with get_db() as conn:
        p = qone(conn, '''
            SELECT p.* FROM payment p
            JOIN reservation r ON p.reservation_id=r.reservation_id
            WHERE p.reservation_id=? AND r.customer_id=?
        ''', [reservation_id, request.user['customer_id']])
        return jsonify(p)


# ══════════════════════════════════════════════════════
# 티켓 (Ticket)
# ══════════════════════════════════════════════════════

@app.route('/api/tickets', methods=['GET'])
@token_required
def get_my_tickets():
    with get_db() as conn:
        tickets = qall(conn, '''
            SELECT tk.*,r.reservation_no,r.viewer_type,
                   m.title as movie_title,m.poster,
                   th.name as theater_name,
                   s.screen_date,s.start_time,s.end_time
            FROM ticket tk
            JOIN reservation r ON tk.reservation_id=r.reservation_id
            JOIN movie_schedule s ON r.schedule_id=s.schedule_id
            JOIN movie m ON s.movie_id=m.movie_id
            JOIN theater th ON s.theater_id=th.theater_id
            WHERE r.customer_id=? AND r.status != '취소'
            ORDER BY tk.issued_at DESC
        ''', [request.user['customer_id']])
        return jsonify(tickets)


# ══════════════════════════════════════════════════════
# 관람평 (Review) — 모델 상 movie_id FK 없음
# ══════════════════════════════════════════════════════

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    customer_id = request.args.get('customer_id')
    sql = "SELECT r.*,c.name as customer_name FROM review r JOIN customer c ON r.customer_id=c.customer_id WHERE r.status='정상'"
    params = []
    if customer_id: sql += ' AND r.customer_id=?'; params.append(customer_id)
    sql += ' ORDER BY r.created_at DESC'
    with get_db() as conn:
        result = qall(conn, sql, params)
        for r in result:
            if isinstance(r.get('viewing_points'), str):
                try:    r['viewing_points'] = json.loads(r['viewing_points'])
                except: r['viewing_points'] = []
        return jsonify(result)


@app.route('/api/reviews', methods=['POST'])
@token_required
def create_review():
    d = request.json or {}
    if not d.get('content') or d.get('rating') is None:
        return jsonify({'error': '평점과 내용은 필수입니다.'}), 400
    today = datetime.now().strftime('%Y-%m-%d')
    with get_db() as conn:
        r = conn.execute(
            "INSERT INTO review (customer_id,rating,viewing_points,content,likes,created_at,status) VALUES (?,?,?,?,0,?,'정상')",
            [request.user['customer_id'], d['rating'],
             json.dumps(d.get('viewing_points', []), ensure_ascii=False),
             d['content'], today]
        )
        return jsonify({'review_id': r.lastrowid}), 201


@app.route('/api/reviews/<int:review_id>/like', methods=['POST'])
def like_review(review_id):
    with get_db() as conn:
        conn.execute('UPDATE review SET likes=likes+1 WHERE review_id=?', [review_id])
        return jsonify({'message': '좋아요 완료'})


@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
@token_required
def delete_review(review_id):
    with get_db() as conn:
        rev = qone(conn, 'SELECT * FROM review WHERE review_id=?', [review_id])
        if not rev:
            return jsonify({'error': '관람평을 찾을 수 없습니다.'}), 404
        if rev['customer_id'] != request.user['customer_id']:
            return jsonify({'error': '권한이 없습니다.'}), 403
        conn.execute("UPDATE review SET status='삭제' WHERE review_id=?", [review_id])
        return jsonify({'message': '삭제 완료'})


# ══════════════════════════════════════════════════════
# 미디어 (Media)
# ══════════════════════════════════════════════════════

@app.route('/api/media', methods=['GET'])
def get_media():
    movie_id  = request.args.get('movie_id')
    file_type = request.args.get('file_type')
    sql = "SELECT * FROM media WHERE status='정상'"
    params = []
    if movie_id:  sql += ' AND movie_id=?';  params.append(movie_id)
    if file_type: sql += ' AND file_type=?'; params.append(file_type)
    with get_db() as conn:
        return jsonify(qall(conn, sql, params))


@app.route('/api/media', methods=['POST'])
@token_required
def create_media():
    d = request.json or {}
    with get_db() as conn:
        r = conn.execute(
            "INSERT INTO media (movie_id,customer_id,file_name,file_type,url,status,file_size,mime_type) VALUES (?,?,?,?,?,'정상',?,?)",
            [d.get('movie_id'), request.user['customer_id'], d.get('file_name'),
             d.get('file_type'), d.get('url'), d.get('file_size'), d.get('mime_type')]
        )
        return jsonify({'media_id': r.lastrowid}), 201


# ══════════════════════════════════════════════════════
# DB 초기화 & 시드
# ══════════════════════════════════════════════════════

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS address (
            address_id INTEGER PRIMARY KEY AUTOINCREMENT,
            postal_code TEXT, region_code TEXT, detail_address TEXT,
            road_address TEXT, lot_address TEXT
        );
        CREATE TABLE IF NOT EXISTS customer (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            megamax_id TEXT, profile_photo TEXT,
            password TEXT NOT NULL, name TEXT NOT NULL,
            birth_date TEXT, phone TEXT, email TEXT UNIQUE NOT NULL,
            customer_type TEXT DEFAULT '회원', status TEXT DEFAULT '정상'
        );
        CREATE TABLE IF NOT EXISTS movie (
            movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_title TEXT, title TEXT NOT NULL, subtitle TEXT,
            content TEXT, summary TEXT, rating TEXT, screening_rating TEXT,
            booking_rate REAL DEFAULT 0, cum_audience INTEGER DEFAULT 0,
            screen_type TEXT, genre TEXT, runtime INTEGER, release_date TEXT,
            poster TEXT, still_cut TEXT, trailer TEXT,
            director TEXT, cast TEXT, writer TEXT, screenplay TEXT,
            music_direction TEXT, country TEXT, awards TEXT,
            production_company TEXT, distributor TEXT, status TEXT DEFAULT '상영중'
        );
        CREATE TABLE IF NOT EXISTS theater (
            theater_id INTEGER PRIMARY KEY AUTOINCREMENT,
            address_id INTEGER REFERENCES address(address_id),
            region TEXT, name TEXT NOT NULL, info TEXT,
            transport TEXT, parking TEXT, manager TEXT, manager_phone TEXT,
            facilities TEXT, status TEXT DEFAULT '운영중', screen_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS screen (
            screen_id INTEGER PRIMARY KEY AUTOINCREMENT,
            theater_id INTEGER REFERENCES theater(theater_id),
            classification TEXT, screen_number INTEGER, floor INTEGER,
            seat_count INTEGER, manager TEXT, manager_phone TEXT,
            status TEXT DEFAULT '운영중'
        );
        CREATE TABLE IF NOT EXISTS seat (
            seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            screen_id INTEGER REFERENCES screen(screen_id),
            seat_number TEXT, seat_row TEXT, seat_col INTEGER,
            seat_type TEXT, seat_status TEXT DEFAULT '정상'
        );
        CREATE TABLE IF NOT EXISTS movie_schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            theater_id INTEGER REFERENCES theater(theater_id),
            movie_id INTEGER REFERENCES movie(movie_id),
            screen_date TEXT, start_time TEXT, end_time TEXT,
            time_slot TEXT, round INTEGER, status TEXT DEFAULT '상영예정'
        );
        CREATE TABLE IF NOT EXISTS reservation (
            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER REFERENCES movie_schedule(schedule_id),
            customer_id INTEGER REFERENCES customer(customer_id),
            reservation_no TEXT UNIQUE, reservation_date TEXT,
            viewer_count INTEGER, viewer_type TEXT, price INTEGER,
            status TEXT DEFAULT '예매완료'
        );
        CREATE TABLE IF NOT EXISTS reservation_detail (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_no TEXT, reservation_date TEXT,
            viewer_count INTEGER, viewer_type TEXT,
            price INTEGER, status TEXT DEFAULT '예매완료'
        );
        CREATE TABLE IF NOT EXISTS payment (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER REFERENCES reservation(reservation_id),
            payment_no TEXT UNIQUE, coupon TEXT, coupon_type TEXT, coupon_status TEXT,
            points INTEGER DEFAULT 0, pay_method TEXT, card_company TEXT,
            amount INTEGER, payment_status TEXT DEFAULT '결제완료',
            payment_type TEXT DEFAULT '결제', status TEXT DEFAULT '결제완료'
        );
        CREATE TABLE IF NOT EXISTS ticket (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER REFERENCES reservation(reservation_id),
            reservation_date TEXT, seat_no TEXT, amount INTEGER,
            issued_at TEXT, ticket_status TEXT DEFAULT '미사용'
        );
        CREATE TABLE IF NOT EXISTS review (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customer(customer_id),
            rating INTEGER, viewing_points TEXT, content TEXT,
            likes INTEGER DEFAULT 0, created_at TEXT, status TEXT DEFAULT '정상'
        );
        CREATE TABLE IF NOT EXISTS media (
            media_id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER REFERENCES movie(movie_id),
            customer_id INTEGER REFERENCES customer(customer_id),
            file_name TEXT, file_type TEXT, url TEXT,
            status TEXT DEFAULT '정상', file_size INTEGER, mime_type TEXT
        );
    ''')

    if conn.execute('SELECT COUNT(*) FROM movie').fetchone()[0] == 0:
        seed_db(conn)
    conn.close()
    print('[OK] DB 초기화 완료')


def seed_db(conn):
    def addr(p, r, d, road, lot):
        return conn.execute('INSERT INTO address (postal_code,region_code,detail_address,road_address,lot_address) VALUES (?,?,?,?,?)',
                            [p,r,d,road,lot]).lastrowid

    a1 = addr('06234','강남구','지하 1층','서울 강남구 강남대로 438','서울 강남구 역삼동 832')
    a2 = addr('04066','마포구','2층','서울 마포구 양화로 188','서울 마포구 동교동 147-3')
    a3 = addr('48095','해운대구','3층','부산 해운대구 마린시티 2로 33','부산 해운대구 우동 725')
    a4 = addr('41940','중구','2층','대구 중구 중앙대로 407','대구 중구 동성로 2-3')
    a5 = addr('21577','부평구','5층','인천 부평구 부평대로 33','인천 부평구 부평동 555')

    # ── 영화: TMDB 현재 상영작 or 폴백 ──────────────────
    tmdb_movies = []
    if TMDB_API_KEY:
        print('[TMDB] 현재 상영 중인 영화 가져오는 중...')
        tmdb_movies = fetch_now_playing_movies(limit=6)

    if not tmdb_movies:
        print('[TMDB] API 키 없음 또는 실패 - 기본 영화 데이터 사용')
        tmdb_movies = [
            {'original_title':'Veteran 2','title':'베테랑 2','content':'광역수사대 형사 서도철이 또다시 거대한 악과 맞닥뜨린다.','summary':'정의로운 형사의 두 번째 이야기','rating':'15세','screening_rating':'폭력성','booking_rate':32.5,'cum_audience':7630000,'screen_type':'2D','genre':'액션','runtime':109,'release_date':'2024-09-13','director':'류승완','cast':'황정민, 정해인, 오달수','writer':'류승완','country':'한국','awards':'2024 청룡영화상 최우수작품상','production_company':'외유내강','distributor':'CJ ENM','poster':'linear-gradient(160deg,#0d1b4b,#b71c1c)','still_cut':''},
            {'original_title':'Inside Out 2','title':'인사이드 아웃 2','content':'라일리의 새로운 감정들이 등장하면서 벌어지는 이야기.','summary':'새로운 감정 불안과 함께하는 성장 이야기','rating':'전체관람가','screening_rating':'없음','booking_rate':18.2,'cum_audience':5900000,'screen_type':'2D/3D','genre':'애니메이션','runtime':100,'release_date':'2024-06-12','director':'Kelsey Mann','cast':'에이미 포얼러, 마야 호크','writer':'Dave Holstein','country':'미국','awards':'','production_company':'픽사','distributor':'월트디즈니','poster':'linear-gradient(160deg,#1565c0,#e53935)','still_cut':''},
            {'original_title':'Exhuma','title':'파묘','content':'거액의 의뢰를 받은 무당과 장의사가 수상한 묫자리를 이장하면서 벌어지는 이야기.','summary':'이장 작업에서 시작된 기이한 사건들','rating':'15세','screening_rating':'공포','booking_rate':8.1,'cum_audience':11920000,'screen_type':'2D','genre':'공포','runtime':134,'release_date':'2024-02-22','director':'장재현','cast':'최민식, 유해진, 김고은, 이도현','writer':'장재현','country':'한국','awards':'2024 대종상 최우수작품상','production_company':'쇼박스','distributor':'쇼박스','poster':'linear-gradient(160deg,#0a0a0a,#4a7c4a)','still_cut':''},
            {'original_title':'Dune: Part Two','title':'듄: 파트 2','content':'폴 아트레이데스는 프레멘의 예언자로 거듭나 황제에게 복수를 시작한다.','summary':'폴의 복수와 예언자로서의 여정','rating':'12세','screening_rating':'없음','booking_rate':12.3,'cum_audience':4200000,'screen_type':'2D/3D/IMAX','genre':'SF','runtime':165,'release_date':'2024-02-28','director':'드니 빌뇌브','cast':'티모시 샬라메, 젠데이아','writer':'드니 빌뇌브','country':'미국','awards':'2024 아카데미 최우수촬영상','production_company':'레전더리','distributor':'워너브라더스','poster':'linear-gradient(160deg,#3e1f00,#c9a84c)','still_cut':''},
            {'original_title':'Hijack 1971','title':'하이재킹','content':'1971년 실화 기반 항공기 납치 사건.','summary':'1971년 실화 기반 납치 사건','rating':'15세','screening_rating':'폭력성','booking_rate':15.7,'cum_audience':3100000,'screen_type':'2D','genre':'액션','runtime':100,'release_date':'2024-06-21','director':'류승완','cast':'하정우, 여진구, 성동일','writer':'류승완','country':'한국','awards':'','production_company':'외유내강','distributor':'CJ ENM','poster':'linear-gradient(160deg,#0d2137,#4a90d9)','still_cut':''},
            {'original_title':'Wicked','title':'위키드','content':'오즈의 마법사 이전 이야기. 두 마녀의 우정과 갈등.','summary':'두 마녀의 우정과 갈등','rating':'전체관람가','screening_rating':'없음','booking_rate':22.4,'cum_audience':890000,'screen_type':'2D','genre':'뮤지컬','runtime':160,'release_date':'2024-11-22','director':'존 M. 추','cast':'신시아 에리보, 아리아나 그란데','writer':'위닌 홀즈만','country':'미국','awards':'','production_company':'유니버설','distributor':'유니버설','poster':'linear-gradient(160deg,#1a003e,#e91e8c)','still_cut':''},
        ]

    movie_ids = []
    for md in tmdb_movies:
        mid = conn.execute('''INSERT INTO movie
            (original_title,title,content,summary,rating,screening_rating,booking_rate,cum_audience,
             screen_type,genre,runtime,release_date,director,cast,writer,country,awards,
             production_company,distributor,status,poster,still_cut)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,"상영중",?,?)''',
            [md['original_title'],md['title'],md['content'],md['summary'],md['rating'],
             md['screening_rating'],md['booking_rate'],md['cum_audience'],md['screen_type'],
             md['genre'],md['runtime'],md['release_date'],md['director'],md['cast'],
             md['writer'],md['country'],md['awards'],md['production_company'],
             md['distributor'],md['poster'],md['still_cut']]).lastrowid
        movie_ids.append((mid, md['runtime']))

    def theater(addr_id, region, name, info, transport, parking, manager, phone, screen_cnt):
        return conn.execute('INSERT INTO theater (address_id,region,name,info,transport,parking,manager,manager_phone,status,screen_count) VALUES (?,?,?,?,?,?,?,?,"운영중",?)',
                            [addr_id,region,name,info,transport,parking,manager,phone,screen_cnt]).lastrowid

    t1 = theater(a1,'서울','CGV 강남','강남역 근처 프리미엄 극장','지하철 2호선 강남역 11번 출구','2시간 무료','홍길동','02-123-4567',8)
    t2 = theater(a2,'서울','CGV 홍대','홍대입구역 CGV','지하철 2호선 홍대입구역 9번 출구','1시간 무료','김철수','02-234-5678',6)
    t3 = theater(a3,'부산','CGV 부산해운대','해운대 마린시티 CGV','지하철 2호선 해운대역 3번 출구','2시간 무료','박영희','051-345-6789',7)
    t4 = theater(a4,'대구','CGV 대구동성로','동성로 CGV 프리미엄','지하철 1호선 중앙로역','제한 없음','이민수','053-456-7890',5)
    t5 = theater(a5,'인천','CGV 인천','인천 CGV','지하철 1호선 부평역','2시간 무료','최지은','032-567-8901',6)

    def screen(t_id, cls, num, floor, seats):
        return conn.execute('INSERT INTO screen (theater_id,classification,screen_number,floor,seat_count,status) VALUES (?,?,?,?,?,"운영중")',
                            [t_id,cls,num,floor,seats]).lastrowid

    sc1 = screen(t1,'일반관',1,3,150); sc2 = screen(t1,'특별관',2,4,80); sc3 = screen(t1,'IMAX',3,5,200)
    sc4 = screen(t2,'일반관',1,2,120); sc5 = screen(t2,'특별관',2,3,90)
    sc6 = screen(t3,'일반관',1,2,130); sc7 = screen(t4,'일반관',1,2,140); sc8 = screen(t5,'일반관',1,2,120)

    reserved_set = {'B3','C5','D2','D7','E1','F4','F5','G8','H3','H9'}
    for sc_id in [sc1,sc2,sc3,sc4,sc5,sc6,sc7,sc8]:
        for row_ch in 'ABCDEFGHIJ':
            for col in range(1,11):
                sn = f'{row_ch}{col}'
                st = '특별석' if row_ch=='A' else ('장애인석' if row_ch=='J' else '일반')
                ss = '예약완료' if sn in reserved_set else '정상'
                conn.execute('INSERT INTO seat (screen_id,seat_number,seat_row,seat_col,seat_type,seat_status) VALUES (?,?,?,?,?,?)',
                             [sc_id,sn,row_ch,col,st,ss])

    def sch(t_id, m_id, date, start, end, slot, rnd):
        conn.execute('INSERT INTO movie_schedule (theater_id,movie_id,screen_date,start_time,end_time,time_slot,round,status) VALUES (?,?,?,?,?,?,?,"상영예정")',
                     [t_id,m_id,date,start,end,slot,rnd])

    def calc_end(start, runtime):
        h, m = map(int, start.split(':'))
        total = h * 60 + m + runtime + 20
        return f"{(total//60)%24:02d}:{total%60:02d}"

    all_theaters = [t1, t2, t3, t4, t5]
    time_slots   = [('09:00','조조'),('12:00','일반'),('15:00','일반'),('18:30','일반'),('21:00','심야')]
    today        = datetime.now()
    dates        = [(today.replace(hour=0,minute=0,second=0,microsecond=0) +
                     timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]

    for date in dates:
        for theater in all_theaters:
            for idx, (mid, rt) in enumerate(movie_ids):
                s1, slot1 = time_slots[idx % len(time_slots)]
                s2, slot2 = time_slots[(idx + 2) % len(time_slots)]
                sch(theater, mid, date, s1, calc_end(s1, rt), slot1, 1)
                sch(theater, mid, date, s2, calc_end(s2, rt), slot2, 2)

    hashed = bcrypt.hashpw('test1234'.encode(), bcrypt.gensalt()).decode()
    conn.execute("INSERT INTO customer (name,email,password,phone,birth_date,customer_type,status) VALUES ('김민준','test@cinebook.com',?,?,?,'회원','정상')",
                 [hashed,'010-1234-5678','1995-03-15'])
    conn.commit()
    print('[OK] 시드 데이터 삽입 완료')
    print('     테스트 계정: test@cinebook.com / test1234')


def ensure_schedules():
    """모든 상영중 영화에 오늘~14일치 스케줄이 없으면 추가"""
    conn = get_db()
    try:
        movies   = qall(conn, "SELECT movie_id, runtime FROM movie WHERE status='상영중'")
        theaters = [r['theater_id'] for r in qall(conn, 'SELECT theater_id FROM theater')]
        today    = datetime.now()
        dates    = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]
        slots    = [('09:00','조조'),('12:00','일반'),('15:00','일반'),('18:30','일반'),('21:00','심야')]

        def calc_end(start, rt):
            h, m = map(int, start.split(':'))
            total = h * 60 + m + rt + 20
            return f"{(total//60)%24:02d}:{total%60:02d}"

        added = 0
        for mid_row in movies:
            mid, rt = mid_row['movie_id'], mid_row['runtime'] or 120
            idx = mid % len(slots)
            for tid in theaters:
                for date in dates:
                    exists = conn.execute(
                        'SELECT 1 FROM movie_schedule WHERE movie_id=? AND theater_id=? AND screen_date=?',
                        [mid, tid, date]).fetchone()
                    if not exists:
                        s1, slot1 = slots[idx % len(slots)]
                        s2, slot2 = slots[(idx + 2) % len(slots)]
                        conn.execute('INSERT INTO movie_schedule (theater_id,movie_id,screen_date,start_time,end_time,time_slot,round,status) VALUES (?,?,?,?,?,?,?,"상영예정")',
                                     [tid, mid, date, s1, calc_end(s1, rt), slot1, 1])
                        conn.execute('INSERT INTO movie_schedule (theater_id,movie_id,screen_date,start_time,end_time,time_slot,round,status) VALUES (?,?,?,?,?,?,?,"상영예정")',
                                     [tid, mid, date, s2, calc_end(s2, rt), slot2, 2])
                        added += 2
        conn.commit()
        if added:
            print(f'[Schedule] {added}개 스케줄 추가됨')
    finally:
        conn.close()


def refresh_movies_from_tmdb():
    """TMDB now_playing으로 영화 목록 갱신 (추가/업데이트/상영종료)"""
    if not TMDB_API_KEY:
        return
    print('[TMDB] 영화 데이터 자동 갱신 시작...')
    try:
        new_movies = fetch_now_playing_movies(limit=6)
        if not new_movies:
            return

        conn = get_db()
        existing = {r['original_title']: r['movie_id']
                    for r in qall(conn, 'SELECT movie_id, original_title FROM movie')}
        new_titles = {md['original_title'] for md in new_movies}

        for md in new_movies:
            if md['original_title'] in existing:
                mid = existing[md['original_title']]
                conn.execute('''UPDATE movie SET poster=?,still_cut=?,booking_rate=?,
                                cum_audience=?,content=?,status='상영중' WHERE movie_id=?''',
                             [md['poster'],md['still_cut'],md['booking_rate'],
                              md['cum_audience'],md['content'],mid])
            else:
                conn.execute('''INSERT INTO movie
                    (original_title,title,content,summary,rating,screening_rating,booking_rate,
                     cum_audience,screen_type,genre,runtime,release_date,director,cast,writer,
                     country,awards,production_company,distributor,status,poster,still_cut)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'상영중',?,?)''',
                    [md['original_title'],md['title'],md['content'],md['summary'],md['rating'],
                     md['screening_rating'],md['booking_rate'],md['cum_audience'],md['screen_type'],
                     md['genre'],md['runtime'],md['release_date'],md['director'],md['cast'],
                     md['writer'],md['country'],md['awards'],md['production_company'],
                     md['distributor'],md['poster'],md['still_cut']])
                print(f'[TMDB] 새 영화 추가: {md["title"]}')

        # now_playing에 없는 영화는 상영종료 처리
        for orig, mid in existing.items():
            if orig not in new_titles:
                conn.execute("UPDATE movie SET status='상영종료' WHERE movie_id=?", [mid])
                print(f'[TMDB] 상영종료 처리: {orig}')

        conn.commit()
        conn.close()
        ensure_schedules()
        print('[TMDB] 자동 갱신 완료')
    except Exception as e:
        print(f'[TMDB] 자동 갱신 실패: {e}')


def auto_refresh_worker():
    """24시간마다 영화 데이터 + 스케줄 자동 갱신"""
    while True:
        time.sleep(24 * 60 * 60)
        refresh_movies_from_tmdb()
        ensure_schedules()


def fetch_tmdb_posters():
    if not TMDB_API_KEY:
        print('[TMDB] API 키 없음 - 포스터 업데이트 건너뜀')
        return
    conn = get_db()
    movies = qall(conn, "SELECT movie_id, title, original_title, release_date FROM movie WHERE poster NOT LIKE 'http%' OR poster IS NULL OR poster = ''")
    updated = 0
    for m in movies:
        try:
            query = urllib.parse.quote(m['original_title'] or m['title'])
            year  = (m['release_date'] or '')[:4]
            url   = (f"https://api.themoviedb.org/3/search/movie"
                     f"?api_key={TMDB_API_KEY}&query={query}&language=ko-KR&year={year}")
            with urllib.request.urlopen(url, timeout=5) as resp:
                results = json.loads(resp.read()).get('results', [])
            if not results:
                # 연도 없이 재시도
                url2 = (f"https://api.themoviedb.org/3/search/movie"
                        f"?api_key={TMDB_API_KEY}&query={query}&language=ko-KR")
                with urllib.request.urlopen(url2, timeout=5) as resp:
                    results = json.loads(resp.read()).get('results', [])
            if results:
                r        = results[0]
                poster   = TMDB_IMG_W500  + r['poster_path']   if r.get('poster_path')   else None
                backdrop = TMDB_IMG_W1280 + r['backdrop_path'] if r.get('backdrop_path') else None
                if poster:
                    conn.execute("UPDATE movie SET poster=?, still_cut=? WHERE movie_id=?",
                                 [poster, backdrop, m['movie_id']])
                    updated += 1
                    print(f"[TMDB] {m['title']} 포스터 업데이트 완료")
        except Exception as e:
            print(f"[TMDB] {m['title']} 실패: {e}")
    conn.commit()
    conn.close()
    print(f'[TMDB] 총 {updated}개 영화 포스터 업데이트 완료')


if __name__ == '__main__':
    print('[CineBook] 서버 시작 중...')
    init_db()
    fetch_tmdb_posters()
    ensure_schedules()
    if TMDB_API_KEY:
        t = threading.Thread(target=auto_refresh_worker, daemon=True)
        t.start()
        print('[TMDB] 24시간 자동 갱신 활성화')
    print('[CineBook] http://127.0.0.1:3000 에서 접속하세요')
    app.run(host='0.0.0.0', port=3000, debug=False)
