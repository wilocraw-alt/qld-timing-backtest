# aimux 설계 문서

AIMemory tmux 멀티에이전트 오케스트레이션(`aimux`)의 아키텍처·동작·설계 근거·레퍼런스.
개요는 `README.md`, 에이전트용 규약(영문)은 `AIMemory/tmux-handoff.md`·`AIMemory/PROTOCOL.md`,
역량 원장은 `AIMemory/agents.md`, 스캐폴드 개발 이력은 `HARNESS-CHANGELOG.md`(T 시리즈).

---

## 1. 목표

여러 AI 에이전트(claude·antigravity·opencode·qwen 등)를 tmux 패널로 띄우고, **매니저 1명이
사람과 대화하며 작업을 분해·위임**하고 워커들이 수행해 결과를 돌려주는 협업 체계.
설계 원칙은 "한 사람만 사람과 대화, 나머지는 워커", "전달은 단일 채널로 직렬화",
"idle을 완료로 착각하지 않기", "동시 세션 간섭 없음".

---

## 2. 아키텍처

구성요소:
- **매니저 패널** — 사람과 대화하고 프로젝트를 소유. 작업을 분해·배정·통합·판정. 실질 작업(구현·통합·검증)은 전부 위임하고 **직접 일하지 않음** — 직접 수행은 해당 유닛이 위임에서 2회+ 실패 AND 사용자 승인일 때만(T29).
- **워커 패널** — 핸드오프를 받아 *정해진 범위만* 수행하고 결과를 큐 로 반환(antigravity·opencode·qwen 등).
- **디스패처 패널** — 단일 데몬(`aimux dispatch`). 큐를 읽어 idle 패널에만 전달, 상태 추적, 라이브 피드 출력.
- **큐/상태**(`AIMemory/.aimux/<session>/{queue,inflight,done,failed}`) — 요청·응답을 파일로 적재.
- **AICP**(`AIMemory/PROTOCOL.md`) — 진실의 원천. 핸드오프 파일 + append-only `work.log`.

데이터 흐름(요청 1건):
```
매니저: handoff_*.md 작성 + work.log(HANDOFF) → aimux enqueue
   → queue/  ──(디스패처)── 타깃 idle? & 잠금 없음? → paste+Enter → inflight/
   → 워커 수행 → 응답 handoff + aimux enqueue --type response
   → queue/ ──(디스패처)── 매니저 idle? → paste → 매니저 판정 → done/
```

---

## 3. 동작 생명주기 (디스패처)

매 사이클(`dispatch_once`):
1. 큐의 신규 항목을 피드에 `＋ QUEUE`로 표시.
2. in-flight 항목 진행/해제 판정(`process_inflight`).
3. 대기(pending) 항목을 우선순위+FIFO로 전달 시도(`deliver_pending`).
4. 카운트 변동 시 `┄ p=N i=M d=K ┄` 보드 출력.

전달 가드(겹침 차단):
- **in-flight 잠금**: 한 패널에 동시 1건만. 그 패널에 처리 중 항목이 있으면 보류.
- **idle 게이트**: 타깃 화면 tail이 안정(idle)일 때만 paste. 작업 중이면 보류.

해제 사유(`release_reason`):
- `response-seen` — 타깃이 응답(reply-to)을 enqueue함 → 정상 완료.
- `resolved` — 매니저가 `aimux resolve <req-id>`로 대역외(out-of-band) 종결 선언(직접 검증·수락) → 완료(freed-notice 미발행, report에서 completed 집계).
- `idle-stable` — 전달 후 참여 신호(work.log 활동 **또는** busy 관찰=`saw_busy`)가 있었고 연속 idle 충족 → 완료.
- `unacked` — 참여 신호가 전혀 없어(busy 관찰도, 로그도 없음) 재촉 후에도 무활동 → 미수신으로 판단(escalate).
- `timeout` — 하드 타임아웃.
- `pane-gone` — 패널 소멸.
- `superseded` — resolved된 요청에 대한 후속물(notice/늦은 response)이라 전달하지 않고 드롭됨.

---

## 4. 핵심 메커니즘과 근거(why)

각 장치는 실제 에이전트 운영에서 드러난 문제를 막기 위해 도입됨.

- **큐 + 단일 디스패처** — 에이전트가 서로 직접 paste하면 다수 동시 사용 시 초인종이 겹침.
  적재만 하게 하고 단일 디스패처가 전달 → 겹침 원천 차단.
- **idle 게이트 + 연속 idle 해제(streak)** — 초기엔 단일 idle 체크로 해제(`idle-no-change`)해서,
  생각 중인 LLM의 일시적 화면 안정을 idle로 오판 → 바쁜 패널에 덮어쓰기·유실 발생.
  이제 `AIMUX_RELEASE_IDLE_CYCLES`회 **연속** idle일 때만 해제(busy면 streak 리셋). (T1·T17)
  - **긴 단일 턴 거짓 해제 방지(v0.1.1)**: 하드 타임아웃 시점에 패널이 **여전히 busy**(화면 변동, 프롬프트
    막힘 아님)면 멈춘 게 아니라 긴 작업(대용량 문서 변환·빌드)이다. 실측: 28쪽 변환이 902s>900s라
    "타임아웃·무응답"으로 거짓 보고됨. 이제 busy면 해제 대신 `AIMUX_INFLIGHT_TIMEOUT_MAX`(2700s) 천장까지
    연장하고, idle/막힘이거나 천장 도달 시에만 해제.
