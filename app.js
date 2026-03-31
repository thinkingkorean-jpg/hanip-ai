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

  // 구글 Apps Script 연동 완료!
  const WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyLsg9gTnHcJylKD33pbJk_rIrnB1jocqKnSTy1RHikxe9fC1yhxNJxjpQzIt0MsRmX1A/exec";

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = document.getElementById('emailInput');
    const email = input.value.trim();
    if (!email) return;

    const btn = form.querySelector('.subscribe-btn');
    const originalText = btn.textContent;
    btn.textContent = '구독 중...';
    btn.style.background = '#94a3b8';
    btn.disabled = true;

    // 만약 URL을 아직 설정하지 않았다면 테스트용 알림만 표시
    if (WEBHOOK_URL === "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL") {
      alert(`[테스트 완료]\n입력하신 이메일(${email})이 정상적으로 전달되었습니다.\n(구글 시트 연동을 완료하고 WEBHOOK_URL을 수정해주세요!)`);
      resetBtn();
      return;
    }

    // Google Apps Script로 데이터 전송 (CORS 우회를 위해 mode: 'no-cors' 필수)
    fetch(WEBHOOK_URL, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ email: email })
    })
    .then(response => {
        btn.textContent = '✅ 구독 완료!';
        btn.style.background = 'var(--success)';
        input.value = '';
    })
    .catch(error => {
        alert("일시적인 오류가 발생했습니다. 나중에 다시 시도해주세요.");
        console.error('Subscription Error:', error);
    })
    .finally(() => {
        setTimeout(resetBtn, 3000);
    });

    function resetBtn() {
        btn.textContent = originalText;
        btn.style.background = '';
        btn.disabled = false;
        input.value = '';
    }
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
