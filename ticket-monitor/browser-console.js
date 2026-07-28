/* ─────────────────────────────────────────────────────────────
   국립극장 잔여석 감시 — 브라우저 콘솔용 (설치 불필요)
   RE : MOVE ERA (리무브 에라) · 22일 공연

   ▶ 사용법
     1) 크롬에서 예매 페이지를 연다.
     2) F12 (또는 우클릭 → 검사) → 상단 [Console] 탭.
     3) 아래 코드를 전부 복사해 붙여넣고 Enter.
     4) 잔여석이 뜨면 alert 팝업이 뜬다. 그때 직접 예매하기!
     ※ 멈추려면 콘솔에 __stopWatch() 입력 후 Enter.
   ───────────────────────────────────────────────────────────── */
(() => {
  const DATE = '22';        // 감시할 날짜(일)
  const MIN = 10, MAX = 15; // 확인 간격(초)
  let stopped = false;

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const wait  = () => (MIN + Math.random() * (MAX - MIN)) * 1000;

  // '잔여좌석' 영역의 좌석 수를 읽는다. 0보다 크면 잔여석 발생.
  function seatCount() {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    for (const anchor of ['잔여좌석', '잔여석']) {
      const i = t.indexOf(anchor);
      if (i === -1) continue;
      const w = t.slice(i, i + 100); // 앵커 뒤 100자만 (다른 곳 '석' 숫자에 안 속게)
      const nums = [...w.matchAll(/(\d+)\s*석/g)].map(m => +m[1]);
      const pos = nums.filter(n => n > 0);
      if (pos.length) return Math.max(...pos);
      if (nums.length) return 0; // 0석만 보임 → 아직 매진
    }
    const m = t.match(/전석\s*(\d+)\s*석/); // 보조
    return m ? +m[1] : -1;
  }

  // 22일 날짜(정확히 '22' 텍스트인 클릭가능 요소)를 눌러 잔여석 정보 갱신
  function clickDate() {
    const els = document.querySelectorAll('a,button,td,li,span,dd,strong');
    for (const el of els) {
      if (el.textContent.trim() === DATE && el.offsetParent !== null) {
        el.click();
        return true;
      }
    }
    return false;
  }

  async function loop() {
    console.log('%c[감시 시작] ' + DATE + '일 잔여석 확인 중… (멈추려면 __stopWatch())',
                'color:green;font-weight:bold');
    while (!stopped) {
      clickDate();
      await sleep(1500); // 갱신 대기
      const c = seatCount();
      const now = new Date().toLocaleTimeString();
      if (c > 0) {
        document.title = '★잔여석 ' + c + '석★';
        console.log('%c★★★ 잔여석 ' + c + '석 발생! (' + now + ') ★★★',
                    'color:red;font-size:20px;font-weight:bold');
        alert('잔여석 발생! (' + DATE + '일)\n\n전석 ' + c + '석\n\n' +
              '지금 예매하기를 누르세요!\n' + now);
        stopped = true;
        break;
      }
      console.log('[' + now + '] 전석 ' + (c === 0 ? '0' : '?') + '석 … 대기');
      await sleep(wait());
    }
  }

  window.__stopWatch = () => { stopped = true; console.log('감시 중지됨'); };
  loop();
})();