- **사용자 입력 대기 vs 완료 후 idle 구별** — 권한/예-아니오/선택 프롬프트로 **사용자 입력을 기다리는**
  패널(화면은 안정=idle처럼 보임)은 `AIMUX_WAIT_PATTERN`으로 감지해 **보류**(해제·재촉 안 함,
  재배분 안 함, 새 전달 안 함) → 매니저에 오보·건너뛰기 방지. "완료 후 무응답 idle"(통지/재촉 대상)과
  구분. 하드 타임아웃은 백스톱으로 유지. (T24)
  - **가시 화면만 매칭(스크롤백 제외, T36)**: 초기 구현은 `-S -40`으로 스크롤백까지 캡처해,
    이미 답한 프롬프트("Esc to cancel" 등)가 히스토리에 남아 패널을 **영구 waiting으로 오판** →
    해당 패널로의 모든 전달이 멈춤(매니저가 디스패처 사망으로 오진해 강제 재시작까지 함). 지금
    막혀 있는 프롬프트는 정의상 화면에 보이므로, wait/risk/발췌는 **가시 화면만** 캡처.
    (idle 안정성 해시는 스크롤백 포함 유지 — 무해.)
- **대기 프롬프트의 위험도 라우팅** — 보류된 프롬프트를 `AIMUX_WAIT_RISK_PATTERN`(파괴적/비가역/외부노출/
  자격증명 마커)으로 한 번 더 분류해 에피소드당 1회 라우팅. 위험도는 프롬프트 **배후 동작**으로 판정 —
  "always allow / don't ask again" 같은 UI 옵션은 거의 모든 권한 프롬프트에 떠 있어 그 자체로 고위험이
  아님(T29). **저위험**(단순 권한 요청 포함)이면 매니저에게 "사람 역할
  수행" notice(워커 pane id + 프롬프트 발췌 포함)를 보내 매니저가 해당 패널에 `tmux send-keys`로 직접
  답하게 함(프롬프트 응답은 핸드오프가 아니므로 허용되는 유일한 직접 paste) → 사소한 확인으로 워커가
  멈추지 않음. **고위험**이면 매니저가 답하지 않고 **실제 사람에게만** 표면화. 매니저가 저위험 notice를
  읽고 위험하다고 판단하면 답 대신 사용자에게 에스컬레이션. (T25, T29)
  - **사용자 우선 유예 + stale 답 차단(T32)**: 저위험 notice는 즉시 발사하지 않고 연속
    `AIMUX_WAIT_NOTICE_CYCLES`(기본 2) 대기 관찰 후에만 발사 — 실제 사용자가 먼저 답할 기회를 줌.
    사용자가 먼저 답해 프롬프트가 사라지면 ① 아직 미발사면 notice 자체가 안 나가고, ② 발사됐지만
    미전달이면 큐에서 **자동 취소**, ③ 이미 전달됐어도 notice 본문이 매니저에게 "답하기 전에 그
    프롬프트가 아직 떠 있는지 `capture-pane`으로 재확인, 사라졌으면 아무것도 보내지 말 것"을 지시 —
    stale 답이 새 입력으로 주입돼 엉뚱한 수행을 시키는 것을 3중으로 차단. 고위험 표면화는 주입이
    없으므로 유예 없이 즉시.
  - **프롬프트-막힘 패널의 짧은 타임아웃(v0.1.1)**: 프롬프트에 막힌 패널은 사람/매니저가 답해야만
    풀리고 **스스로 response로 해소되지 않으므로**, 하드 타임아웃(900s)까지 붙드는 건 재라우팅만 늦춘다.
    실측: 구현 작업(pip·torch·셸 실행 등 위험 명령 多)에서 고위험 프롬프트 5건이 각 900s를 끝까지
    낭비(~75분)하고 "무응답" 거짓 알림을 냈다(반면 논문 작성 세션은 위험 명령이 적어 타임아웃 0건).
    `AIMUX_WAIT_TIMEOUT`(240s)에 막힘이 지속되면 freed-notice와 함께 조기 해제 → 매니저가 즉시
    재라우팅. 프롬프트는 화면에 남으니 늦은 답은 superseded/늦은 response로 처리(기존 흐름이 흡수).
  - **매니저 프롬프트는 사람 전용(워커 위임 금지)(v0.1.2)**: 워커가 매니저로 보낸 reply는
    `response` 타입이라 **매니저 pane을 inflight 유닛으로 등록**한다. 매니저는 계속 동작하며 자기
    권한 프롬프트(git·plan-gate 등)에 자주 막히는데, LOW-RISK 경로가 wait-notice 수신자를
    `to=from`(=reply를 보낸 **워커**)로 잡아 "워커야, 매니저 프롬프트에 대신 답해라"는 **권한 반전**이
    생겼다. 실측(test_AGTplatform): 워커가 매니저의 git 승인·`STEP 2 진행` 권한까지 대리 승인했고,
    매니저로 간 response inflight는 자연 종료신호(response-seen/resolved)가 없어 매 wait episode마다
    워커에게 notice를 재발행하며 wait-timeout(241s)까지 핑퐁 → 워커·디스패처가 엉뚱한 상대와
    통신하며 멈춘 것처럼 보였다. 해결: `is_manager_pane()`(pane의 `@awm_pane_name == manager`)로
    매니저를 식별해, 매니저가 프롬프트에 막히면 HIGH-RISK와 동일하게 **사람에게만 surface**하고
    워커 wait-notice는 발행하지 않음(매니저는 상위 대리인이 없음). 무인 실행 시 매니저 자체 도구
    프롬프트로 멈추지 않게 하려면 `AWM_AUTO_APPROVE=1`로 런치. (잔류 inflight는 매니저 idle 시
    idle-stable로, 미해소 시 wait-timeout로 해제되어 영구 lock 없음.)
