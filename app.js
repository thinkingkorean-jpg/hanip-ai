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

/* === Email Subscribe (보안 강화 + JSONP 방식) === */
function initSubscribe() {
  const form = document.getElementById('subscribeForm');
  if (!form) return;

  // 🛡️ 허니팟 안티봇 필드 (봇만 이 숨겨진 필드를 채움)
  const honeypot = document.createElement('input');
  honeypot.type = 'text';
  honeypot.name = 'website';
  honeypot.id = 'hp_field';
  honeypot.tabIndex = -1;
  honeypot.autocomplete = 'off';
  honeypot.style.cssText = 'position:absolute;left:-9999px;opacity:0;height:0;width:0;';
  form.prepend(honeypot);

  // 🛡️ URL 난독화
  const _s = [104,116,116,112,115,58,47,47,115,99,114,105,112,116,46,103,111,111,103,108,101,46,99,111,109,47,109,97,99,114,111,115,47,115,47,65,75,102,121,99,98,122,122,115,77,79,57,55,120,73,52,69,97,97,53,52,111,82,51,55,107,106,117,82,69,72,105,102,118,56,122,117,112,55,68,51,45,55,78,67,79,112,121,70,95,105,117,80,88,84,57,68,95,119,89,80,98,108,86,65,57,102,80,85,56,67,104,66,119,47,101,120,101,99];
  const WEBHOOK_URL = _s.map(c => String.fromCharCode(c)).join('');

  // JSONP 콜백
  window.hannipCb = function(status) {
    console.log('구독 처리:', status);
  };

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    // 🛡️ 1. 허니팟 검사
    if (honeypot.value) { console.warn('Bot detected'); return; }

    // 🛡️ 2. 속도 제한 — 30초 내 재시도 차단
    const lastSub = localStorage.getItem('hannip_last_sub');
    if (lastSub && (Date.now() - parseInt(lastSub)) < 30000) {
      alert('잠시 후 다시 시도해주세요.');
      return;
    }

    const input = document.getElementById('emailInput');
    const email = input.value.trim();

    // 🛡️ 3. 이메일 형식 검증
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!email || !emailRegex.test(email)) {
      alert('올바른 이메일 주소를 입력해주세요.');
      return;
    }

    const btn = form.querySelector('.subscribe-btn');
    btn.textContent = '구독 중...';
    btn.style.background = '#94a3b8';
    btn.disabled = true;

    // 🚀 JSONP 방식 구독 전송
    const script = document.createElement('script');
    script.src = WEBHOOK_URL + '?email=' + encodeURIComponent(email) + '&callback=hannipCb&t=' + Date.now();

    script.onload = function() {
        btn.textContent = '✅ 구독 완료!';
        btn.style.background = 'var(--success)';
        input.value = '';
        localStorage.setItem('hannip_last_sub', Date.now().toString());
        try { document.head.removeChild(script); } catch(e) {}
        setTimeout(function() { btn.textContent = '구독하기'; btn.style.background = ''; btn.disabled = false; }, 3000);
    };

    script.onerror = function() {
        btn.textContent = '⚠️ 네트워크 오류';
        btn.style.background = '#ef4444';
        try { document.head.removeChild(script); } catch(e) {}
        setTimeout(function() { btn.textContent = '구독하기'; btn.style.background = ''; btn.disabled = false; }, 3000);
    };

    document.head.appendChild(script);
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
