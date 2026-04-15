/* ============================================
   한입 AI (Hannip) - App Logic
   ============================================ */

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initDate();
  initAnimations();
  initSubscribe();
  initShare();
});

function initTheme() {
  const toggle = document.getElementById("themeToggle");
  if (!toggle) return;

  const saved = localStorage.getItem("hannip-theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  toggle.textContent = saved === "dark" ? "🌔" : "☀️";

  toggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("hannip-theme", next);
    toggle.textContent = next === "dark" ? "🌔" : "☀️";
  });
}

function initDate() {
  const dateEl = document.getElementById("todayDate");
  if (!dateEl || dateEl.dataset.staticDate === "true") return;

  const now = new Date();
  const days = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];
  dateEl.textContent = `${now.getFullYear()}년 ${now.getMonth() + 1}월 ${now.getDate()}일 ${days[now.getDay()]}`;
}

function initAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = "running";
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll(".animate-in").forEach((el) => {
    el.style.animationPlayState = "paused";
    observer.observe(el);
  });
}

function setSubscribeState(button, message, background, disabled = true) {
  if (!button) return;
  button.textContent = message;
  button.style.background = background || "";
  button.disabled = disabled;
}

function normalizeSubscribeResponse(payload) {
  if (!payload) {
    return { ok: false, message: "응답을 확인하지 못했어요. 잠시 후 다시 시도해 주세요." };
  }

  if (typeof payload === "string") {
    const lowered = payload.toLowerCase();
    if (lowered.includes("success") || lowered.includes("ok")) {
      return { ok: true, message: "구독이 완료됐어요. 메일함에서 첫 소식을 기다려 주세요." };
    }
    return { ok: false, message: payload };
  }

  const success = Boolean(
    payload.success ||
      payload.ok ||
      payload.status === "success" ||
      payload.code === "success"
  );

  const message =
    payload.message ||
    payload.result ||
    payload.detail ||
    (success
      ? "구독이 완료됐어요. 메일함에서 첫 소식을 기다려 주세요."
      : "구독 처리에 실패했어요. 잠시 후 다시 시도해 주세요.");

  return { ok: success, message };
}

function initSubscribe() {
  const form = document.getElementById("subscribeForm");
  if (!form) return;

  // 🛡️ 허니팟 안티봇
  const honeypot = document.createElement("input");
  honeypot.type = "text";
  honeypot.name = "website";
  honeypot.id = "hp_field";
  honeypot.tabIndex = -1;
  honeypot.autocomplete = "off";
  honeypot.style.cssText = "position:absolute;left:-9999px;opacity:0;height:0;width:0;";
  form.prepend(honeypot);

  const statusEl =
    document.getElementById("subscribeStatus") ||
    (() => {
      const el = document.createElement("p");
      el.id = "subscribeStatus";
      el.style.marginTop = "0.75rem";
      el.style.fontSize = "0.9rem";
      form.insertAdjacentElement("afterend", el);
      return el;
    })();

  // 🛡️ URL 난독화 (Google Apps Script JSONP)
  const _s = [104,116,116,112,115,58,47,47,115,99,114,105,112,116,46,103,111,111,103,108,101,46,99,111,109,47,109,97,99,114,111,115,47,115,47,65,75,102,121,99,98,122,122,115,77,79,57,55,120,73,52,69,97,97,53,52,111,82,51,55,107,106,117,82,69,72,105,102,118,56,122,117,112,55,68,51,45,55,78,67,79,112,121,70,95,105,117,80,88,84,57,68,95,119,89,80,98,108,86,65,57,102,80,85,56,67,104,66,119,47,101,120,101,99];
  const WEBHOOK_URL = _s.map(c => String.fromCharCode(c)).join('');

  // JSONP 콜백
  window.hannipCb = function(status) {
    console.log('구독 처리:', status);
  };

  form.addEventListener("submit", function(e) {
    e.preventDefault();

    // 🛡️ 허니팟 검사
    if (honeypot.value) { console.warn("Bot detected"); return; }

    // 🛡️ 속도 제한
    const lastSub = localStorage.getItem("hannip_last_sub");
    if (lastSub && Date.now() - parseInt(lastSub, 10) < 30000) {
      statusEl.textContent = "잠시 후 다시 시도해 주세요.";
      statusEl.style.color = "#ef4444";
      return;
    }

    const input = document.getElementById("emailInput");
    const button = form.querySelector(".subscribe-btn");
    const email = input.value.trim();
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    if (!email || !emailRegex.test(email)) {
      statusEl.textContent = "올바른 이메일 주소를 입력해 주세요.";
      statusEl.style.color = "#ef4444";
      return;
    }

    setSubscribeState(button, "구독 중..", "#94a3b8");
    statusEl.textContent = "잠시만 기다려 주세요...";
    statusEl.style.color = "var(--text-secondary)";

    // 🚀 JSONP 방식 (서버에 API 키 노출 없이 안전하게 전송)
    const script = document.createElement("script");
    script.src = WEBHOOK_URL + "?email=" + encodeURIComponent(email) + "&callback=hannipCb&t=" + Date.now();

    script.onload = function() {
      setSubscribeState(button, "✅ 구독 완료", "var(--success)");
      statusEl.textContent = "구독이 완료되었습니다! 🎉";
      statusEl.style.color = "var(--success)";
      input.value = "";
      localStorage.setItem("hannip_last_sub", Date.now().toString());
      try { document.head.removeChild(script); } catch(err) {}
      setTimeout(function() { setSubscribeState(button, "구독하기", "", false); }, 3000);
    };

    script.onerror = function() {
      setSubscribeState(button, "⚠️ 네트워크 오류", "#ef4444");
      statusEl.textContent = "구독 처리 중 오류가 발생했어요. 잠시 후 다시 시도해 주세요.";
      statusEl.style.color = "#ef4444";
      try { document.head.removeChild(script); } catch(err) {}
      setTimeout(function() { setSubscribeState(button, "구독하기", "", false); }, 3000);
    };

    document.head.appendChild(script);
  });
}

function initShare() {
  const url = window.location.href;
  const title = document.title;
  const text = `${title} ${url}`;

  document.getElementById("shareTwitter")?.addEventListener("click", () => {
    window.open(
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`,
      "_blank",
      "noopener,noreferrer"
    );
  });

  document.getElementById("shareKakao")?.addEventListener("click", async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title, text, url });
        return;
      } catch (error) {
        // 사용자가 취소한 경우 링크 복사로 대체
      }
    }

    copyToClipboard(url, "카카오톡 공유용 링크를 복사했어요.");
  });

  document.getElementById("shareCopy")?.addEventListener("click", () => {
    copyToClipboard(url, "링크를 복사했어요.");
  });
}

function copyToClipboard(text, message) {
  navigator.clipboard.writeText(text).then(() => {
    const button = document.getElementById("shareCopy");
    if (button) {
      const original = button.textContent;
      button.textContent = "✓";
      window.setTimeout(() => {
        button.textContent = original;
      }, 2000);
    }

    const statusEl = document.getElementById("subscribeStatus");
    if (statusEl && message) {
      statusEl.textContent = message;
      statusEl.style.color = "var(--text-secondary)";
    }
  });
}
