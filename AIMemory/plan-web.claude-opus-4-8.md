# Plan — 데일리 어드바이저 웹사이트 (GitHub Actions 일일 갱신 + 모바일 PWA)

**Author**: claude-opus-4-8 (manager)
**Date**: 2026-06-20 06:57
**Re**: 사용자 요청 — (1) README 재작성 + GitHub Actions 일일 갱신 website + 휴대폰 URL 앱(PWA) 접근

> 매니저가 독자 수립한 계획(diverge-converge PROPOSE 생략 — 사용자 "업무 명확, 독자 계획" 지시).
> 실제 수행은 전부 worker로 위임(aimux enqueue). 매니저는 분해·라우팅·증거기반 accept/re-route만.

## 목표
1. README.md를 make_Harness 스캐폴드 설명 → **qld-timing-backtest 프로젝트 README**로 재작성.
2. 추천 전략①(SOXL60 buffer±3% + QLD40)의 **오늘의 신호·목표배분**을 보여주는 정적 웹사이트.
3. GitHub Actions cron으로 **매일 자동 갱신**, GitHub Pages 배포.
4. 휴대폰에서 URL → 홈화면 추가 → **앱처럼(PWA)** 사용(오프라인 캐시·standalone).

배포 URL(예상): `https://wilocraw-alt.github.io/qld-timing-backtest/` (project pages → **모든 경로 상대(`./`)** 필수).

## 사이트 데이터 계약 (매니저 확정 — 모든 단위가 이 계약 준수)
`web/build_site.py --out <dir> [--config backtest/live/advisor_config.yaml]` 가 `<dir>`에 생성:
- `index.html` — 모바일 우선 PWA 셸. 표시 항목:
  - 오늘의 신호 판정: **SOXL ON(보유) / OFF(현금) / 중립(직전유지)** + SOXX ratio(종가/120MA) vs ±3% 밴드
  - 갱신 시각(KST), 기준 전일 종가일, 오늘 미국장 개장/휴장(NYSE 캘린더)
  - 목표 배분 카드: SOXL 60% / QLD 40% (신호 OFF면 코어→현금)
  - 최신 종가: SOXL · SOXX · QLD
  - 핵심 결론 1~2줄 + RESEARCH.md(GitHub) 링크, **면책 고지**
- `manifest.webmanifest` — name/short_name/icons(192·512)/display=standalone/theme_color/`start_url`·`scope`=상대
- `sw.js` — 셸 + `data/latest.json` 오프라인 캐시(서브경로에서 동작하도록 상대 등록)
- `icons/icon-192.png`, `icon-512.png` (+ maskable) — 워커 생성(PIL 등)
- `data/latest.json` — 기계판독 스냅샷: `{updated_at, tz, ref_close, market:{open,reason}, signal:{soxx_close, ma120, ratio, upper, lower, state}, prices:{SOXL,SOXX,QLD}, target:{core_pct,satellite_pct}, conclusion, disclaimer}`

신호 로직(무상태 스냅샷): ratio>1+buf→ON / ratio<1-buf→OFF / 사이→중립(직전유지). 히스테리시스는 무상태라 근사 — index에 캐비엇 표기.
신호·휴장 판정은 `backtest/live/daily_advisor.py`의 `_NYSEHolidays`/`market_status`/120MA buffer 로직 재사용(import 또는 동일 규칙).

## 단위 분해 (의존성 기준)
- **A. README 재작성** — 의존 없음. (→ antigravity)
- **B. 사이트 빌더 + PWA 프론트** — 의존 없음. yfinance/env 사용 → (→ opencode, env 안정적)
- **C. GitHub Actions 워크플로** — 계약 고정이므로 병렬 가능, 검증은 B 산출 후. (→ A 끝낸 워커 또는 idle)
- **D. 통합·배포·검증** — B·C 의존. commit+push+Pages 활성(`gh api ... build_type=workflow`)+`workflow_dispatch` 트리거+URL 도달 확인. (→ opencode)

## Wave
- Wave1(병렬): A→antigravity, B→opencode
- Wave2: C(→먼저 idle된 워커), 그 후 D(→opencode)

## 수용 기준
- A: README 최상단이 더 이상 "make_Harness"가 아니고 프로젝트(목적·결론·실행·RESEARCH 링크·면책) 반영. 스캐폴드 설명은 DESIGN.md 링크로 축소.
- B: `python web/build_site.py --out /tmp/site_test` 에러0, index.html+manifest+sw.js+icons+data/latest.json 생성, latest.json 스키마 일치, 경로 전부 상대. 휴대폰 뷰포트 meta 포함.
- C: YAML 유효(`python -c yaml.safe_load`), cron `0 6 * * *`+workflow_dispatch, pages권한, build(upload-pages-artifact)+deploy(deploy-pages) 잡.
- D: 푸시 완료, Pages=Actions 소스 활성, 워크플로 1회 성공, 배포 URL이 200 + index 렌더.

## 라우팅 메모(agents.md 반영)
- antigravity: env 건드리면 rabbit-hole → A(순수 docs)·C(순수 YAML)만, env 언급 금지.
- opencode: 가장 신뢰 — B(env/멀티파일)·D(git/gh) 담당.
