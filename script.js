// ===========================
//   EDU PLATFORM — SCRIPT.JS
// ===========================

const API = 'http://127.0.0.1:5000/api';

// ── ДАННЫЕ КУРСОВ (локальные, для поиска) ──
const COURSES = [
  { id:1, title:'Технологии дистанционного обучения', desc:'Принципы PBL, Google Classroom, геймификация и автоматические тесты.', section:'pedagogy', sectionLabel:'Педагогика', badgeClass:'badge-blue', emoji:'🎓', bg:'linear-gradient(135deg,#EEF2FF,#C7D2FE)', modules:3, url:'course.html?id=1' },
  { id:2, title:'Педагогическая геймификация', desc:'Alias, Wordle, SOYA, дебаты и интерактивные форматы в учебном процессе.', section:'pedagogy', sectionLabel:'Педагогика', badgeClass:'badge-blue', emoji:'🎮', bg:'linear-gradient(135deg,#F5F3FF,#DDD6FE)', modules:3, url:'course.html?id=2' },
  { id:3, title:'Python-разработка', desc:'От фреймворка Kivy до работы с библиотеками SQLite и pandas.', section:'it', sectionLabel:'IT', badgeClass:'badge-cyan', emoji:'🐍', bg:'linear-gradient(135deg,#E0F2FE,#BAE6FD)', modules:4, url:'course.html?id=3' },
  { id:4, title:'Основы кибербезопасности', desc:'Защита данных, моделирование угроз и практика с тайными ролями.', section:'it', sectionLabel:'IT', badgeClass:'badge-cyan', emoji:'🔐', bg:'linear-gradient(135deg,#EFF6FF,#BFDBFE)', modules:3, url:'course.html?id=4' },
  { id:5, title:'Геоинформационные системы (ГИС)', desc:'Анализ пространственных данных и работа с геоинформационными инструментами.', section:'special', sectionLabel:'Спецдисциплины', badgeClass:'badge-green', emoji:'🌍', bg:'linear-gradient(135deg,#F0FDF4,#BBF7D0)', modules:3, url:'course.html?id=5' }
];

// ══════════════════════════════════
//   API ФУНКЦИИ
// ══════════════════════════════════

async function apiPost(url, data) {
  try {
    const res = await fetch(API + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data)
    });
    return await res.json();
  } catch (e) {
    console.warn('API недоступен, работаем офлайн:', e.message);
    return null;
  }
}

async function apiGet(url) {
  try {
    const res = await fetch(API + url, { credentials: 'include' });
    return await res.json();
  } catch (e) {
    console.warn('API недоступен, работаем офлайн:', e.message);
    return null;
  }
}

// ══════════════════════════════════
//   АВТОРИЗАЦИЯ
// ══════════════════════════════════

// Текущий пользователь в памяти
let currentUser = null;

// Загрузить пользователя из сессии при старте
async function loadCurrentUser() {
  const user = await apiGet('/auth/me');
  if (user && user.id) {
    currentUser = user;
    updateNavbar(user);
  }
}

function updateNavbar(user) {
  // Меняем кнопки навбара если пользователь вошёл
  const actions = document.querySelector('.nav-actions');
  if (!actions) return;
  actions.innerHTML = `
    <span style="font-size:0.85rem;font-weight:700;color:var(--primary);">
      ${user.role === 'teacher' ? '👨‍🏫' : '👨‍🎓'} ${user.full_name}
    </span>
    <a href="${user.role === 'teacher' ? 'teacher.html' : 'student.html'}"
       class="btn-login">Кабинет</a>
    <button class="btn-primary" onclick="doLogout()">Выйти</button>
  `;
}

async function doLogout() {
  await apiPost('/auth/logout', {});
  currentUser = null;
  window.location.href = 'index.html';
}

// ══════════════════════════════════
//   МОДАЛЬНОЕ ОКНО + OTP
// ══════════════════════════════════