- **세션 격리** — pane 이름 해석이 서버 전역이라 동일 이름 패널이 여러 세션에 있으면 오배달,
  단일 lock도 충돌. 해결: 세션명 timestamp + 세션별 상태 디렉터리 + `AIMUX_SESSION`으로 pane 해석을
  해당 세션으로 한정. **주의**: 기존 tmux 서버가 떠 있으면 `export`가 패널에 안 닿으므로,
  런처가 실행줄에 `env AIMUX_STATE=… AIMUX_SESSION=… TMPDIR=…`를 직접 프리픽스. (T11)
  - **중첩 프로젝트 work.log 오염 차단(v0.1.1)**: 프리픽스가 `AIMUX_STATE`(큐)만 고정하고
    `AIMUX_MEM_DIR`(→`AIMUX_WORKLOG`)은 빠져 있었다. `AIMUX_MEM_DIR`은 미설정 시 **호출된 aimux
    바이너리 위치**로 재계산되는데, 하위 폴더 프로젝트(예: `paper/`가 부모 안에 중첩, 동일 aimux 사본)에서
    워커 cwd가 부모로 드리프트하면 **큐는 자기 세션, 로그 라인은 부모 work.log**로 갈라졌다(reply 파일은
    여기, 로그는 옆 프로젝트로 새는 split-brain). 런처 프리픽스에 `AIMUX_MEM_DIR='$PROJECT_DIR/AIMemory'`를
    추가해 로그·tmp가 큐와 동일 세션을 따르게 함.
  - **continue 시 CLI 대화 복원의 프로젝트 bleed(v0.1.3)**: `aimux-up continue`는 aimux run-state
    (큐·handoff·work.log)는 매니페스트의 `project`로 정확히 복원한다. 그러나 워커 CLI의 **대화 자체**
    복원은 CLI에 위임되는데, opencode/antigravity/codex는 세션을 **git-루트 worktree 단위**로 버킷팅한다.
    중첩 프로젝트(`<proj>/paper`가 부모 `<proj>`의 git 루트를 공유)는 **같은 세션 버킷**에 들어가므로,
    bare `opencode --continue`(=버킷의 최근 세션)는 더 늦게 돈 **다른 프로젝트(paper)의 대화**를 복원한다
    → run-state는 부모, opencode 패널만 paper인 split-brain. claude/qwen은 매니페스트 uuid로 정확
    복원(`--resume <id>`)돼 안전. 해결: opencode는 세션 JSON의 `directory`가 PROJECT_DIR과 **정확히
    일치**(끝따옴표로 부모-자식 접두 오매칭 차단)하는 최신 세션 id를 찾아 `--session <id>`로 고정
    (`opencode_session_for_dir`); 없으면 `--continue`로 폴백하며 경고. antigravity(`--resume latest`)·codex
    (`resume --last`)는 정확-id 복원 미지원이라 경고만 발행. 추가로 continue 시 부모/자식 중 다른 aimux
    프로젝트가 있으면 **중첩 경고**를 띄워 패널이 올바른 프로젝트인지 확인하도록 함. 권고: 별도 aimux
    프로젝트는 별도 git 루트에 둘 것.
  - **`/verify-project` 스킬 = aimux 매니저 워크로드의 일급 사례(v0.2.0)**: 주어진 프로젝트를
    T0~T5(코드→설치→기능→적대적→종합)로 검증하는 슬래시 스킬을 하네스 본체에 추가. 설계상 `ideate`와
    동일한 매니저-패턴을 따른다 — 시작 시 `aimux agents`로 모드 분기(워커 있으면 매니저로 INSPECT/
    VERIFY/IMPLEMENT/TEST 위임, 없으면 단독). 흐름 계약은 두 모드 동일하고 *누가 실행하느냐*만 다르다.
    검증의 최종 판정·헬스·무결성은 매니저가 직접 재현(워커 자가보고는 곧이곧대로 받지 않는다는 원칙과
    동일 근거 — 워커 자가보고는 거짓일 수 있다). 산출물은 현재 작업 레포의 `evaluation/<대상명>/`,
    대상 폴더·자체 git은 미변경. 구조는 `ideate`와 대칭(skill 본체 `.claude/skills/`, 흐름 계약 `claude/`,
    양식 `templates/`)이라 폴더 통째 복사 시 슬래시 커맨드가 그대로 동작.
- **자동 통지(notice)** — 워커가 응답 없이 idle/timeout으로 해제되면 "idle=완료"가 아님을
  매니저가 모름. 디스패처가 원 source(매니저)에 `notice`를 자동 enqueue: "워커 X 무응답 — 산출물
  확인 후 accept/재배분". (T14)
- **대역외 종결 선언(`aimux resolve`)** — 매니저가 idle 워커를 먼저 발견해 산출물을 직접 검증·수락한
  경우, 디스패처는 그걸 모른 채 나중에 freed-notice·늦은 response를 또 넘겨 **같은 유닛을 재검증**하게
  만들었음. 매니저가 수락 즉시 `aimux resolve <req-id>`를 실행하면: ① inflight면 `resolved` 사유로
  해제(notice 미발행), ② 큐에 남은 그 요청의 notice/response 드롭(`superseded`), ③ 이후 enqueue되는
  후속물도 전달 시점에 드롭(`resolved.ids` 대조). 정상 완료가 아니면 resolve하지 않음 — 응답 대기/notice
  처리의 기존 흐름이 맞음. notice 본문·매니저 브리프에 사용 시점 명시. (T34)
