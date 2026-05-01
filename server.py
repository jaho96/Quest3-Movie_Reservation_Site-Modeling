"""
CineBook 영화 예매 사이트 - 백엔드
실행: python server.py
접속: http://localhost:3000
테스트 계정: test@cinebook.com / test1234
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, json, time, bcrypt
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from functools import wraps

app = Flask(__name__, static_folder='public', static_url_path='')
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

    def movie(orig, title, content, summary, rating, scr_rating, book_rate, cum_aud,
              scr_type, genre, runtime, release, director, cast_, writer, country, awards, prod, dist, poster=''):
        return conn.execute('''INSERT INTO movie
            (original_title,title,content,summary,rating,screening_rating,booking_rate,cum_audience,
             screen_type,genre,runtime,release_date,director,cast,writer,country,awards,
             production_company,distributor,status,poster)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,"상영중",?)''',
            [orig,title,content,summary,rating,scr_rating,book_rate,cum_aud,
             scr_type,genre,runtime,release,director,cast_,writer,country,awards,prod,dist,poster]).lastrowid

    m1 = movie('Veteran 2','베테랑 2','광역수사대 형사 서도철이 또다시 거대한 악과 맞닥뜨린다.','정의로운 형사의 두 번째 이야기','15세','폭력성',32.5,7630000,'2D','액션',109,'2024-09-13','류승완','황정민, 정해인, 오달수','류승완','한국','2024 청룡영화상 최우수작품상','외유내강','CJ ENM',
              poster='linear-gradient(160deg,#0d1b4b 0%,#1a3a7a 50%,#b71c1c 100%)')
    m2 = movie('Inside Out 2','인사이드 아웃 2','라일리의 새로운 감정들이 등장하면서 벌어지는 이야기.','새로운 감정 불안과 함께하는 라일리의 성장 이야기','전체관람가','없음',18.2,5900000,'2D/3D','애니메이션',100,'2024-06-12','Kelsey Mann','에이미 포얼러, 마야 호크','Dave Holstein','미국','','픽사','월트디즈니',
              poster='linear-gradient(160deg,#1565c0 0%,#f57f17 60%,#e53935 100%)')
    m3 = movie('Exhuma','파묘','거액의 의뢰를 받은 무당과 장의사가 수상한 묫자리를 이장하면서 벌어지는 이야기.','이장 작업에서 시작된 기이한 사건들','15세','공포',8.1,11920000,'2D','공포',134,'2024-02-22','장재현','최민식, 유해진, 김고은, 이도현','장재현','한국','2024 대종상 최우수작품상','쇼박스','쇼박스',
              poster='linear-gradient(160deg,#0a0a0a 0%,#1b3a1b 50%,#4a7c4a 100%)')
    m4 = movie('Dune: Part Two','듄: 파트 2','폴 아트레이데스는 프레멘의 예언자로 거듭나 황제에게 복수를 시작한다.','폴의 복수와 예언자로서의 여정','12세','없음',12.3,4200000,'2D/3D/IMAX','SF',165,'2024-02-28','드니 빌뇌브','티모시 샬라메, 젠데이아, 오스틴 버틀러','드니 빌뇌브','미국','2024 아카데미 최우수촬영상','레전더리','워너브라더스',
              poster='linear-gradient(160deg,#3e1f00 0%,#8b5e1a 50%,#c9a84c 100%)')
    m5 = movie('Hijack 1971','하이재킹','1971년 실화 기반 항공기 납치 사건.','1971년 실화 기반 항공기 납치 사건','15세','폭력성',15.7,3100000,'2D','액션',100,'2024-06-21','류승완','하정우, 여진구, 성동일','류승완','한국','','외유내강','CJ ENM',
              poster='linear-gradient(160deg,#0d2137 0%,#1e4976 50%,#4a90d9 100%)')
    m6 = movie('Wicked','위키드','오즈의 마법사 이전 이야기. 두 마녀의 우정과 갈등.','오즈의 마법사 세계관 속 두 마녀의 우정','전체관람가','없음',22.4,890000,'2D','뮤지컬',160,'2024-11-22','존 M. 추','신시아 에리보, 아리아나 그란데','위닌 홀즈만','미국','','유니버설','유니버설',
              poster='linear-gradient(160deg,#1a003e 0%,#6a0dad 50%,#e91e8c 100%)')

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

    movies_runtimes = {m1:109, m2:100, m3:134, m4:165, m5:100, m6:160}

    def end(start, runtime):
        h, m = map(int, start.split(':'))
        total = h * 60 + m + runtime + 20  # 상영시간 + 광고
        return f"{(total//60)%24:02d}:{total%60:02d}"

    # 모든 영화를 모든 극장에서 상영
    all_movies = [m1,m2,m3,m4,m5,m6]
    all_theaters = [t1,t2,t3,t4,t5]
    time_slots = [('09:00','조조'),('12:00','일반'),('15:00','일반'),('18:30','일반'),('21:00','심야')]

    for date in ['2026-05-01','2026-05-02','2026-05-03','2026-05-04','2026-05-05','2026-05-06','2026-05-07']:
        for theater in all_theaters:
            for idx, movie in enumerate(all_movies):
                rt = movies_runtimes[movie]
                # 각 영화를 극장당 2회 상영 (시간대 분산)
                start1 = time_slots[idx % len(time_slots)][0]
                slot1  = time_slots[idx % len(time_slots)][1]
                start2 = time_slots[(idx + 2) % len(time_slots)][0]
                slot2  = time_slots[(idx + 2) % len(time_slots)][1]
                sch(theater, movie, date, start1, end(start1, rt), slot1, 1)
                sch(theater, movie, date, start2, end(start2, rt), slot2, 2)

    hashed = bcrypt.hashpw('test1234'.encode(), bcrypt.gensalt()).decode()
    conn.execute("INSERT INTO customer (name,email,password,phone,birth_date,customer_type,status) VALUES ('김민준','test@cinebook.com',?,?,?,'회원','정상')",
                 [hashed,'010-1234-5678','1995-03-15'])
    conn.commit()
    print('[OK] 시드 데이터 삽입 완료')
    print('     테스트 계정: test@cinebook.com / test1234')


if __name__ == '__main__':
    print('[CineBook] 서버 시작 중...')
    init_db()
    print('[CineBook] http://127.0.0.1:3000 에서 접속하세요')
    app.run(host='0.0.0.0', port=3000, debug=False)
