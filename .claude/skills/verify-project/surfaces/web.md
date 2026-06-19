# surface: web — 브라우저 UI Live Test 드라이버

## Detect (T0 표면감지 신호)
- HTTP 서버 + HTML/템플릿/SPA 빌드(`templates/`, `static/`, `index.html`, React/Vue/Svelte 빌드).
- 의존성에 프론트 프레임워크 또는 server-side 렌더(FastAPI+Jinja, Flask, Next, etc.).
- README가 "브라우저에서 localhost:PORT 접속" 류를 안내.

## Driver — Playwright headed (Windows에서 보이게)
- WSL/WSLg 환경: `DISPLAY=:0`이면 headed 브라우저가 Windows 데스크톱에 표시된다. 먼저 확인:
  ```bash
  echo "$DISPLAY"; command -v playwright || pip show playwright
  ```
- headed 실행(파이썬 예):
  ```python
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
      browser = p.chromium.launch(headless=False)   # WSLg → Windows에 표시
      page = browser.new_page()
      page.goto("http://localhost:PORT/")
      page.screenshot(path="evaluation/<대상>/screenshots/01_home.png")
      # ... 케이스별 상호작용 + 단계 스크린샷
      browser.close()
  ```
- Playwright 미설치 시: `pip install playwright && playwright install chromium`(대상 venv 오염 주의 — 검증용 별도 venv 권장).

## 케이스별 캡처 규칙
- 각 정상 케이스마다 **시작 → 조작 → 결과** 최소 1~3매 스크린샷, `screenshots/NN_<케이스>.png`.
- 보고서에는 스크린샷을 상대경로 이미지로 임베드 + 그 케이스의 mermaid flow.
- 동적 응답(LLM 등)은 비결정적일 수 있음 — **형태/존재**를 단언(특정 문자열 강제 금지).

## 흔한 함정
- headless로 떨어지면 Windows에 안 보임 → 사용자 요구가 "보이게"면 반드시 `headless=False` + `DISPLAY` 확인.
- 포트/경로는 T2 가동표에서 가져옴(하드코딩 금지).