- **제출 검증(Enter 재시도)** — TUI CLI(codex·claude 등)는 멀티라인 bracketed paste를 비동기로
  소화하므로, paste 직후 같은 순간에 보낸 Enter가 paste에 **삼켜져** 입력창에 "[Pasted Content N
  chars]"로 미제출 상태로 남는 일이 잦음. `deliver()`가 paste 후 `AIMUX_ENTER_SETTLE` 대기 → Enter →
  **화면 tail 해시 변화로 제출을 검증**(입력창 비워짐/에이전트 동작 시작), 변화 없으면 Enter를 최대
  `AIMUX_ENTER_TRIES`회 재시도. 끝까지 실패하면 로그 남기고 아래 재촉(re-nudge)이 백스톱. (T33)
  - **CLI별 제출 대기(v0.1.1)**: 실측상 RETRY/STUCK 경고의 ~90%가 opencode 단일 패널 **오탐**이었다
    (긴 세션에서 opencode가 일감을 다 끝냈는데도 28/31회 STUCK 로그). opencode TUI가 Enter-제출
    렌더를 기본 0.4s 창보다 느리게 그려 화면검사가 제출 전에 끝났기 때문. `enter_settle_for()`가 pane의
    `@awm_agent_kind`로 CLI별 대기(`AIMUX_ENTER_SETTLE_OPENCODE`=0.9s)를 선택 → 오탐 제거. 최종-시도
    로그도 "제출 실패"가 아니라 "느린 TUI라 미확인(대개 제출됨)"으로 톤을 낮춤.
- **무활동 재촉(re-nudge)** — 멀티라인 paste가 idle 패널 입력창에 *미제출*로 남아, 전달된 응답을
  매니저가 못 집는 경우. 참여 판정은 두 신호 중 **하나라도** 있으면 참여로 간주: (a) 전달 후 work.log의
  에이전트 이벤트(aimux 제외) 증가, (b) 전달 후 패널이 한 번이라도 **busy로 관찰**됨(`saw_busy` —
  전달은 idle 패널에만 하므로 이후의 busy는 paste에 대한 반응). (b)는 CLI 비의존이라 work.log를 안 쓰는
  워커가 "미수신"으로 오판돼 **같은 일을 재수행(중복작업)**하는 것을 막음(T32). 두 신호 모두 없을 때만 =
  진짜 미제출로 보고 **단일줄 nudge**(개행 없어 Enter로 제출 → 입력창의 원본까지 함께 제출)를 1회 재전달.
  그래도 없으면 `unacked`. (T17, T32)
- **견고성** — 디스패처 PID를 lock에 기록 + HUP 트랩(패널/서버 종료 시 동반 종료, orphan 방지)
  + `dispatch --force`(stale lock 회수). (T1·gap2)
  - **사망 포렌식 + 자동 재기동(T36)**: 모든 종료를 work.log에 기록 — 정상 신호 종료는
    "Dispatcher stopped", 그 외는 "EXITED unexpectedly (rc=N)" → dispatch 패널이 사라져도 원인이
    남음. `aimux-up`의 dispatch 패널은 `exec` 대신 **재기동 래퍼**로 실행: 비정상(rc≠0) 종료면 2초
    후 같은 패널에서 자동 재시작, 정상 종료면 셸로 복귀(패널이 닫히지 않음). 매니저 브리프에 오진
    방지 추가: `aimux status`가 "lock held"면 디스패처는 살아 있음 — 정지의 원인은 전달 게이트
    (waiting 보류 등)이므로 dispatch 패널 kill·`--force` 재시작 금지.
- **`/tmp` → `AIMemory/tmp`** — 프로젝트 밖(/tmp) 쓰기는 권한 프롬프트 유발. 스크래치를 프로젝트
  내부로. (T8)
- **라이브 피드** — dispatch 패널에 `＋ QUEUE → ▶ DELIVER → ✔ DONE`(+ `↻ NUDGE`) + 보드 실시간 표시.
  `AIMUX_VLOG=0`로 끔. (T13)
- **`aimux down`** — 작업 완결 시 현재 세션만 finalize+종료. (T16)

---

## 5. 오케스트레이션 정책 (매니저 행동)

**Phase 0 — 발산→수렴 계획(비단순 작업, 구현 전):**
- (0a) 사용자 요구사항(범위·제약·수용기준)을 확인·명확화.
- (0b) 확인된 요구사항을 파일로 적고, **매니저와 각 워커가 각자 독립적으로 자기 계획안을 병렬 작성**.
  워커에는 `PROPOSE` 핸드오프("너 자신의 접근을 자유롭게 제안하라, 구현 금지"), 매니저도 동시에 자기 안 작성.
  각 제안을 REVIEW_RESPONSE로 회수.
- (0c) 모든 제안(워커들 + 매니저)의 **아이디어별 장단점을 분석**해 좋은 부분을 결합한 **최선의 최종안** 도출
  (어떤 안에서 왔는지·트레이드오프 명시). 한 초안을 추인하는 게 아니라 독립적 발산 후 수렴이 목적. 이후 루프 진행.

매니저는 `AIMemory/agents.md`와 `aimux agents`(상태 보드)를 보고 운영하는 폐루프:
1. **분해** — 최종안을 가능한 독립적인 단위로(테스트/검증 단위 포함). **의존성 기준, 순서 기준 아님(T37)**:
   "1단계→2단계→3단계"는 서술 순서지 의존성 그래프가 아님 — 다른 단위의 산출물을 실제로 소비하는
   단위만 직렬화. **핸드오프 1건 = 1단위**("A 하고 B 하고 C" 묶음은 한 워커 안에 병렬성을 숨겨
   나머지를 idle로 만들고, 하위 단계 하나가 실패하면 묶음 전체가 막힘).
