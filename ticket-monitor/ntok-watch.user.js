// ==UserScript==
// @name         국립극장 잔여석 감시 + 자동 예매진입 (RE:MOVE ERA 22일)
// @namespace    ntok-watch
// @version      1.1
// @description  22일 잔여석 감시 → 좌석 뜨면 예매창 자동 이동 → 유의사항 '확인' 자동 클릭 (좌석선택/결제는 직접)
// @match        *://*.ntok.go.kr/*
// @match        *://ntok.go.kr/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==
(function () {
  'use strict';

  // ───────── 설정 (공연/회차 바꾸려면 여기만) ─────────
  const PERF = '267191';   // IdPerf
  const TIME = '82193';    // IdTime (22일 19:30)
  const MIN = 3, MAX = 5;  // 감시 간격(초). 너무 짧으면 방화벽 차단 위험.
  const COOL = 90;         // 차단/실패 감지 시 대기(초)
  const BOOKURL = 'https://mbooking.ntok.go.kr/Pages/Perf/Sale/PerfSaleProcess.aspx?IdPerf=' + PERF + '&IdTime=' + TIME;
  // ──────────────────────────────────────────────────

  const host = location.hostname;

  // ===== (A) 예매 사이트: 유의사항 '확인' 자동 클릭 =====
  if (host.indexOf('mbooking') >= 0) {
    let done = false, tries = 0;
    const rank = e => (['BUTTON', 'A', 'INPUT'].indexOf(e.tagName) >= 0 ? 0 : 1);
    const click = e => {
      ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(tp => {
        try { e.dispatchEvent(new MouseEvent(tp, { bubbles: true, cancelable: true, view: window })); } catch (_) {}
      });
      try { e.click(); } catch (_) {}
    };
    const iv = setInterval(() => {
      tries++;
      if (done || tries > 100) { clearInterval(iv); return; }
      const body = document.body ? document.body.innerText : '';
      // 유의사항 팝업이 떠 있을 때만 동작 (좌석선택 등 다른 화면의 '확인'은 건드리지 않음)
      if (body.indexOf('유의사항') < 0 && body.indexOf('2매') < 0) return;
      const els = [...document.querySelectorAll('button,a,input,[role=button],span,div')]
        .filter(e => { const tx = (e.textContent || e.value || '').trim(); return tx === '확인' && e.offsetParent !== null; })
        .sort((a, b) => rank(a) - rank(b));
      if (els[0]) { click(els[0]); done = true; clearInterval(iv); }
    }, 120);
    return;
  }

  // ===== (B) 국립극장 상세페이지: 잔여석 감시 =====
  // 상세페이지(performanceDetail)에서만 감시 시작. 그 외 ntok 페이지에선 아무것도 안 함.
  if (location.pathname.indexOf('performanceDetail') < 0) return;

  let s = false, AC, cnt = 0, lastc = -1, last = '--:--:--';
  try { AC = new (window.AudioContext || window.webkitAudioContext)(); AC.resume(); } catch (e) {}
  // 아무 클릭이나 한 번 하면 소리 잠금 해제
  document.addEventListener('click', () => { try { AC && AC.resume(); } catch (e) {} }, { once: true });

  let b = document.getElementById('__watchbar');
  if (b) b.remove();
  b = document.createElement('div');
  b.id = '__watchbar';
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#0a7;color:#fff;font:bold 14px sans-serif;padding:9px 6px;text-align:center;box-shadow:0 2px 6px rgba(0,0,0,.35)';
  b.textContent = '감시 준비중… (소리 켜려면 화면 아무 곳이나 한 번 클릭)';
  (document.body || document.documentElement).appendChild(b);

  const sl = m => new Promise(r => setTimeout(r, m));
  const rnd = () => Math.round(MIN + Math.random() * (MAX - MIN));
  const bar = (t, bg) => { b.style.background = bg; b.textContent = t; };

  function beep() {
    try {
      if (AC) {
        for (let k = 0; k < 3; k++) {
          const o = AC.createOscillator(), g = AC.createGain();
          o.connect(g); g.connect(AC.destination);
          o.type = 'square'; o.frequency.value = k % 2 ? 988 : 784;
          const t = AC.currentTime + k * 0.2;
          g.gain.setValueAtTime(0.4, t); o.start(t); o.stop(t + 0.16);
        }
      }
    } catch (e) {}
  }

  async function chk() {
    try {
      const r = await fetch('/ntok/pm/prfmng/selectSeatListInfo.do', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest' },
        body: 'id=' + PERF + '&timeId=' + TIME
      });
      if (!r.ok) return -3;
      const j = await r.json();
      if (!j || !j.seatList) return -1;
      let mx = 0;
      for (const x of j.seatList) if (typeof x.bookableCount === 'number' && x.bookableCount > mx) mx = x.bookableCount;
      return mx;
    } catch (e) { return -2; }
  }

  async function lp() {
    while (!s) {
      cnt++;
      lastc = await chk();
      last = new Date().toLocaleTimeString();
      if (lastc > 0) {
        s = true;
        document.title = '★잔여석' + lastc + '석';
        try { if (navigator.vibrate) navigator.vibrate([300, 100, 300]); } catch (_) {}
        beep();
        bar('★ 잔여석 ' + lastc + '석! 예매창으로 이동…', '#c00');
        location.href = BOOKURL;   // 같은 탭 즉시 이동 → mbooking에서 확인 자동 클릭됨
        break;
      }
      if (lastc <= -2) {
        let sec = COOL;
        for (; sec > 0 && !s; sec--) { bar('⚠ 요청 실패/차단 감지 — ' + sec + '초 대기 (무리한 재시도 금지)', '#b30000'); await sl(1000); }
        continue;
      }
      const st = lastc === 0 ? '전석 0석' : '응답형식오류';
      let sec = rnd();
      for (; sec > 0 && !s; sec--) { bar('🟢 감시중 ' + cnt + '회 · ' + last + ' · ' + st + ' · 다음 ' + sec + '초', '#0a7'); await sl(1000); }
    }
  }
  lp();
})();
