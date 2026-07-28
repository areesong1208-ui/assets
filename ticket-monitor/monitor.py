#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
국립극장(ntok.go.kr) 잔여석 감시기
─────────────────────────────────────────────
단순 자동 클리커와 달리, 이 스크립트는 "좌석이 실제로 떴는지"를
스스로 판단해서 잔여석이 생기는 순간 **팝업 창**으로 알려줍니다.

동작 방식
  1) 실제 크롬 브라우저 창을 띄웁니다(봇 차단 우회 + 사람처럼 접속).
  2) 사용자가 직접 날짜(22일/23일 등)를 선택합니다.
  3) 터미널에서 Enter를 누르면 감시를 시작합니다.
  4) 10~15초 간격(랜덤)으로 페이지를 새로고침하며 좌석 수를 확인합니다.
  5) "0석 / 매진"이 숫자(잔여석)로 바뀌는 순간 감시를 멈추고
     화면 맨 위에 팝업 경고창을 띄웁니다. → 직접 예매하기!

필요 프로그램
  - Python 3
  - Playwright:  pip install playwright  &&  python -m playwright install chromium
  - 팝업(tkinter)은 파이썬 기본 내장이라 별도 설치가 필요 없습니다.

실행
  python monitor.py
"""

import re
import sys
import time
import random
import threading
import tkinter as tk
from tkinter import messagebox

from playwright.sync_api import sync_playwright

# ─────────────────────────── 설정 (여기만 고치면 됩니다) ───────────────────────────

# 감시 대상: 한국예술종합학교 무용원 <RE : MOVE ERA (리무브 에라)>  — 22일 공연만
SHOW_NAME = "RE : MOVE ERA (리무브 에라) — 22일"
URL = "https://www.ntok.go.kr/ntok/pm/prfmng/performanceDetail.do?perfId=267191&mi=21008"

# 감시할 날짜(일). "22"일만 봅니다. 새로고침할 때마다 이 날짜를 자동으로 다시 선택합니다.
DATE_TEXT = "22"

# ↑ 자동 날짜 선택이 안 맞으면(브라우저에서 22일이 안 눌리면) 여기에 정확한 선택자를 넣으세요.
#   예) "a:has-text('22')"  또는  "td[data-date='2026-08-22']"  등.
#   비워두면 아래 여러 패턴을 자동으로 시도합니다.
DATE_SELECTOR = ""

# 새로고침 간격(초). 서버가 봇으로 오해해 차단하지 않도록 10~15초를 권장합니다.
MIN_INTERVAL = 10
MAX_INTERVAL = 15

# 잔여석 표시 영역을 찾는 기준 문구. 이 문구 바로 뒤의 좌석 수를 봅니다.
# 페이지에는 "예매가능 잔여좌석  전석  0석" 형태로 나옵니다.
AVAIL_ANCHORS = ["잔여좌석", "잔여석"]

# 좌석 수를 뽑아내는 패턴 (예: "전석 0석", "12석"). 앵커 뒤에서만 찾습니다.
SEAT_COUNT_PATTERN = re.compile(r"(\d+)\s*석")

# 앵커 뒤로 이만큼(글자 수)만 살펴봅니다. 페이지 다른 곳의 "석" 숫자에 속지 않기 위함.
AVAIL_WINDOW = 100

# ──────────────────────────────────────────────────────────────────────────────


def show_popup(title, message):
    """항상 맨 위에 뜨는 팝업 경고창을 띄운다. 사용자가 확인을 누를 때까지 유지."""
    root = tk.Tk()
    root.withdraw()  # 빈 기본창 숨기기
    root.attributes("-topmost", True)
    root.lift()
    root.after(100, lambda: root.focus_force())
    messagebox.showinfo(title, message, parent=root)
    root.destroy()


def select_date(page):
    """
    감시할 날짜(DATE_TEXT, 기본 '22'일)를 클릭해 그 날짜 기준으로 잔여석 정보를 갱신한다.
    새로고침하면 날짜 선택이 풀리므로 매번 다시 눌러줘야 한다.
    반환: (성공여부, 사용한 선택자)
    """
    candidates = []
    if DATE_SELECTOR:
        candidates.append(DATE_SELECTOR)
    # 달력/탭/목록에서 '22'만 정확히 매칭하는 흔한 패턴들
    candidates += [
        f"a:text-is('{DATE_TEXT}')",
        f"button:text-is('{DATE_TEXT}')",
        f"td:text-is('{DATE_TEXT}')",
        f"li:text-is('{DATE_TEXT}')",
        f"span:text-is('{DATE_TEXT}')",
        f"[data-day='{DATE_TEXT}']",
        f"a:has-text('{DATE_TEXT}일')",
    ]
    for sel in candidates:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                target = loc.first
                if target.is_visible():
                    target.click(timeout=3000)
                    page.wait_for_timeout(1500)  # 잔여석 정보 갱신 대기
                    return True, sel
        except Exception:
            continue
    return False, None


def is_seat_available(page_text):
    """
    페이지의 '잔여좌석' 영역을 찾아, 그 뒤의 좌석 수가 0이 아니면
    잔여석 발생으로 판단한다. (예: "전석 0석" → "전석 5석")
    반환: (True/False, 사람이 읽을 설명 문자열)
    """
    for anchor in AVAIL_ANCHORS:
        idx = page_text.find(anchor)
        if idx == -1:
            continue
        # 앵커 바로 뒤 구간만 살펴본다 → 페이지 다른 곳의 "석" 숫자에 안 속음
        window = page_text[idx: idx + AVAIL_WINDOW]
        seat_numbers = [int(n) for n in SEAT_COUNT_PATTERN.findall(window)]
        positive = [n for n in seat_numbers if n > 0]
        if positive:
            return True, f"잔여좌석 {max(positive)}석 (0석 → 숫자로 변경)"
        if seat_numbers:  # 0석만 보임 → 아직 매진
            return False, "전석 0석 (매진)"

    # 앵커 자체를 못 찾은 경우: 페이지 전체에서 "전석 N석"이라도 확인 (보조)
    m = re.search(r"전석\s*(\d+)\s*석", page_text)
    if m and int(m.group(1)) > 0:
        return True, f"전석 {m.group(1)}석 감지"

    return False, "잔여좌석 정보 확인 중"


def main():
    print("=" * 60)
    print("  잔여석 감시기")
    print(f"  공연     : {SHOW_NAME}")
    print("=" * 60)
    print(f"  대상 URL : {URL}")
    print(f"  감시 날짜: {DATE_TEXT}일 (매 새로고침마다 자동 재선택)")
    print(f"  새로고침 : {MIN_INTERVAL}~{MAX_INTERVAL}초 간격 (랜덤)")
    print("=" * 60)

    with sync_playwright() as p:
        # headless=False → 실제 창이 보입니다. 사람처럼 접속해 봇 차단을 피합니다.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            locale="ko-KR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded")

        # 시작 전에 22일 자동 선택을 한 번 시도해 본다.
        ok, used = select_date(page)
        if ok:
            print(f"\n[준비] {DATE_TEXT}일 자동 선택 성공 (선택자: {used}).")
            print(f"       브라우저에 {DATE_TEXT}일의 '전석 0석'이 보이는지 확인하세요.")
        else:
            print(f"\n[준비] {DATE_TEXT}일 자동 선택 실패 — 브라우저 창에서 직접 {DATE_TEXT}일을 눌러주세요.")
            print("       (계속 실패하면 monitor.py 상단 DATE_SELECTOR에 정확한 선택자를 넣으세요.)")
        print("       준비가 끝나면 이 터미널로 돌아와 Enter를 누르세요.")
        try:
            input("       ▶ 준비되면 Enter... ")
        except (EOFError, KeyboardInterrupt):
            print("\n중단합니다.")
            browser.close()
            return

        print("\n[감시 시작] 잔여석이 뜨면 팝업이 뜹니다. 중단하려면 Ctrl+C.\n")

        check_count = 0
        try:
            while True:
                check_count += 1
                try:
                    # 페이지 새로고침 (= '다시 보기'와 같은 효과)
                    page.reload(wait_until="domcontentloaded")
                    time.sleep(1.5)  # 내용 로딩 대기
                    # 새로고침하면 날짜가 풀리므로 22일을 다시 선택
                    select_date(page)
                    body_text = page.inner_text("body")
                except Exception as e:
                    print(f"  [{check_count}] 새로고침 오류: {e} → 잠시 후 재시도")
                    time.sleep(random.uniform(MIN_INTERVAL, MAX_INTERVAL))
                    continue

                available, reason = is_seat_available(body_text)
                now = time.strftime("%H:%M:%S")

                if available:
                    print(f"  [{check_count}] {now}  ★★★ 잔여석 발생! ({reason}) ★★★")
                    # 브라우저 창을 앞으로
                    try:
                        page.bring_to_front()
                    except Exception:
                        pass
                    # 팝업 (사용자가 확인 누를 때까지 유지)
                    show_popup(
                        "잔여석 발생!",
                        f"[{SHOW_NAME}]\n\n"
                        f"잔여석이 감지되었습니다!\n\n{reason}\n\n"
                        f"지금 브라우저에서 '예매하기'를 누르세요!\n\n"
                        f"시각: {now}",
                    )
                    print("\n감시를 종료합니다. 브라우저에서 직접 예매하세요!")
                    # 브라우저는 열어둔 채 유지 → 바로 예매 가능
                    input("예매를 마친 뒤 Enter를 누르면 창을 닫습니다... ")
                    break
                else:
                    print(f"  [{check_count}] {now}  {reason} … 대기")

                time.sleep(random.uniform(MIN_INTERVAL, MAX_INTERVAL))

        except KeyboardInterrupt:
            print("\n사용자 중단. 종료합니다.")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