2. **배정** — idle이고 역량 맞는 에이전트에 병렬 배정. **현재 막히지 않은(ready) 단위는 전부 동시에**
   다른 idle 워커들로 살포하고, 워커가 돌아올 때마다 그 반환이 풀어준 단위를 **즉시** 후속 배정.
   ready 단위가 있는데 워커가 idle이면 = 라우팅 실패 — 더 쪼갬(구현 vs 테스트 하네스 vs 문서,
   모듈별; 완료 단위의 검증은 다른 워커가 다음 단위를 만드는 **동안** 병행). 라우팅 제약:
   - **데이터 민감도 우선**: 개인/민감/기밀 데이터는 **qwen(완전 로컬) 전 담**, 클라우드 에이전트
     (claude/opencode/antigravity)에는 절대 전달 금지.
   - **qwen은 약함**: 자료조사·simple shell script·소규모 기계적 작업만.  주요/복잡 작업은
     **opencode·antigravity**.
3. **모니터** — "idle≠완료". 무응답은 자동통지로 받음. 실제 산출물을 확인.
4. **실패 대응** — 버리지 말고 **진단 → 적응(범위 축소·"지금 적용"·"실제 실행") → 1회 재시도 →
   다른 idle 가용 에이전트로 재배분**. 원인·해법을 `agents.md` Learnings에 기록.
5. **검증도 위임** — 통합/테스트/검증은 *작업*이지 judgment가 아님. "테스트/하네스를 작성하고 **실행**해
   증거 보고"를 idle 워커에 VERIFY 단위로 위임. 매니저는 분해/증거기반 accept·재배분/최종 조립만.

이 정책은 워커 초기 브리프(`AGENTS.md`/`AGENTS.md`/`QWEN.md`)와 런처의 매 니저 온보딩, `tmux-handoff.md`
Roles·Orchestration strategy에 함께 명시됨.

---

## 6. 명령 레퍼런스

### `AIMemory/bin/aimux`
- `panes` — 패널 레지스트리(id·name·kind·init·위치).
- `agents` — 상태 보드(name·kind·idle/busy/waiting·처리중). 상태기반 배정/재배분용. `waiting`=권한 프롬프트 대기(보류 중, 재배분·실패 아님)이라 `idle`과 구분(T29).
- `name <name> [--kind <k>] [--pane <id>]` — 현재/지정 패널 이름·종류 지정 + 보더 고정.
- `enqueue --to <name> --handoff <path> [--roles R[+R]] [--from <pane>] [--type request|response] [--reply-to <id>] [--priority N]` — 큐 적재.
- `dispatch [--interval S] [--once] [--force]` — 디스패처 루프(단일 인스턴스, flock).
- `status` — 큐·디스패처 상태(+ 세션 패널).
- `send-test --to <name>` — 하이파이브 스모크테스트.
- `cancel <req-id>` — 대기/처리중 요청 취소.
- `resolve <req-id> [--note <t>]` — 매니저의 대역외 종결 선언: 직접 검증·수락한 유닛을 닫음(notice 미발행 + 관련 후속물 드롭). 미완료 유닛에는 사용 금지.
- `shell [project-dir]` — 단일 명령 수명주기: `aimux-up`으로 기동+attach, detach(Ctrl-b d) 시 finalize&종료[Y]/유지[n]/재접속[a] 질문. 세션 안에서 이미 `down`했으면 그냥 종료. `AWM_SHELL_ON_DETACH=down|keep|ask`로 비대화 지정(tty 없으면 keep — 조용히 죽이지 않음). tmux 안에서 실행하면 감독 불가라 aimux-up으로 위임. 런처가 `.aimux/last-session`에 세션명을 기록해 이 명령이 자기 세션을 식별(T35).
- `down [--yes] [--purge]` — 현재 세션 finalize+종료(다른 세션/서버 무영향; `--yes` 없으면 프리뷰).

### `AIMemory/bin/aimux-up` (런처)
- 매니저(좌상)+디스패처(좌하) 좌측 컬럼, 워커 우측 균등 스택으로 세션 기동.
- 후보 풀(로스터): `AIMemory/agents.roster`(기본; `AWM_ROSTER`로 교체)에 `[manager]`/`[worker]` 두 섹션, 각 줄 `label | command`. 모델 태그·후보를 자유롭게 추가/변경. `AWM_CONFIG` 파일을 주면 풀·선택을 모두 건너뛰고 전체 로스터를 대체(첫 줄=매니저).
- **역할 선택(기동 시)**: ① `[manager]` 풀에서 매니저 1명 객관식 → ② `[worker]` 풀에서 워커 다중 선택(번호/이름, `all`). `AWM_MANAGER`/`AWM_WORKERS`로 프롬프트 생략 가능. 매니저 pane은 어떤 CLI를 골라도 항상 `manager`로 명명(워커가 `--to manager` 반환). 첫 워커=split h(우측 컬럼 개시), 나머지=v.
- **세션 브리프 생성**: 선택된 역할에 맞춰 매니저 브리프 1개 + 워커별 브리프를 `AIMemory/briefs/{manager,worker}.md` 템플릿에서 세션 state 디렉터리로 렌더링하고, 각 pane이 자기 브리프를 1차로 읽게 함(`@awm_init_file`). 커밋된 `CLAUDE.md`/`AGENTS.md`/`AGENTS.md`/`QWEN.md`는 **수정하지 않음** — 생성 브리프 + 온보딩 메시지가 역할의 권위 → 어떤 CLI든 매니저/워커로 기동 가능(T30).
- **독립 실행 ↔ 멀티 실행 양립**: 커밋된 자동로드 브리프(`AGENTS.md`/`AGENTS.md`/`QWEN.md`)는 **역할 중립** — 단독 실행 시 독립 에이전트로 동작(PROJECT.md/CLAUDE.md 따라 프로젝트 규칙 적용), aimux로 기동되면 pane에 붙는 `ROLE:` 메시지 + 세션 브리프가 이를 덮어써 매니저/워커가 됨. 같은 폴더에서 CLI를 단독으로 띄워도 워커로 멈추지 않음(T31).

