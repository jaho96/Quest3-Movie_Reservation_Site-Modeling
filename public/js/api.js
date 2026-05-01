const API = 'http://127.0.0.1:3000/api';

// ── API 요청 헬퍼 ─────────────────────────────────────
async function req(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API + path, { ...options, headers: { ...headers, ...(options.headers || {}) } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || '오류가 발생했습니다.');
  return data;
}

const api = {
  get:    (path)       => req(path),
  post:   (path, body) => req(path, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (path, body) => req(path, { method: 'PUT',    body: JSON.stringify(body) }),
  delete: (path)       => req(path, { method: 'DELETE' }),

  customers: {
    register:       (d)   => api.post('/customers/register', d),
    login:          (d)   => api.post('/customers/login', d),
    me:             ()    => api.get('/customers/me'),
    updateMe:       (d)   => api.put('/customers/me', d),
    changePassword: (d)   => api.put('/customers/me/password', d),
    withdraw:       ()    => api.delete('/customers/me'),
  },
  movies: {
    list:  (p = {}) => api.get('/movies?' + new URLSearchParams(p)),
    get:   (id)     => api.get(`/movies/${id}`),
    media: (id)     => api.get(`/movies/${id}/media`),
  },
  theaters: {
    list:    (region) => api.get('/theaters' + (region ? `?region=${region}` : '')),
    get:     (id)     => api.get(`/theaters/${id}`),
    screens: (id)     => api.get(`/theaters/${id}/screens`),
  },
  screens: {
    seats: (id) => api.get(`/screens/${id}/seats`),
  },
  schedules: {
    list:          (p = {}) => api.get('/schedules?' + new URLSearchParams(p)),
    get:           (id)     => api.get(`/schedules/${id}`),
    reservedSeats: (id)     => api.get(`/schedules/${id}/reserved-seats`),
  },
  reservations: {
    list:   ()     => api.get('/reservations'),
    get:    (id)   => api.get(`/reservations/${id}`),
    create: (d)    => api.post('/reservations', d),
    cancel: (id)   => api.put(`/reservations/${id}/cancel`),
  },
  payments: {
    create:        (d)   => api.post('/payments', d),
    get:           (id)  => api.get(`/payments/${id}`),
    byReservation: (id)  => api.get(`/payments/reservation/${id}`),
  },
  tickets: {
    list: () => api.get('/tickets'),
  },
  reviews: {
    list:   (p = {}) => api.get('/reviews?' + new URLSearchParams(p)),
    create: (d)      => api.post('/reviews', d),
    like:   (id)     => api.post(`/reviews/${id}/like`),
    delete: (id)     => api.delete(`/reviews/${id}`),
  },
  media: {
    list:   (p = {}) => api.get('/media?' + new URLSearchParams(p)),
    create: (d)      => api.post('/media', d),
  },
};

// ── 인증 상태 ─────────────────────────────────────────
const auth = {
  getToken:   () => localStorage.getItem('token'),
  getUser:    () => { try { return JSON.parse(localStorage.getItem('user')); } catch { return null; } },
  setAuth:    (token, user) => { localStorage.setItem('token', token); localStorage.setItem('user', JSON.stringify(user)); },
  clearAuth:  () => { localStorage.removeItem('token'); localStorage.removeItem('user'); },
  isLoggedIn: () => !!localStorage.getItem('token'),
};

// ── 공통 유틸 ─────────────────────────────────────────
function showToast(msg, type = '') {
  document.querySelector('.toast')?.remove();
  const t = document.createElement('div');
  t.className = 'toast' + (type ? ' ' + type : '');
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

function logout() {
  auth.clearAuth();
  location.href = '/';
}

// ── 헤더 인증 렌더링 ──────────────────────────────────
function renderAuthHeader() {
  const el = document.getElementById('headerActions');
  if (!el) return;
  const user = auth.getUser();
  if (user) {
    el.innerHTML = `
      <span style="font-size:14px;color:var(--text-secondary);">
        안녕하세요, <strong style="color:var(--text-primary);">${user.name}</strong>님
      </span>
      <a href="/mypage.html" class="btn-outline">마이페이지</a>
      <button class="btn-outline" onclick="logout()">로그아웃</button>`;
  } else {
    el.innerHTML = `
      <button class="btn-outline" onclick="openModal('authModal')">로그인</button>
      <button class="btn-primary"  onclick="openModal('authModal')">회원가입</button>`;
  }
}

// ── 공통 로그인/회원가입 모달 주입 ──────────────────────
function injectAuthModal() {
  if (document.getElementById('authModal')) return;
  document.body.insertAdjacentHTML('beforeend', `
    <div class="modal-overlay" id="authModal">
      <div class="modal" style="position:relative;width:440px;">
        <span class="modal-close" onclick="closeModal('authModal')">✕</span>

        <div id="loginTab">
          <h2>로그인</h2>
          <p style="color:var(--text-secondary);font-size:14px;margin-bottom:24px;">CineBook 계정으로 로그인하세요</p>
          <div class="form-group">
            <label class="form-label">이메일</label>
            <input class="form-input" id="loginEmail" type="email" placeholder="이메일" value="test@cinebook.com">
          </div>
          <div class="form-group">
            <label class="form-label">비밀번호</label>
            <input class="form-input" id="loginPw" type="password" placeholder="비밀번호" value="test1234">
          </div>
          <div class="modal-actions">
            <button class="btn-primary" style="padding:13px;" onclick="doLogin()">로그인</button>
            <button class="btn-outline" style="padding:12px;" onclick="switchAuth('register')">회원가입하기</button>
          </div>
        </div>

        <div id="registerTab" style="display:none;">
          <h2>회원가입</h2>
          <p style="color:var(--text-secondary);font-size:14px;margin-bottom:24px;">CineBook 계정을 만들어보세요</p>
          <div class="form-group">
            <label class="form-label">이름</label>
            <input class="form-input" id="regName" type="text" placeholder="이름">
          </div>
          <div class="form-group">
            <label class="form-label">이메일</label>
            <input class="form-input" id="regEmail" type="email" placeholder="이메일">
          </div>
          <div class="form-group">
            <label class="form-label">비밀번호</label>
            <input class="form-input" id="regPw" type="password" placeholder="비밀번호 (6자 이상)">
          </div>
          <div class="form-group">
            <label class="form-label">휴대폰</label>
            <input class="form-input" id="regPhone" type="tel" placeholder="010-0000-0000">
          </div>
          <div class="form-group">
            <label class="form-label">생년월일</label>
            <input class="form-input" id="regBirth" type="date">
          </div>
          <div class="modal-actions">
            <button class="btn-primary" style="padding:13px;" onclick="doRegister()">회원가입</button>
            <button class="btn-outline" style="padding:12px;" onclick="switchAuth('login')">로그인하기</button>
          </div>
        </div>
      </div>
    </div>
  `);
  document.getElementById('authModal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal('authModal');
  });
}

function switchAuth(tab) {
  document.getElementById('loginTab').style.display    = tab === 'login'    ? 'block' : 'none';
  document.getElementById('registerTab').style.display = tab === 'register' ? 'block' : 'none';
}

async function doLogin() {
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPw').value;
  if (!email || !password) { showToast('이메일과 비밀번호를 입력해주세요.', 'error'); return; }
  try {
    const { token, customer } = await api.customers.login({ email, password });
    auth.setAuth(token, customer);
    closeModal('authModal');
    renderAuthHeader();
    showToast(`${customer.name}님 환영합니다!`, 'success');
    if (typeof onLoginSuccess === 'function') onLoginSuccess();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function doRegister() {
  const name     = document.getElementById('regName').value.trim();
  const email    = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPw').value;
  const phone    = document.getElementById('regPhone').value.trim();
  const birth_date = document.getElementById('regBirth').value;
  if (!name || !email || !password) { showToast('이름, 이메일, 비밀번호는 필수입니다.', 'error'); return; }
  if (password.length < 6) { showToast('비밀번호는 6자 이상이어야 합니다.', 'error'); return; }
  try {
    await api.customers.register({ name, email, password, phone, birth_date });
    showToast('회원가입 완료! 로그인해주세요.', 'success');
    switchAuth('login');
    document.getElementById('loginEmail').value = email;
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// ── 페이지 로드 시 공통 초기화 ────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  injectAuthModal();
  renderAuthHeader();
  document.querySelectorAll('.modal-overlay').forEach(el => {
    el.addEventListener('click', e => { if (e.target === el) el.classList.remove('open'); });
  });
});
