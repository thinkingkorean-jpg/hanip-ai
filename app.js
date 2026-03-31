/* ============================================
   한입 AI (Hannip) — App Logic
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initDate();
  initAnimations();
  initSubscribe();
  initShare();
});

/* === Theme Toggle === */
function initTheme() {
  const toggle = document.getElementById('themeToggle');
  if (!toggle) return;

  const saved = localStorage.getItem('hannip-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  toggle.textContent = saved === 'dark' ? '🌙' : '☀️';

  toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('hannip-theme', next);
    toggle.textContent = next === 'dark' ? '🌙' : '☀️';
  });
}

/* === Dynamic Date === */
function initDate() {
  const dateEl = document.getElementById('todayDate');
  if (!dateEl) return;

  const now = new Date();
  const days = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
  const formatted = `${now.getFullYear()}년 ${now.getMonth() + 1}월 ${now.getDate()}일 ${days[now.getDay()]}`;
  dateEl.textContent = formatted;
}

/* === Scroll Animations === */
function initAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate-in').forEach(el => {
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });
}

/* === Email Subscribe === */
function initSubscribe() {
  const form = document.getElementById('subscribeForm');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('emailInput').value;
    
    // Store locally for now (will connect to Mailchimp later)
    const subs = JSON.parse(localStorage.getItem('hannip-subscribers') || '[]');
    if (!subs.includes(email)) {
      subs.push(email);
      localStorage.setItem('hannip-subscribers', JSON.stringify(subs));
    }

    // Show success
    const btn = form.querySelector('.subscribe-btn');
    btn.textContent = '✅ 구독 완료!';
    btn.style.background = 'var(--success)';
    document.getElementById('emailInput').value = '';

    setTimeout(() => {
      btn.textContent = '구독하기';
      btn.style.background = '';
    }, 3000);
  });
}

/* === Share === */
function initShare() {
  const url = window.location.href;
  const title = document.title;

  document.getElementById('shareTwitter')?.addEventListener('click', () => {
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`, '_blank');
  });

  document.getElementById('shareKakao')?.addEventListener('click', () => {
    // Kakao share (simplified — full impl needs Kakao SDK)
    if (navigator.share) {
      navigator.share({ title, url });
    } else {
      copyToClipboard(url);
    }
  });

  document.getElementById('shareCopy')?.addEventListener('click', () => {
    copyToClipboard(url);
  });
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('shareCopy');
    if (btn) {
      btn.textContent = '✅';
      setTimeout(() => { btn.textContent = '🔗'; }, 2000);
    }
  });
}