---

## 7. 설정 (환경변수)

aimux:
- `AIMUX_SESSION` — pane 라우팅을 이 세션으로 한정(런처가 자동 설정).
- `AIMUX_STATE` — 큐/lock 상태 디렉터리(기본 `AIMemory/.aimux`; 런처는 세션별).
- `AIMUX_MEM_DIR` — 프로젝트 AIMemory 디렉터리. `AIMUX_WORKLOG`·`AIMUX_TMP`·기본 `AIMUX_STATE`의 베이스. 미설정 시 **호출된 aimux 바이너리 위치**(`$_self/..`)로 추정 — 런처가 패널에 세션 고정(아래 세션 격리 참조). (v0.1.1)
- `AIMUX_WORKLOG` — work.log 경로(기본 `$AIMUX_MEM_DIR/work.log`).
- `AIMUX_TMP` — 스크래치(기본 `$AIMUX_MEM_DIR/tmp`).
- `AIMUX_DISPATCH_INTERVAL`(2s) / `AIMUX_IDLE_SAMPLE_SECS`(1.2s) / `AIMUX_CAPTURE_LINES`(40) — 폴링·idle 감지.
- `AIMUX_ENTER_SETTLE`(0.4s) / `AIMUX_ENTER_TRIES`(3) — paste 후 제출 Enter 전후 대기와, 화면 변화로 제출이 확인될 때까지의 Enter 재시도 횟수.
- `AIMUX_ENTER_SETTLE_OPENCODE`(0.9s) — opencode 전용 제출 대기. opencode TUI는 Enter-제출 렌더가 기본 창(0.4s)보다 느려 화면검사가 제출 전에 끝나 **거짓 RETRY/STUCK**(실제론 제출됨)을 남겼다. CLI별 오버라이드는 `enter_settle_for()`가 pane의 `@awm_agent_kind`로 선택. (v0.1.1)
- `AIMUX_MIN_INFLIGHT_SECS`(4s) — 해제 전 유예.
- `AIMUX_RELEASE_IDLE_CYCLES`(3) — 해제에 필요한 연속 idle 횟수.
- `AIMUX_WAIT_NOTICE_CYCLES`(2) — 저위험 대기 프롬프트를 매니저에게 넘기기 전 연속 대기 관찰 횟수(사용자가 먼저 답할 유예; 고위험 표면화는 즉시).
- `AIMUX_WAIT_TIMEOUT`(240s) — **응답 대기 프롬프트에 막힌** 패널을 푸는 별도 짧은 타임아웃. 프롬프트-막힘 패널은 사람/매니저가 답해야만 풀리고 스스로 response로 해소되지 않으므로, 하드 타임아웃(900s)까지 붙들지 않고 4분에 freed-notice와 함께 해제 → 매니저가 재라우팅. 0=끔(하드 타임아웃으로 폴백). (v0.1.1)
- `AIMUX_INFLIGHT_TIMEOUT`(900s) — 하드 타임아웃.
- `AIMUX_INFLIGHT_TIMEOUT_MAX`(2700s) — 타임아웃 시점에 패널이 **여전히 busy**(화면 변동, 프롬프트 막힘 아님)면 긴 단일 턴(대용량 문서 변환/빌드)으로 보고 해제 대신 이 천장까지 **연장**. idle/막힘이거나 천장 도달 시에만 해제 → "타임아웃·무응답" 거짓 보고 방지. (v0.1.1)
- `AIMUX_VLOG`(1) — 라이브 피드(0=끔).
- `AIMUX_WAIT_PATTERN` — 사용자 입력 대기 프롬프트 감지 ERE(대소문자 무시). CLI별로 튜닝(관찰한 마커를 agents.md에 기록).
- `AIMUX_WAIT_RISK_PATTERN` — 대기 프롬프트 중 **고위험**(배후 동작이 파괴적/비가역/외부노출/자격증명) 판별 ERE(대소문자 무시). 매칭=사람에게만 에스컬레이션, 미매칭=매니저가 대신 응답. 빈 값=전부 저위험 취급. UI 옵션("always allow / don't ask again")은 고위험 마커가 아님 — 동작으로 판정(T29).

aimux-up:
- `AWM_ROSTER` — 후보 풀 파일(기본 `AIMemory/agents.roster`).
- `AWM_MANAGER` — 매니저 사전선택(label 또는 1-기반 index). 매니저 프롬프트 생략.
- `AWM_WORKERS` — 워커 사전선택(label/index 콤마·공백 목록 또는 `all`). 워커 프롬프트 생략. (이전의 "워커 개수" 의미를 대체.)
- `AWM_CONFIG` — 전체 명시 로스터 파일(첫 줄=매니저). 풀·선택 프롬프트를 모두 건너뜀.
- `AWM_SESSION` — 고정 세션명(기본 `aimux-<names>-yymmdd-HHMMSS`).
- `AWM_AUTO_APPROVE=1` — 권한/trust 프롬프트 없이 기동: claude=`--dangerously-skip-permissions`, codex=`--dangerously-bypass-approvals-and-sandbox`(매우 위험 — 외부 샌드박스 환경 전용).
- `AWM_DISPATCH_HEIGHT`(10) — 디스패처 패널 높이 %.
- `AWM_CLI_WARMUP`(6s) — CLI 부팅 대기.