function openModal() {
  const overlay = document.getElementById('modalOverlay');
  if (overlay) {
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal() {
  const overlay = document.getElementById('modalOverlay');
  if (overlay) {
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }
}

function closeModalOutside(e) {
  if (e.target === document.getElementById('modalOverlay')) closeModal();
}

async function sendOTP() {
  const phone = document.getElementById('phoneInput').value.replace(/\s/g, '');
  if (phone.length < 9) { alert('Введите корректный номер телефона'); return; }

  const btn = document.querySelector('#stepPhone .btn-full');
  if (btn) { btn.textContent = 'Отправка...'; btn.disabled = true; }

  // Отправляем на бэкенд
  const result = await apiPost('/auth/send-otp', { phone });

  if (btn) { btn.textContent = 'Получить SMS-код →'; btn.disabled = false; }

  if (result && result.success) {
    // Показываем сообщение с кодом (в тестовом режиме)
    const desc = document.getElementById('otpDesc');
    if (desc) desc.textContent = result.message || `Код отправлен на +998 ${phone.slice(0,2)} *** ** **`;

    document.getElementById('stepPhone').style.display = 'none';
    document.getElementById('stepOTP').style.display = 'block';
    document.getElementById('otp1').focus();
  } else {
    // Офлайн режим — продолжаем без бэкенда
    document.getElementById('otpDesc').textContent = `Код: 1234 (тестовый режим)`;
    document.getElementById('stepPhone').style.display = 'none';
    document.getElementById('stepOTP').style.display = 'block';
    document.getElementById('otp1').focus();
  }
}

async function verifyOTP() {
  const code = ['otp1','otp2','otp3','otp4'].map(id => {
    const el = document.getElementById(id);
    return el ? el.value : '';
  }).join('');

  if (code.length < 4) { alert('Введите 4-значный код'); return; }

  const phone    = document.getElementById('phoneInput').value.replace(/\s/g, '');
  const roleEl   = document.getElementById('roleSelect');
  const role     = roleEl ? roleEl.value : 'student';

  const btn = document.querySelector('#stepOTP .btn-full');
  if (btn) { btn.textContent = 'Проверка...'; btn.disabled = true; }

  // Проверяем через бэкенд
  const result = await apiPost('/auth/verify-otp', { phone, code, role });

  if (btn) { btn.textContent = 'Войти ✓'; btn.disabled = false; }

  if (result && result.success) {
    currentUser = result.user;
    closeModal();
    showToast(`Добро пожаловать, ${result.user.full_name}! 👋`);
    setTimeout(() => {
      window.location.href = role === 'teacher' ? 'teacher.html' : 'student.html';
    }, 1000);
  } else if (result && result.error) {
    alert(result.error);
  } else {
    // Офлайн — просто переходим
    closeModal();
    window.location.href = role === 'teacher' ? 'teacher.html' : 'student.html';
  }
}

function otpNext(el, nextId) {
  if (el.value.length === 1 && nextId) {
    document.getElementById(nextId).focus();
  }
}

function backToPhone() {
  document.getElementById('stepOTP').style.display = 'none';
  document.getElementById('stepPhone').style.display = 'block';
}

async function resendOTP() {
  const phone = document.getElementById('phoneInput').value.replace(/\s/g, '');
  await apiPost('/auth/send-otp', { phone });
  alert('Код отправлен повторно!');
}

// ══════════════════════════════════
//   TOAST УВЕДОМЛЕНИЯ
// ══════════════════════════════════

function showToast(msg, type = 'success') {
  const colors = { success: '#10B981', error: '#EF4444', info: '#4F46E5' };
  const toast = document.createElement('div');
  toast.style.cssText = `
    position:fixed; bottom:2rem; right:2rem; z-index:9999;
    background:${colors[type] || colors.success}; color:white;
    padding:0.9rem 1.5rem; border-radius:12px;
    font-family:'Nunito',sans-serif; font-weight:700; font-size:0.92rem;
    box-shadow:0 8px 25px rgba(0,0,0,0.15);
    animation:fadeUp 0.3s ease;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ══════════════════════════════════
//   ЗАПИСЬ НА КУРС
// ══════════════════════════════════

async function enrollCourse(courseId) {
  const result = await apiPost(`/courses/${courseId}/enroll`, {});
  if (result && result.success) {
    showToast('Вы записаны на курс! 🎓');
  } else if (!result) {
    showToast('Войдите для записи на курс', 'info');
    openModal();
  }
}

// ══════════════════════════════════
//   ЗАВЕРШИТЬ МОДУЛЬ
// ══════════════════════════════════

async function completeModule(moduleId, courseId) {
  const result = await apiPost('/progress/complete-module', { module_id: moduleId, course_id: courseId });
  if (result && result.success) {
    showToast('+20 баллов! Модуль пройден ✅');
    // Обновляем прогресс-бар если есть
    loadProgress();
  }
}

// ══════════════════════════════════
//   ЗАГРУЗКА ПРОГРЕССА
// ══════════════════════════════════

async function loadProgress() {
  const data = await apiGet('/progress');
  if (!data || !Array.isArray(data)) return;

  data.forEach(course => {
    const bar = document.querySelector(`[data-course-id="${course.course_id}"] .progress-fill`);
    if (bar) bar.style.width = course.percent + '%';
  });
}

// ══════════════════════════════════
//   ДАШБОРД СТУДЕНТА
// ══════════════════════════════════

async function loadStudentDashboard() {
  const data = await apiGet('/student/dashboard');
  if (!data) return;

  // Обновляем статистику
  const statNums = document.querySelectorAll('.stat-num');
  if (statNums[0]) statNums[0].textContent = data.courses_count || 0;
  if (statNums[1]) statNums[1].textContent = data.modules_done || 0;
  if (statNums[2]) statNums[2].textContent = data.user?.score || 0;
  if (statNums[3]) statNums[3].textContent = data.debts || 0;

  // Имя пользователя
  const h1 = document.querySelector('.main-content h1');
  if (h1 && data.user) {
    h1.textContent = `Добро пожаловать, ${data.user.full_name}! 👋`;
  }
}

// ══════════════════════════════════
//   ЛИДЕРБОРД
// ══════════════════════════════════

async function loadLeaderboard() {
  const data = await apiGet('/student/leaderboard');
  if (!data || !Array.isArray(data)) return;

  const container = document.querySelector('.leaderboard');
  if (!container) return;

  const medals = ['👑','🥈','🥉'];
  const topClasses = ['top1','top2','top3'];

  container.innerHTML = data.map((s, i) => `
    <div class="lb-item ${topClasses[i] || ''} ${s.is_me ? 'style="border:2px solid var(--primary)"' : ''}">
      <div class="lb-rank">${i + 1}</div>
      <div class="avatar" style="width:36px;height:36px;font-size:0.8rem;flex-shrink:0;">
        ${s.name.split(' ').map(n=>n[0]).join('').slice(0,2)}
      </div>
      <div class="lb-name" ${s.is_me ? 'style="color:var(--primary);font-weight:800;"' : ''}>
        ${s.name}${s.is_me ? ' (вы)' : ''}
      </div>
      <div class="lb-score">${s.score} баллов</div>
      <div class="lb-badge">${medals[i] || ''}</div>
    </div>
  `).join('');
}

// ══════════════════════════════════
//   ФОРУМ — СОЗДАТЬ ТЕМУ
// ══════════════════════════════════

async function submitThreadAPI(title, body, category) {
  const result = await apiPost('/forum', { title, body, category });
  return result && result.success;
}

// ══════════════════════════════════
//   ДНЕВНИК
// ══════════════════════════════════

async function saveDiaryAPI(text, courseId) {
  const result = await apiPost('/diary', { text, course_id: courseId });
  if (result && result.success) showToast('Запись сохранена 📓');
}

// ══════════════════════════════════
//   ПОИСК
// ══════════════════════════════════

function doSearch() {
  const q = document.getElementById('searchInput')?.value.trim().toLowerCase();
  if (!q) return;
  showSearchResults(q);
}

function searchTag(text) {
  const input = document.getElementById('searchInput');
  if (input) input.value = text;
  showSearchResults(text.toLowerCase());
}

function showSearchResults(q) {
  const results = COURSES.filter(c =>
    c.title.toLowerCase().includes(q) ||
    c.desc.toLowerCase().includes(q) ||
    c.sectionLabel.toLowerCase().includes(q)
  );
  const section = document.getElementById('searchResults');
  const grid    = document.getElementById('searchGrid');
  const title   = document.getElementById('searchTitle');
  if (!section) return;

  title.textContent = `Найдено: ${results.length} курс(ов) по запросу «${q}»`;
  grid.innerHTML = results.length
    ? results.map(courseCard).join('')
    : '<p style="color:var(--text-secondary);">Ничего не найдено.</p>';

  section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function courseCard(c) {
  return `
    <a href="${c.url}" class="course-card" style="text-decoration:none;">
      <div class="course-card-header" style="background:${c.bg};">${c.emoji}</div>
      <div class="course-card-body">
        <span class="course-section-badge ${c.badgeClass}">${c.sectionLabel}</span>
        <h3>${c.title}</h3>
        <p>${c.desc}</p>
      </div>
      <div class="course-card-footer">
        <span class="course-meta">📦 ${c.modules} модуля</span>
        <span class="btn-card">Подробнее</span>
      </div>
    </a>`;
}

function clearSearch() {
  const section = document.getElementById('searchResults');
  if (section) section.style.display = 'none';
  const input = document.getElementById('searchInput');
  if (input) input.value = '';
}

const si = document.getElementById('searchInput');
if (si) si.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

// ══════════════════════════════════
//   ПРОЧЕЕ
// ══════════════════════════════════

function toggleModule(el) {
  el.closest('.module-item').classList.toggle('open');
}

function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

// Анимации при скролле
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.feature-card, .course-card, .timeline-item, .stat-card').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});

// ══════════════════════════════════
//   ИНИЦИАЛИЗАЦИЯ
// ══════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
  // Загружаем текущего пользователя
  await loadCurrentUser();

  // Если мы на странице студента — загружаем данные
  if (window.location.pathname.includes('student.html')) {
    await loadStudentDashboard();
    await loadProgress();
  }
});