---

## 8. 레이아웃·패널 레지스트리

```
┌──────────┬─────────────┐
│ manager  │ antigravity │
│          ├─────────────┤
├──────────┤ opencode    │   우측 = 워커 균등 스택
│ dispatch ├─────────────┤
│ (~10%)   │  qwen       │
└──────────┴─────────────┘
```
라우팅은 tmux pane 옵션 `@awm_pane_name`(고정 라우팅 이름)·`@awm_agent_kind`·`@awm_init_file`로.
CLI가 타이틀을 덮어써도 보더에 고정 이름이 유지됨.

---

## 9. 에이전트 특성 (요약 — 상세는 agents.md)

- **claude-code** — 강함·신뢰. 편집 자율 적용. 매니저·워커 어느 역할로도 기동 가능(로스터 선택).
- **opencode** — 가장 신뢰. 멀티파일 구현·재배분 1순위.
- **codex** — 브리프는 `AGENTS.md` 공유(opencode와 동일). 설정은 `~/.codex/config.toml`(권장값 `templates/codex/config.toml`), 프로젝트 trust 필요. 자율 실행은 `AWM_AUTO_APPROVE=1` 또는 `approval_policy="never"`+trust.
- **antigravity** — 유능하나 취약: 편집승인 모드 꺼지면 *plan만*(Shift+Tab 필요), tool-call 다발 시
  오류 → 단일파일·단일스텝.
- **qwen(gemma4:e4b)** — 약한 **로컬** 모델. 도구호출을 서술만 하는 경향("실제 실행" 지시 필요).
  민감데이터 전담 + 단순작업 한정. 주요작업 금지.

---

## 10. 파일 맵 + 이력

```
make_Harness/
├── README.md(하네스 개요)  DESIGN.md(본 문서)  HARNESS-CHANGELOG.md(스캐폴드 개발 이력)
├── CHECKLIST.md  PROJECT.md                   복사한 프로젝트가 채우는 템플릿
├── AGENTS.md  AGENTS.md  QWEN.md            역할 중립 CLI 자동로드 브리프(독립/aimux 양립)
├── templates/codex/config.toml             codex CLI 권장 설정 레퍼런스
├── claude/                                  가이드(core/profiles/단계)
└── AIMemory/
    ├── PROTOCOL.md(AICP)  tmux-handoff.md(전송·전략)  agents.md(역량 원장)
    ├── agents.roster(매니저·워커 후보 풀)  briefs/{manager,worker}.md(역할 브리프 템플릿)
    ├── work.log  handoff_example.md
    └── bin/{aimux, aimux-up}
```
스캐폴드 개발 이력·근거는 `HARNESS-CHANGELOG.md`(복사 프로젝트의 단계 체크리스트는 `CHECKLIST.md`). 런타임(`AIMemory/.aimux/`, `AIMemory/tmp/`)은 `.gitignore`.

---

## 11. 런 계측 + 논문화

목적: 완료된 멀티에이전트 런을 **별도 프로젝트에서, 이 하네스로** 논문화. 두 부분으로 분리:

**(가벼운) 실행 하네스 계측** — `aimux report`가 디스패처의 자기 기록(`.aimux/done`·`failed`의
`*.req`, 기계 생성=신뢰)에서 인용 가능한 run-summary를 산출:
- `aimux report` 사람용 요약 / `--json` JSON / `--write`로 **버전 스냅샷** 저장.
- **버전 관리**: 스냅샷은 `AIMemory/run-summary/vNNN-<ts>[-label].json`으로 시점별 보존,
  `AIMemory/run-summary.json`은 항상 **최신** 미러(기본 읽기 대상). 시점 간 비교 분석 가능.
- **매니저 신호 체크포인트**: 매니저가 대규모 요구 해결/마일스톤에서 `aimux checkpoint --label <m>` →
  디스패처가 신호를 받아 자동으로 버전 스냅샷 작성(디스패처와 협업; 디스패처 없으면 즉시 작성).
- `aimux down --yes`는 종료 전 최종 스냅샷(`final`)을 남김.
- 스키마 `aimux-run-summary/1`:
  - `totals{requests,responses,notices,highfives,redispatches}`
  - `release_reasons{response-seen,idle-stable,unacked,timeout,pane-gone}`
  - `durations_seconds{session_span,turnaround_min/avg/max}`
  - `per_agent{<name>{requests,completed,failed}}` (completed=응답 반환, failed=무응답/unacked/timeout)
  - `handoffs[]{type,to,handoff,delivered,released,release_reason}`
  - `redispatches`=토픽당 첫 배정 이후 추가 요청(재시도+재배분), `notices`=무응답 사건(재배분 트리거 프록시).
- 정량 주장은 run-summary.json(기계), 서사는 `work.log`(LLM 작성)에서.

**(별도 프로젝트) 논문 작성 스킬** — `paper` 프로파일(`claude/profiles/paper.md`):
완료 프로젝트의 `AIMemory/`(run-summary.json + work.log + handoff_*)를 입력으로 새 세션에서 실행 →
`templates/paper/`를 채워 논문화. 산출물 **PDF + Word(.docx)**, **시각자료**(실험 구조도 SVG +
표/pgfplots 차트; PDF·Word 모두 임베드), **버전 관리**(피드백 반영 전 `make snapshot` → `versions/vNNN`,
통째로 갈아엎지 않고 증분 수정). 모든 결과는 아티팩트 필드와 1:1 추적. PROJECT.md `profile: paper`로 진입.빌드 도구: latexmk+xelatex, pandoc, rsvg-convert, ghostscript.

---

## 12. 설치/업데이트 하위시스템 및 개발 모드

하네스 스캐폴드(make_Harness) 자체의 배포, 업데이트, 독립 개발을 위한 하위시스템과 전용 모드 설계입니다.

### 12.1 GitHub 설치/업데이트 하위시스템

스캐폴드를 일반 프로젝트 폴더에 손쉽게 설치 및 최신 상태로 유지하기 위한 도구 세트입니다.
- **배포 매니페스트 (`harness-manifest.json`)**: 스캐폴드 파일을 다음 세 분류로 관리합니다.
  - `managed`: 업데이트 시 무조건 덮어쓰는 관리 대상 파일 (`CLAUDE.md`, `claude/`, `AIMemory/PROTOCOL.md`, `templates/` 등).
  - `seed`: 최초 설치 시에만 생성되고 업데이트 시 기존 수정사항을 유지하기 위해 보존하는 시드 파일 (`PROJECT.md`, `README.md`, `CHECKLIST.md`, `.env.example` 등).
  - `skipped`: 설치/업데이트 시 일체 건드리지 않는 런타임 및 상태 데이터 (`work.log`, `.aimux/`, `tmp/` 등).
- **저장소 확인 체인 (Account-Agnostic)**: 업스트림 계정/레포명을 하드코딩하지 않으며, 다음 순서로 확인합니다.
  1. `HARNESS_REPO` 환경 변수
  2. `.harness/source` 파일에 기록된 `repo=<slug>` 포인터
  3. `gh repo view --json nameWithOwner -q .nameWithOwner` (git origin 원격 조회)
- **설치 및 업데이트 스크립트**:
  - `bin/harness-install [--repo R] <target-dir>`: 빈 디렉토리에 최신 릴리스 zip을 내려받아 `managed`와 `seed` 전체 트리를 설치하고 `.harness/source`를 기록합니다.
  - `bin/harness-update [--dry-run] [--repo R]`: 기존 프로젝트 디렉토리에서 매니페스트 분류 규칙에 맞춰 하네스 파일을 최신화합니다. `--dry-run`은 변경을 가하지 않고 덮어써지거나 추가될 파일 요약본을 출력합니다.
  - *Fallback 메커니즘*: `gh` CLI가 없으면 `curl`로 GitHub Releases 최신 API를 조회해 zip 주소를 파싱하여 직접 다운로드합니다 (No `jq` 의존성).
- **배포판 검증 (`make-dist.sh`)**: `git archive`를 통해 커밋된 추적 파일만 zip으로 아카이빙한 후, 압축을 풀어 메인테이너 GitHub 사용자명·계정, 개인 이메일, 홈 디렉토리 경로, API 키 등의 개인식별 정보(Identifiers)가 포함되었는지 엄격하게 정규식 스캔합니다. 감지되면 즉시 빌드를 취소하고 zip을 파기해 유출을 원천 방지합니다.
- **릴리스 자동화 (`harness-release.sh`)**: 유지보수자 전용 스크립트로, `--bump <major|minor|patch>` 버전업 → `./make-dist.sh` 패키징 → `gh release create` 배포를 자동화합니다. `gh`가 없으면 `curl` GitHub API로 릴리스를 만들고 zip 바이너리를 업로드합니다.
  - **드라이런 보증**: `--dry-run` 모드에서는 `VERSION` 파일 수정, zip 빌드, symlink 갱신 등 디스크 상태를 단 1바이트도 수정하지 않고, 최종적으로 실행될 `gh` 릴리스 생성 명령어와 바인딩될 정보를 출력하기만 합니다.

### 12.2 하네스 자체 개발 모드 (make 모드)

`make_Harness` 자체를 리팩토링하거나 스킬을 추가·개발하는 메타 개발 세션 기능입니다.
- **진입**: `AIMemory/bin/aimux-up make [workers...]` 또는 `aimux-up dev`
- **구동 가드**: 실행 시 `PROJECT_DIR`을 하네스 자체 루트로 고정하며, 대상 폴더에 `DESIGN.md`, `HARNESS-CHANGELOG.md`, `VERSION`이 모두 존재하는지 사전 검증하여 하네스 개발 환경 밖에서 잘못 실행되는 것을 차단합니다.
- **역할 브리프 렌더링**: 세션 briefs 폴더에 일반 프로젝트용 `manager.md`/`worker.md`가 아닌, 하네스 개발에 맞게 서술된 `briefs/manager.make.md`와 `briefs/worker.make.md`를 템플릿으로 사용하여 역할 브리프를 렌더링합니다.
- **온보딩 프레이밍 스왑**: 매니저 패널 기동 시 pasted되는 역할 알림 메시지에서 일반 프로젝트 인테이크/가이드 실행 지침을 스왑하고, "이 프로젝트는 `make_Harness` 자체를 개선하는 것"임을 주입하고 T-시리즈 이력 작성, SemVer 및 `VERSION` 관리, `smoke.sh` 및 `make-dist.sh` 검증 지침을 안내합니다.
- **세션 지속성**: manifest 파일에 `mode=make`를 기록하여 `aimux-up continue` 시에도 세션이 메타 개발 모드임을 복원해 `make.md` 전용 브리프를 올바르게 재렌더링합니다.

