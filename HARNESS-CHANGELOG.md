# HARNESS-CHANGELOG.md — make_Harness 스캐폴드 자체 개발 이력

> 이 파일은 **make_Harness 스캐폴드 자체**의 누적 개발 변경 이력(T 시리즈)이다.
> 이 폴더를 복사해 부트스트랩한 **일반 프로젝트의 단계별 체크리스트는 `CHECKLIST.md`** 를 쓴다(plan 단계가 채움).
> 스캐폴드를 직접 더 개발할 때만 이 파일에 T 항목을 이어 적는다.

---

## 릴리스 (SemVer)

> 하네스 버전의 **단일 출처는 루트 `VERSION` 파일**(SemVer). 릴리스 전
> `./bump-version.sh {major|minor|patch}` 로 올리고, 아래에 항목을 추가한 뒤
> 커밋한다. 배포 zip은 `./make-dist.sh` 가 `VERSION` 을 읽어
> `dist/make_Harness-v<버전>-<날짜>-<sha>.zip` 으로 만들고
> `dist/make_Harness-latest.zip`(심볼릭 링크)·`dist/LATEST.txt` 로 "최종본"을 표시한다.
> 규칙: 기능 추가=MINOR, 버그수정=PATCH, 호환 깨짐=MAJOR.

- **v0.5.0** — 2026-06-15 — 외부 pptx 경험 학습을 하네스 pptx 제작 역량에 반영, 일반화된 덱 스킬 추가 (MINOR)
  - **일반화된 pptx-deck 스킬 추가** (`.claude/skills/pptx-deck/`): `pptx-deck`은 하네스에 포함되어 배포되는 추적·이식 가능한 스킬.
    - `pitfalls.md` 추가: pptxgenjs 옵션 객체 변이(in-place mutation), 8-char hex→검정 버그, 슬라이드 전체 이미지→편집 불가, 제목 밑 악센트 라인 금지(AI 생성 특징), 좁은 연결 상자 한글 1행/1자 래핑, 텍스트 오버플로우 휴리스틱의 필요성 등 10가지 함정 정리
    - `audit_pptx.py` 추가: 외부 발표자료 프로젝트의 덱 감사 스크립트를 일반화(포트), 편집 가능성·경계 초과·텍스트 오버플로우·금칙어(보안 용어 기본값, 호출자가 `--forbidden`으로 확장) 검사, 기대 문자열 확인 `--expect` 선택 지원, 최종 행에 기계 판독 가능 `PASS=n FAIL=m` 출력
    - `SKILL.md`·`build-and-verify.md`에 네이티브 pptxgenjs vs HTML→PNG 접근법 안내, 샌드박스 환경 제한(리브레오피스 부재 시 정적 감사 폴백) 명시
    - 기존 외부 발표자료 덱 스킬의 메커니즘(60-30-10 팔레트 방법론, 타이포그래피 척도, 구성요소 패턴, 12장 학회 발표 슬라이드 매핑)을 브랜드 중립 기본값으로 일반화
    - 기본 팔레트: 중립 학술 색상(딥 네이비·화이트·슬레이트), 특정 기관 브랜드 색상은 "예: 브랜드 팔레트 재정의(선택 사항)" 블록으로만 표시
    - `build-and-verify.md`에 pptxgenjs 제작 방법론(px→인치 변환, option 객체 Factory 함수 패턴, 6자리 16진수+투명도, ROUNDED_RECTANGLE·OVAL·LINE 기본 도형 가이드) 수록
  - **paper 프로필 덱에 함정 반영 및 감사 연동**:
    - `build_pptx.js`: 모든 내용 슬라이드의 제목 밑 악센트 바(10개) 제거 — AI 생성 특징 방지
    - `Makefile`: `pptx-qa`에 정적 감사 연동(`audit_pptx.py --forbidden aimux dispatcher handoff work.log run-summary per_agent`), 기존 `../.claude/` 상대경로 버그 수정, 스크립트 경로 `pptx/`→`pptx-deck/`로 변경
    - `slides/README.md`: QA 워크플로에 정적 감사 단계 문서화
  - **검증**: `node --check` 통과, 덱 재빌드(12슬라이드, 168KB), 감사 4/4 PASS(금칙어 0), pptx-deck 파일 기관 식별자 0히트, make-dist.sh 식별자 검사 통과, smoke.sh PASS

- **v0.4.0** — 2026-06-15 — GitHub 설치/업데이트 하위시스템 추가 및 aimux-up 자체 개발(make) 모드 지원 (MINOR)
  - **GitHub 설치 및 업데이트 하위시스템**:
    - `harness-manifest.json` 매니페스트 도입으로 `managed`(항상 업데이트), `seed`(최초 1회 설치), `skipped`(보존) 파일 관리 체계 수립
    - `bin/harness-install` 및 `bin/harness-update` 추가: 최신 릴리스 zip을 내려받아 매니페스트에 따라 파일 적용
    - `gh` CLI 부재 시 `curl` GitHub API 폴백 지원 (No `jq` 의존성)
    - `make-dist.sh` 배포판 생성 시 민감한 개인식별 정보(메인테이너 계정·사용자명, 홈 경로 등) 누출 탐지 및 빌드 차단 강화
    - 유지보수자용 `harness-release.sh` 릴리스 자동화 스크립트 추가 (버전 범프, dist 빌드, GitHub Release 생성 및 curl 업로드 폴백)
    - `harness-release.sh` 드라이런 `--dry-run` 보증: 디스크 상태 변경 및 파일 빌드를 일체 하지 않고 실행 명령어만 출력하도록 수정
  - **하네스 자체 개선을 위한 개발 모드 (make 모드)**:
    - `aimux-up make` 진입 및 `aimux-up dev` 서브커맨드 지원
    - 구동 가드: `DESIGN.md`, `HARNESS-CHANGELOG.md`, `VERSION` 존재 여부를 검증하여 비Scaffold 폴더 내 오실행 차단
    - 전용 개발 역할 브리프인 `briefs/manager.make.md` 및 `briefs/worker.make.md` 템플릿 추가 및 렌더링 지원
    - 매니저 온보딩 역할 메시지를 하네스 자체 개선 가이드(SemVer, T-시리즈 변경점 작성, smoke/make-dist 검증)로 동적 스왑
    - 세션 manifests에 `mode=make`를 저장하여 `continue`로 다시 세션을 띄울 때도 메타 개발 브리프를 재렌더링하도록 지원
  - **검증**: `bash -n` 전 파일 통과, `smoke.sh` 테스트 5/5 통과, dry-run에서 VERSION 보존 및 파일 비생성 확인, guard 오실행 차단 실증 완료.

- **v0.3.4** — 2026-06-15 — aimux-up이 `skills-lock.json` 기반으로 누락 스킬 자동 설치 (MINOR)
  - **aimux-up: 실행 시 `skills-lock.json`을 읽어 `.claude/skills/`에 없는 스킬을 자동 설치**
    - 신규 `aimux skills-sync` 서브커맨드를 패널 생성 전에 비차단 호출
    - tarball+curl fetch(공개 repo, 인증 불필요; main→master 폴백)
    - python3 파싱, **missing-only**, 설치 후 sha256 무결성 검증(불일치 시 경고 후 유지)
    - 모든 실패는 경고 후 계속(launch 비차단)
    - 테스트용 env 오버라이드 (`AIMUX_SKILLS_LOCK`/`AIMUX_CLAUDE_SKILLS_DIR`/`AIMUX_SKILLS_FETCH_CMD`)
  - **검증**: real fetch anthropics/skills 59파일 정상, hash 불일치 경고+유지, bogus repo 실패+exit 0

- **v0.3.3** — 2026-06-15 — paper 프로필 발표자료(.pptx) 출력 + 디스패처 paste `-p` 수정 (PATCH)
  - **paper 프로필: 발표자료(.pptx)를 PDF·DOCX에 이어 기본 산출물로 추가**
    - `templates/paper/slides/` pptxgenjs 스캐폴드(12장 학회 덱, 도메인 중립 CONTENT 섹션, Teal Trust 팔레트, 그림 동적 임베딩)
    - Makefile `pptx`/`pptx-qa` 타깃(graceful degradation, node 부재 시 경고 후 생략)
    - `snapshot.sh`가 슬라이드 소스+덱 버전 보존
    - `paper.md` 절차/규칙 갱신(발표자노트까지 내부 산출물명 금지)
    - `templates/paper/.gitignore` 추가(빌드 산출물·node_modules 오염 차단)
  - **디스패처: `deliver()`의 `paste-buffer`에 `-p`(bracketed paste) 추가**
    - antigravity(Gemini CLI) 등에서 멀티라인 핸드오프가 첫 줄만 제출되고 나머지가 큐로 분리되던 버그 수정(다음 세션 재기동부터 적용)
    - `AIMemory/agents.md` Learning에 원인·증상·수정 기록
  - **검증**: end-to-end 빌드+QA 통과(12슬라이드, 내부명 0누출), paste `-p` 수동 시험 확인(multi-line 정상 단일 paste), `bash -n` 전파일 통과, gitignore 스테이징 검증 통과

- **v0.3.2** — 2026-06-15 — 디스패처가 매니저 패널을 false-`waiting`으로 오판해 전달이 막히던 문제 수정 (PATCH)
  - **증상**: 워커가 매니저로 보낸 응답이 전달되지 않고 대기에 묶이며, `aimux agents` 보드도 매니저를 `waiting`으로 잘못 표시(실제로 v0.3.1 릴리스 전달이 이 버그로 교착됨).
  - **원인**: `pane_waiting`이 패널의 **보이는 화면 전체**를 `AIMUX_WAIT_PATTERN`과 매칭하는데, 매니저는 임의 텍스트(핸드오프 본문·PROTOCOL 발췌·인용된 워커 프롬프트)를 계속 렌더링하므로 그 텍스트가 패턴("Do you want to|Continue?|Proceed?|approve this|Press Enter…")에 오탐. 두 choke point(`deliver_pending` 전달 가드, `process_inflight` idle-streak 리셋)에 매니저 예외가 없어 전달 차단·240s wait-timeout 홀드를 유발했고, agents 보드도 동일하게 오표시.
  - **수정**: 세 지점에 매니저 패널 예외 추가 — 전달 가드/`process_inflight` waiting-block/agents 보드에서 매니저는 `pane_waiting` 판정을 건너뜀(인플라이트+idle 가드로 충분하며, 매니저의 진짜 프롬프트는 별도로 인간에게 surfacing). 워커의 wait 감지는 그대로 유지.
  - **검증**: `bash -n` 통과; 가드 진리표 4조합 확인(매니저+waiting→전달, 워커+waiting→차단 유지)으로 연산자 우선순위 역전 없음 확인. 실행 중인 디스패처는 다음 세션 기동 시 반영됨.
- **v0.3.1** — 2026-06-15 — aimux-up 기본 로스터를 실행 환경에 독립적으로 정의 (PATCH)
  - **증상**: 하네스를 다른 위치에 설치/실행하면 `aimux-up`의 기본 manager·worker 구성·순서가 의도(claude manager + antigravity·opencode worker)와 다르게 나옴.
  - **원인**: 기본값 출처가 둘 — 외부 `AIMemory/agents.roster`(load_roster가 순서+`*`-default 해석)와 하드코딩 `MGR_FALLBACK`/`WRK_FALLBACK` 배열. 로스터 파일을 못 찾으면 fallback으로 빠지는데, `*`-default 집합(`WRK_DEFAULT`)이 파일 파싱 때만 채워져 fallback에선 비어 기본이 "all"(qwen 포함)·다른 순서로 변질. 게다가 로스터 경로가 환경의존 `PROJECT_DIR` 기준이라 설치 위치/호출 방식에 따라 "파일 못 찾음".
  - **수정**: 단일 출처화 — 임베디드 기본 로스터(외부 파일과 순서·`*`-마크 동일)를 동일 `load_roster`로 파싱해 `WRK_DEFAULT`·풀 순서를 항상 동일하게 계산. 해석 순서 `AWM_ROSTER → $PROJECT_DIR/AIMemory/agents.roster → 스크립트-상대 $SELF/../agents.roster → 임베디드`. `MGR_FALLBACK`/`WRK_FALLBACK` 제거.
  - **검증**: 7개 환경 시나리오(기본/파일없음/다른cwd/PROJECT_DIR-타지/심볼릭링크/AWM_ROSTER override/`bash -n`) 전부 PASS — 어떤 환경에서도 claude + antigravity·opencode.
- **v0.3.0** — 2026-06-15 — gemini 에이전트를 antigravity(`agy`) CLI로 교체 (MINOR)
  - **무엇**: 해러스의 표준 클라우드 워커였던 `gemini`(gemini-cli)를 제거하고 Google **Antigravity** CLI(`agy`)로 전면 교체. gemini 흔적을 live 파일 전반에서 제거.
  - **왜**: 사용자가 antigravity로 전환 — gemini를 더 이상 워커/매니저 후보로 두지 않음.
  - **주요 변경**:
    - `aimux-up`: `kind_of`/`initfile_of`에 `agy|antigravity` 추가(brief=`AGENTS.md`), `resume_session_flags`=`--continue`(agy는 세션 ID 사전지정 불가), `launch_session_flags` 비움, `AWM_AUTO_APPROVE`에 `antigravity`→`--dangerously-skip-permissions` arm, `WRK_FALLBACK`·nested-project 경고·매니저 온보딩 문자열 갱신, gemini-cli case 전부 제거.
    - `agents.roster`: `[manager]`·`[worker]` 양쪽에 `antigravity | agy`(워커 기본선택).
    - `GEMINI.md` 삭제 — agy는 `AGENTS.md`를 자동 로드.
    - `.gitignore`·`make-dist.sh`: agy는 프로젝트-로컬 config dir를 만들지 않음(실증 확인) → 잘못된 항목 정리.
    - `agents.md` 및 문서 다수(`tmux-handoff.md`, `briefs/*`, `README.md`, `DESIGN.md`, `claude/*`, `/verify-project` 스킬, 논문 템플릿) gemini→antigravity 반영.
  - **검증**: aimux 매니저-워커 협업으로 분해·구현·독립 검증 — `bash -n` 통과, 함수 dry-run 정합, `command -v agy` 해석 확인, live 파일 `gemini` grep=0 (7개 기준 전부 PASS).
  - **주의**: `agy`는 최초 Google OAuth 인증 필요(미인증 시 워커 기동 전 `agy` 로그인).

- **v0.2.1** — 2026-06-12 — `aimux-up` 에이전트 CLI 해석 강화: rc-설정 CLI 실행 실패 수정 (PATCH)
  - **증상**: `~/.bashrc`에서 `claude` 등을 alias·shell 함수·rc-추가 PATH(`~/.claude/local`·nvm 등)로
    설정한 환경에서 `aimux-up`이 실행 초기에 에이전트를 못 띄움 + 거짓 "not in PATH" 경고.
  - **원인 1 (실행 실패)**: 에이전트 런치가 `env $PENV claude …` 였음 — `env`는 execvp라 PATH의
    실제 파일만 실행, alias/함수인 `claude`는 띄우지 못함.
  - **원인 2 (오탐)**: preflight `command -v` 가 이 스크립트의 비대화형 셸에서 실행 → 사용자 rc를
    안 읽어 거짓 경고.
  - **수정**: `resolve_cli()` 추가 — 사용자 대화형 셸(`$SHELL -ic`, Ubuntu 기본 .bashrc 조기 return
    회피 위해 `-i` 필수)에 물어 각 CLI 위치를 찾음. 디스크 실행파일이면 절대경로로 고정(pin),
    alias/함수면 그대로 두고 패널 셸이 해석, 어디에도 없으면 경고만(치명적 아님). 에이전트 런치를
    `env $PENV …` → `$PENV …`(셸 변수할당 프리픽스)로 변경해 패널 대화형 셸이 alias/함수/ rc-PATH를
    해석하면서 변수는 동일하게 export. 매니페스트는 원래 명령(`claude`) 그대로 저장해 이식성 유지
    (`continue` 때 재해석). dispatcher 줄은 `$AIMUX`가 항상 절대경로라 `env` 유지.
- **v0.2.0** — 2026-06-12 — `/verify-project` 스킬 추가: 주어진 프로젝트 검증 하네스 (MINOR)
  - 실 프로젝트(`test/test_AGTplatform`)에서 작성한 스킬을 하네스 본체로 반영.
  - **무엇**: 이미 존재하는(서드파티 포함) 프로젝트 폴더를 **코드검증→설치검증→기능검증→
    적대적기능검증→종합**(T0~T5)으로 검증하고 단계별 증거 보고서를 산출하는 슬래시 스킬.
    `ideate`(사전 구체화)·`paper`(사후 논문화)와 대칭을 이루는 세 번째 축 — **검증**(빌드 아님,
    코드 미수정·발견만 보고).
  - **표면 적응**: web/api/cli/lib/tui를 T0에서 자동감지(`--surface`로 강제 가능)해 기능검증
    드라이버를 전환 → 임의의 프로젝트에 일반 적용. 각 단계 끝 사용자 게이트(G0~G4, 명확하면
    fast-track).
  - **aimux 연계**: 매니저 역할로 동작하며 INSPECT/VERIFY/IMPLEMENT/TEST를 aimux 워커에 위임,
    aimux 세션이 없으면 매니저 단독으로 동일 단계·게이트 수행(흐름 계약은 두 모드 동일). 헬스·
    무결성은 매니저가 직접 재현(워커 자가보고를 곧이곧대로 받지 않음).
  - **안전 비협상**: 대상 `.env` 미수정·비밀 미출력, 악성 입력은 데이터로만 주입(미실행), heavy는
    상한 명시, 대상 폴더 트리·자체 git 미변경, probe 테스트는 격리 디렉토리·자동 커밋 금지.
  - **반영 위치**(`ideate`와 동일 구조): 스킬 본체 `.claude/skills/verify-project/`
    (SKILL·flow·gate + `surfaces/{web,api,cli,lib,tui}` + `checklists/adversarial-catalog`),
    흐름 계약 `claude/verify-project.md`, 보고서 양식 `templates/verify-project/`(00~40·FINAL·
    `_case_block`). 인덱스 등록: `CLAUDE.md §2` 표 1행 + `claude/README.md` 트리·설명.

- **v0.1.3** — 2026-06-12 — continue 시 워커 CLI 대화의 프로젝트 bleed 수정 (PATCH)
  - 실 프로젝트(`test/test_AGTplatform`에서 `continue`)에서 도출. `AIMemory/bin/aimux-up` 수정,
    스텁 테스트 5/5 통과(`test_opencode_resume_pin.sh`).
  - **증상**: test_AGTplatform에서 `aimux-up continue` 했는데 opencode 패널이 하위 프로젝트
    `paper`의 세션을 복원한 것처럼 보임.
  - **원인**: aimux run-state(큐·handoff·work.log)는 매니페스트 `project`로 정확히 복원되나, 워커
    CLI의 **대화 복원**은 CLI에 위임된다. opencode/gemini/codex는 세션을 **git-루트 worktree 단위**로
    버킷팅하는데, `paper`는 독립 git 저장소가 아니라 부모 `test_AGTplatform`의 git 루트를 공유한다.
    따라서 둘이 같은 세션 버킷에 들어가고, bare `opencode --continue`(=버킷 최근 세션)가 더 늦게 돈
    paper 대화를 복원 → run-state는 부모, opencode 패널만 paper인 split-brain. (claude/qwen은
    매니페스트 uuid로 정확 복원돼 안전.)
  - **수정**: opencode는 세션 JSON의 `directory`가 PROJECT_DIR과 정확히 일치(끝따옴표로 부모-자식
    접두 오매칭 차단)하는 최신 세션을 찾아 `--session <id>`로 고정(`opencode_session_for_dir`);
    없으면 `--continue` 폴백 + 경고. gemini(`--resume latest`)·codex(`resume --last`)는 정확-id
    복원 미지원이라 경고만. 추가로 continue 시 부모/자식에 다른 aimux 프로젝트가 있으면 **중첩 경고**.
    권고: 별도 aimux 프로젝트는 별도 git 루트에 둘 것.

- **v0.1.2** — 2026-06-11 — 매니저 프롬프트 라우팅 반전 수정 (PATCH)
  - 실 프로젝트(`test/test_AGTplatform` 최신버전) AIMemory 리뷰에서 도출. `AIMemory/bin/aimux` 수정,
    스텁 테스트 8/8 통과(`test_manager_prompt_routing.sh`) + 기존 25/25 무회귀.
  - **증상**: 워커가 작업 완료·idle이 되면 디스패처와 매니저가 통신을 못 하고 멈춤.
  - **원인(권한 반전)**: 워커 reply는 `response`라 **매니저 pane을 inflight 유닛으로 등록**한다.
    매니저는 계속 동작하며 자기 권한 프롬프트(git 승인·`STEP 2 진행?` plan-gate)에 자주 막히는데,
    LOW-RISK wait 경로가 notice 수신자를 `to=from`(=reply 보낸 **워커**)로 잡아 "워커가 매니저
    프롬프트를 대신 승인"하는 반전이 발생. 매니저로 간 response inflight는 자연 종료신호가 없어 매
    wait episode마다 워커에게 notice를 재발행하며 wait-timeout(241s)까지 핑퐁 → 멈춘 것처럼 보임.
    실측상 워커가 매니저의 git 승인·`STEP 2 진행` 권한까지 대리 승인(정합성 위험).
  - **수정**: `is_manager_pane()`(pane의 `@awm_pane_name == manager`)로 매니저를 식별해, 매니저가
    프롬프트에 막히면 HIGH-RISK와 동일하게 **사람에게만 surface**하고 워커 wait-notice는 발행하지 않음
    (매니저는 상위 대리인이 없음). 잔류 inflight는 매니저 idle 시 idle-stable, 미해소 시 wait-timeout으로
    해제되어 영구 lock 없음. 무인 실행 시 매니저 자체 도구 프롬프트로 멈추지 않게 하려면
    `AWM_AUTO_APPROVE=1`로 런치.

- **v0.1.1** — 2026-06-09 — aimux 디스패치 신뢰성 4건 (PATCH)
  - 실 프로젝트(`pdf_translate2` 구현 + 하위 `paper` 논문) AIMemory 리뷰에서 도출. 전부
    `AIMemory/bin/aimux`·`aimux-up` 수정, env 오버라이드 가능, 스텁 테스트 25/25 통과(기존 무회귀).
  - **중첩 프로젝트 work.log 오염 차단**: `AIMUX_STATE`(큐)는 런처가 패널에 세션 고정했지만
    `AIMUX_MEM_DIR`(→`AIMUX_WORKLOG`)은 호출된 aimux 바이너리 위치로 재계산돼, 하위 폴더 프로젝트에서
    워커 cwd가 부모로 드리프트하면 큐는 자기 세션·로그는 부모로 갈렸다(split-brain). 런처 PENV에
    `AIMUX_MEM_DIR='$PROJECT_DIR/AIMemory'` 추가로 고정.
  - **프롬프트-막힘 패널 짧은 타임아웃**: `AIMUX_WAIT_TIMEOUT`(240s) 신설 — 자가해소 불가한 프롬프트
    막힘을 900s 풀 타임아웃 대신 조기 해제(re-route notice 동반). (구현 세션에서 5건이 각 900s 낭비)
  - **STUCK 오탐 제거**: STUCK의 ~90%가 opencode 단일 패널 오탐(느린 제출 렌더)이었다.
    `enter_settle_for()` + `AIMUX_ENTER_SETTLE_OPENCODE`(0.9s) 도입, 최종-시도 로그 톤 하향.
  - **긴 단일 턴 거짓 해제 방지**: `AIMUX_INFLIGHT_TIMEOUT_MAX`(2700s) 신설 — 타임아웃 시점에 busy면
    해제 대신 천장까지 연장(28쪽 변환 902s 거짓 "무응답" 사례).
  - 미반영(후속 후보, 코드 아닌 프로토콜 영역): 워커 자기보고 허위(증거필수 회신+매니저 독립 재검증),
    섹션 병렬 작성의 용어/주장 드리프트(공유 글로서리·기여 계약 + 일관성 패스).

- **v0.1.0** — 2026-06-08 (커밋 4d53917)
  - T1~T37 누적분의 첫 SemVer 기준점(아래 T 시리즈 = 0.1.0 구성 내역).
  - 도입: 루트 `VERSION`, `bump-version.sh`, `make-dist.sh` 버전 연동(파일명 +
    `latest` 포인터 + `LATEST.txt`, 동일 버전 zip 1개만 유지).

---

생성일  : 2026-05-29
목표    : AIMemory에 tmux 전달/회수 메커니즘 복원 — 큐 + 단일 디스패처(모니터링 스크립트)로 초인종 겹침 차단
진행    : 5/5 완료

> 참조: `~/Work/test/awm-260528/AIMemory/tmux-handoff.md`(풀 버전).
> 개선점: 각 패널 직접 paste(겹침) → 큐 적재 + 디스패처가 idle 패널에만 순차 주입.

## 수행 단계 (현재 작업)

- [x] **T1. 헬퍼 스크립트 `AIMemory/bin/aimux` 작성**
  - 서브커맨드: `panes` / `name` / `enqueue` / `dispatch` / `status` / `send-test` / `cancel`.
  - 검증 기준
    - `bash -n`(문법) 통과.
    - 하드코딩 경로 없음 — 스크립트 위치·tmux·env에서 유도.
    - jq 등 외부 의존성 없음 (tmux + coreutils만).
  - 롤백: 파일 삭제.

- [x] **T2. 큐 기반 디스패처 로직**
  - 검증 기준
    - 단일 인스턴스 보장(flock).
    - 타깃 패널 idle + in-flight 잠금 없을 때만 paste → 겹침 차단.
    - 응답도 동일 큐로 요청자에게 idle 시점에 반환.
    - in-flight 해제: 응답 감지 / working→idle / 타임아웃.
  - 롤백: 파일 삭제.

- [x] **T3. 문서 `AIMemory/tmux-handoff.md` (간소화 + 큐 방식) 작성**
  - 검증 기준
    - 풀 버전의 핵심(불변식·패널 레지스트리·역할·자율성·스모크테스트) 유지, 분량 축소.
    - 직접 paste 대신 `aimux enqueue` 흐름 명시.
    - PROTOCOL.md(AICP)가 진실의 원천이라는 불변식 유지.
  - 롤백: 파일 삭제.

- [x] **T4. `AIMemory/PROTOCOL.md` · `INDEX`(없으면 생략)에 tmux 확장 포인터 한 줄 추가**
  - 검증 기준: PROTOCOL.md에서 tmux-handoff.md 존재를 알 수 있음.
  - 롤백: 라인 제거.

- [x] **T5. 검증 — 스모크 흐름 점검**
  - 검증 기준
    - `aimux status`가 tmux 밖에서도 깨지지 않고 동작.
    - `aimux panes` 정상 출력(tmux 안일 때).
    - 큐 적재→디스패처 1회전 dry-run 동작 확인(`dispatch --once`).
  - 롤백: N/A.

- [x] **T6. 프로젝트 전용 런처 `AIMemory/bin/aimux-up` 작성** (후속)
  - 결정: `~/bin/awm-setup`(전역)은 미수정, 프로젝트 전용 런처 신규.
  - 검증 기준
    - 상단 에이전트 패널 균등 + 하단 풀폭 디스패처 패널 레이아웃.
    - 디스패처 패널에서 `aimux dispatch` 상시 구동(dispatch.lock + 로그 확인).
    - 풀버전 agent-work-mem 설치 지시 안 함(기존 간소화 AIMemory 보존).
    - 패널마다 `@awm_pane_name` + `@awm_agent_kind` + 보더 고정.
    - 첫 에이전트 = 매니저(사람과 대화·위임), 나머지 = 워커 온보딩 메시지.
  - 검증 완료: 3-에이전트 더미 기동 → enqueue → 상시 디스패처가 idle worker에 자동 전달 → idle-after-work 해제까지 통합 확인.
  - 롤백: 파일 삭제.

- [x] **T7. 에이전트별 초기 파일 + 역할 온보딩** (후속)
  - 로스터 `name:command[:init-file]` — 3번째 필드로 초기 파일 명시 가능, 생략 시 CLI 종류로 유도(claude→CLAUDE.md, codex/opencode→AGENTS.md, gemini→GEMINI.md).
  - 패널에 `@awm_init_file` 기록(`aimux panes` 컬럼 추가).
  - 온보딩 메시지: 매니저/워커 역할 명시 + "자기 초기 파일을 먼저 읽어라" + "역할·정체성은 이 메시지·붙여진 프롬프트에서 오며 공유 파일에서 추론하지 말 것" → 시작 시 역할 혼동 방지.
  - 검증 완료: 초기 파일 매핑(유도/명시 오버라이드), `@awm_init_file` 옵션, 매니저·워커 온보딩 텍스트 전달 모두 확인.
  - 롤백: 파일 삭제.

- [x] **T8. 실제 에이전트 검증 + 하드닝** (후속)
  - 실 claude(manager) + opencode(worker)로 핸드오프 왕복 성공 검증 (request: response-seen, response: idle-after-work).
  - 하드닝 적용:
    - 스크래치 경로 `/tmp` → `./AIMemory/tmp`: aimux는 `AIMUX_TMP` 사용, aimux-up은 `TMPDIR` export + 실행줄 프리픽스, 핸드오프 프롬프트·온보딩에 안내. (권한 프롬프트 회피)
    - gap1 권한: `AWM_AUTO_APPROVE=1` → claude에 `--dangerously-skip-permissions`, 로스터 명령에 플래그 허용(kind/init은 첫 토큰 기준).
    - gap2 orphan lock: lock에 PID 기록 + 보유 시 PID 안내 거부 + `dispatch --force`(폴링 탈취) + HUP 트랩(패널 사망 시 동반 종료).
  - 검증 완료: --force 탈취, HUP 해제, PID 표시, TMPDIR 프리픽스, 프롬프트 scratch 안내, 전달 회귀 모두 확인.
  - 롤백: 파일 삭제/되돌림.

- [x] **T9. qwen 워커 추가 + 분할 레이아웃** (후속)
  - 기본 로스터에 qwen(worker, 모델 gemma4:e4b, pane명 qwen) 추가.
  - 모델명에 콜론이 있어 콜론-안전 `name|command|init|split` 포맷 추가(기존 콜론 포맷도 유지).
  - per-agent `split`(h=우측 새 컬럼, v=이전 패널 아래 스택) 지원 → 레이아웃: manager(좌) | opencode(우상) / qwen(우하, 수평 분할), dispatcher(하단 풀폭).
  - kind_of/initfile_of에 qwen 추가(kind=qwen, init=AGENTS.md).
  - 검증 완료: 3-에이전트 더미 기동 → 레이아웃 좌표(manager 40x18 좌, opencode/qwen 우측 상/하 스택, dispatch 풀폭) 확인, qwen 실행줄 `qwen --model gemma4:e4b` 확인.
  - 가정(사용자 조정 가능): qwen 모델 플래그 `--model`, qwen init 파일 AGENTS.md.
  - 롤백: 파일 되돌림.

- [x] **T10. gemini 워커 추가 + 워커 초기 파일 + 매니저 책임 문서화** (후속)
  - 우측 컬럼 상단에 gemini 추가(위→아래: gemini/opencode/qwen).
  - 워커 초기 파일 신규: `AGENTS.md`(opencode)·`GEMINI.md`(gemini)·`QWEN.md`(qwen) — "전체 흐름 파악하되 워커로서 매니저 지시를 범위 그대로 충실 수행, 반환은 실제 실행". `initfile_of` qwen→QWEN.md.
  - `tmux-handoff.md` Roles에 매니저 책임(분해·워커 역량/응답시간 판단·효율 배분·완료까지 관리) 기록 + 매니저 온보딩 강화.

- [x] **T11. 세션 격리 (timestamp + 세션 범위 상호작용)** (후속)
  - 세션명 timestamp(`aimux-<names>-yymmdd-HHMMSS`), 세션별 상태 dir `AIMemory/.aimux/<session>`(자체 큐+lock), `AIMUX_SESSION`으로 pane 해석을 해당 세션으로 한정(`scope_list`).
  - 핵심 수정: 기존 tmux 서버가 떠 있으면 export가 패널에 전달 안 됨 → 실행줄에 `env TMPDIR/AIMUX_STATE/AIMUX_SESSION` 직접 프리픽스.
  - 검증: 기존 서버 + 동명 opencode pane을 가진 victim 세션 존재 시, 핸드오프가 자기 세션 pane에만 전달됨(교차 전달 없음).
  - 실측: 4-CLI(claude+gemini+opencode+qwen) 전달은 3 워커 모두 성공, opencode 완수 / gemini·qwen은 전달됐으나 결과파일 미생성(모델·CLI 한계).

- [x] **T12. 실전(scienceon Tetris) 로그에서 발견된 버그 3건 수정** (후속)
  - 버그1(최우선) — idle 오판 조기해제 → 반환 유실: `process_inflight`를 단일 idle 체크(`idle-no-change`) 대신 **연속 idle streak(`AIMUX_RELEASE_IDLE_CYCLES`=3) 후에만 해제**로 교체(busy면 리셋). + 매니저 온보딩·문서에 "전달≠수신, 매 턴 work.log 재스캔" 명시.
  - 버그2 — `--type response` 오용: enqueue에서 action role(IMPLEMENT/FIX/...) 동반 시 **request로 강제**(경고). 잘못된 "judge this" 프롬프트/roles 누락 방지.
  - 버그3 — work.log 타임스탬프 추정: PROTOCOL.md에 "`date '+%Y-%m-%d %H:%M'` 실제 시각 사용, 추정 금지" 명시.
  - 검증: 버그2 강제 확인; 버그1 streak 해제 타이밍·2번째 요청 보류·busy 리셋 확인.
  - 미적용: scienceon은 라이브 테스트라 미수정(다음 재기동 시 `AIMemory/bin/aimux` 복사 권장).

- [x] **T13. 디스패처 패널 실시간 가시화** (후속)
  - 요청: 워커 완료 후 디스패처가 제대로 안 알려줌 → 큐 적재/팝/완료를 패널에 보이게.
  - 구현: `aimux`에 stdout 라이브 피드 — `＋ QUEUE`(적재) → `▶ DELIVER`(팝, 패널 전달) → `✔ DONE`(완료/반환) + 카운트 변동 시 `┄ p=N i=M d=K ┄` 보드. 짧은 id(HHMMSS-rand), 컴팩트 1줄. `AIMUX_VLOG=0`로 끔.
  - 검증: 더미 세션에서 req·resp 왕복이 QUEUE→DELIVER→DONE+보드로 표시됨(60cols 적합).
  - scienceon(라이브): 새 `aimux` 복사 + idle 시점에 dispatch 패널(%27) `--force` 재기동으로 피드 활성화(에이전트 무영향, 버그1·2도 함께 적용).

- [x] **T14. 워커 무응답 idle 시 매니저 자동 통지** (후속)
  - 문제(tetris-service 실측): gemini가 핸드오프 받고 응답 없이 idle → 디스패처가 `idle-stable`로 락만 풀고 done 카운트만 올림. 매니저는 "idle"만 보고 추측·재배분. 디스패처가 상황을 매니저로 전달 못 함.
  - 보완: `release_inflight`에서 **request가 `response-seen` 아닌 사유(idle-stable/timeout/pane-gone)로 해제되면** 원 source(매니저)에 **`notice` 자동 enqueue**(우선순위 010). `build_notice_prompt`: "워커 X가 응답 없이 freed — 실제 산출물 확인 후 accept/재배분, idle≠완료". 통상 전달 경로·라이브 피드로 매니저에 도달.
  - 검증: 더미에서 워커 무응답 idle → `note`가 매니저 패널에 실제 전달됨 확인.
  - 라이브 적용: tetris-service에 aimux 복사 + dispatch 패널(%4) `--force` 재기동(큐 idle, 무영향).

- [x] **T15. 위임 범위 확대 + 에이전트 노하우/상태기반 운영** (후속)
  - ① test/verify도 위임: 매니저 온보딩·tmux-handoff Roles에 "통합·테스트·검증도 TEST/VERIFY 역할로 위임, 매니저는 분해·통합·판정만" 명시.
  - ② 거부 원인 분석 + 노하우 축적: `AIMemory/agents.md`(역량·실패모드·Learnings 원장) 신설·시드. gemini "튕김" 주원인 = 편집승인 모드(Shift+Tab 미적용 시 plan만, 파일 0) + tool-call 취약 → 진단·완화법 기록. 실패 시 진단→적응→1회 재시도→재배분, 결과를 agents.md에 append. 워커 초기파일에 "막히면 BLOCKER로 에러 보고, 편집 실제 적용" 추가.
  - ③ 상태기반 운영: `aimux agents`(NAME·KIND·idle/busy·HANDLING) 신규 명령 + tmux-handoff "Orchestration strategy(state-based)" 섹션. idle·역량 기반 배정, 결과 부실 시 다른 idle 가용 에이전트로 재위임.
  - 검증: `aimux agents` 보드 출력(busy/idle/handling) 확인, `bash -n` 통과.

- [x] **T16. `aimux down` 종료 명령 + 검증 위임 정책 명확화** (후속)
  - `aimux down [--yes] [--purge]`: 현재 세션(AIMUX_SESSION)만 finalize+종료(디스패처 정지→세션 kill), 다른 세션/서버 무영향. 프리뷰/확인 가드. (검증: A만 종료·B 생존.)
  - 정책 검토(supermario): 완성본 통합 검증을 매니저가 직접 수행(워커 전원 idle). 원인=역할 모호성("test/verify 위임" vs "synthesis/judgment는 매니저"). 수정: 온보딩·tmux-handoff·agents.md에 "**검증은 위임 작업, judgment=워커 증거 검토**; 완성본 검증도 VERIFY 단위로 위임(write AND RUN test/harness→evidence); 분해 시 통합/verify 단위 명시; 워커 idle인데 소스 읽어 직접 테스트 금지" 명확화.

- [x] **T17. 전달된 응답 미수신(매니저) 안전망 — 무활동 재촉** (후속)
  - 문제(supermario): opencode가 jump fix 후 응답까지 정상 enqueue·전달됐으나, 매니저가 idle 유지(멀티라인 paste가 입력창에 미제출) → idle_streak 0→3 → 조용히 `idle-stable` 해제. 매니저가 인지 못함. 워커 무응답엔 통지 있지만 매니저 미수신엔 안전망 없었음.
  - 보완: `process_inflight`에 **engagement 체크** — 전달 후 work.log에 에이전트 이벤트(aimux 제외) 증가가 없으면 = 미처리로 보고, **단일줄 nudge 1회 재전달**(`build_nudge`, 개행 없어 Enter로 제출됨 → 입력창에 남은 원본+nudge 함께 제출). 그래도 무활동이면 `unacked` 해제(요청은 기존 통지, 응답은 display-message). 활동 감지 시 정상 `idle-stable`(재촉 안 함).
  - `agentlog_count` 헬퍼(aimux NOTE 제외), 전달 시 `logn` 베이스라인 기록.
  - 검증: 무활동→NUDGE→unacked, 활동기록→idle-stable·재촉0 확인.

- [x] **T18. qwen 라우팅 정책 — 약한 로컬 모델 + 민감도 기반** (후속)
  - qwen(gemma4:e4b)은 약한 **완전 로컬** 모델 → (a) 비민감 작업은 자료조사·simple shell script·소규모 기계적 작업으로 **제한**, (b) 로컬이라 **개인/민감/기밀 데이터는 qwen 전담**(클라우드 에이전트 claude/opencode/gemini엔 절대 전달 금지), (c) 주요·복잡 작업은 opencode/gemini.
  - 반영: `AIMemory/agents.md`(운영규칙 #5 데이터 민감도 라우팅 + qwen 섹션), 매니저 온보딩(`aimux-up`), `tmux-handoff.md` 전략 배정 단계.

- [x] **T19. 발산→수렴 초기 계획 수립 절차(Phase 0)** (후속)
  - 절차: (0a) 구현계획 전 사용자 요구사항 확인 → (0b) 요구사항을 파일로, **매니저와 각 워커가 각자 독립 계획안 병렬 작성**(워커=`PROPOSE`, 구현 금지) → (0c) 모든 안의 아이디어 장단점 분석해 좋은 부분 결합한 **최선의 최종안** → 이후 분해·구현. (앵커링 방지: 초안 추인이 아닌 독립 발산 후 수렴.)
  - 반영: 역할 시스템 `PROPOSE` 추가(`role_instruction`), 매니저 온보딩(`aimux-up`), `tmux-handoff.md`(Phase 0 + 역할목록), `agents.md`(운영규칙 #0), 워커 초기파일(PROPOSE=자기안 작성·편집권한 없음), `DESIGN.md` 정책 섹션.

- [x] **T20. 논문화 지원 — 런 계측(run-summary) + paper 프로파일/LaTeX 스캐폴딩** (후속)
  - 하네스 계측(가벼움): `aimux report [--json] [--write]` — `.aimux/done`·`failed`의 기계 생성 `*.req`에서 인용 가능한 run-summary 산출(스키마 `aimux-run-summary/1`: totals·release_reasons·durations·per_agent(req/완료/실패)·redispatches·notices·handoffs[]). `down --yes`가 종료 전 `AIMemory/run-summary.json` 자동 저장.
  - 별도 프로젝트용: `claude/profiles/paper.md`(완료 AIMemory/를 입력으로 새 세션에서 논문화하는 절차/스킬) + `templates/paper/`(LaTeX: main/sections/refs/Makefile/README). 정량=run-summary.json, 서사=work.log, 주장↔아티팩트 1:1 추적 규칙.
  - 통합/문서: PROJECT.md·claude/README.md 프로파일 목록에 paper 추가, DESIGN.md §11(계측+논문화·스키마), README(명령·구조·핵심설계).
  - 검증: `aimux report` 합성 done셋으로 수치 정확(재배정·per-agent·duration), JSON 저장 확인.

- [x] **T21. 매니저 신호 체크포인트 + run-summary 버전 관리** (후속)
  - 매니저 신호: `aimux checkpoint [--label <m>]` — 대규모 요구 해결/마일스톤에서 호출. 디스패처 구동 중이면 **신호만**(`checkpoint.signal`) 남기고 디스패처가 루프에서 받아 자동 스냅샷(협업), 디스패처 없으면 즉시 작성(fallback). 종료 아니어도 단서 저장.
  - 버전 관리: 스냅샷을 `AIMemory/run-summary/vNNN-<ts>[-label].json`으로 시점별 보존, `run-summary.json`=최신 미러(기본 읽기). `report --write`·`checkpoint`·`down`(final) 모두 버전 증분. 시점 간 비교 분석 가능.
  - 논문: 별도 언급 없으면 **최신 버전** 사용(=run-summary.json), 요청 시 특정 vNNN/버전 비교(paper 프로파일에 명시).
  - 버그수정: `report --write`가 `--json` 없이도 기록하도록 조기 return 조건 수정.
  - 검증: report --write→v001, checkpoint→v002(+label) 증분·latest 미러, 디스패처 구동 시 신호→`■ SNAPSHOT` 자동작성·신호클리어 확인. JSON 유효.

- [x] **T22. 논문 워크플로우 보강 — 논문 버전관리 + 시각자료 + Word 산출** (후속)
  - 실증(plantest_paper) 검증 방식을 하네스 템플릿으로 일반화 이식:
    - **논문 버전관리**: `snapshot.sh`/`versions/vNNN-<date>[-label]/` + Makefile `snapshot`. 프로파일 규칙: 피드백 반영 전 스냅샷 → **증분 수정(통째 재생성 금지)**. (초기 "결과 통째 변경" 문제 해결.)
    - **시각자료**: 실험 전체 구조도(`figures/experiment-structure.svg`, 논문 실험 자체) + 수치비교 표(booktabs)+차트(`figures/results-bar.fig.tex`, pgfplots). 확장자 없는 `\includegraphics{figures/<name>}`로 PDF·Word 양쪽 임베드.
    - **Word 산출**: `build_docx.py`(pandoc; main.bbl 인라인+`\cite`→[n]+그림 .png 재작성). `make all`=pdf+docx.
  - 빌드 도구: latexmk+xelatex, pandoc, rsvg-convert, gs.
  - 검증: 템플릿에서 `make all`→main.pdf(44KB)+main.docx(그림 2개 임베드), `make snapshot`→versions/v001 확인.

- [x] **T23. paper 프로파일 보완 — 관련연구·내부파일 비인용·비전문가 접근성·주제 집중** (후속, plantest_paper2 피드백)
  - ① 관련연구 필수: 선행연구 조사 + 본 연구와의 유사점·차이점 명시(기본 포함). `background.tex`→"Related Work" 스텁.
  - ② 내부 파일명 인용 금지: `run-summary.json`·`per_agent`·`compare_*.md`·`work.log`·`handoff_*`·"aimux" 등은 인용대상 아님 → 본문/캡션/참고문헌에 등장 금지, 데이터는 "측정 결과"로 제시. (results 캡션·references.bib 자기인용 stub·main.tex 안내 수정.)
  - ③ 비전문가 접근성: 문제·예제 특성·용어 정의를 서론/배경에서 짚기. `introduction.tex` 스텁.
  - ④ 주제 집중: 주제 무관 시행착오는 제외 가능.
  - 반영: `claude/profiles/paper.md`(요약/범위/입력주의/절차/규칙), `templates/paper/`(sections·references.bib·main.tex·README). 빌드 회귀 확인(pdf+docx).

- [x] **T24. 사용자 입력 대기 idle vs 완료 후 idle 구별** (후속)
  - 문제: 워커가 사용자 판단(권한/선택 프롬프트)을 기다릴 때 디스패처가 idle로 오판 → 매니저에 통지·건너뛰기.
  - 해결: `pane_waiting`(tail에서 `AIMUX_WAIT_PATTERN` 매칭)으로 "사용자 입력 대기" 감지 → ① 전달 게이트에서 대기 패널 제외, ② `process_inflight`에서 대기 시 **보류**(해제·통지·재촉 안 함, idle_streak 리셋, "awaiting user input" 1회 표시+work.log NOTE "do not reassign"), 프롬프트 해소 시 정상 재개. 하드 타임아웃은 백스톱 유지.
  - 패턴 env 튜닝(`AIMUX_WAIT_PATTERN`), 기본값에 Do you want to/(y/n)/Esc to cancel/allow all edits 등.
  - 검증: 프롬프트 표시 중 3사이클 held(통지·재촉 0, WAIT 1회), 해소 후 release. 문서(DESIGN §4·§7, tmux-handoff 해제사유, agents.md #2) 갱신.

- [x] **T25. 대기 idle 위험도 라우팅 — 저위험은 매니저가 사람 역할 수행** (후속)
  - 문제: 워커가 사용자 판단을 기다리는 대기 상태일 때 매번 사람을 거치면 사소한 확인(예: "계속할까요?")에도 워커가 멈춤. 위험도가 낮으면 매니저가 직접 사람 역할을 수행해 진행시키는 게 효율적.
  - 해결: `AIMUX_WAIT_RISK_PATTERN`(파괴적/비가역/외부노출/자격증명/권한확대 ERE)으로 대기 프롬프트를 한 번 더 분류. ① **저위험** → `_emit_wait_notice`로 매니저에 고우선(005) notice 발행(워커 pane id + base64 프롬프트 발췌) → 매니저가 `tmux send-keys`로 직접 응답(핸드오프 아닌 허용된 직접 paste). ② **고위험** → 응답 안 함, 실제 사람에게만 표면화(work.log NOTE "escalated to the human"). 에피소드당 1회(`waiting` 플래그 게이트), 워커는 계속 held(재배분 안 함). 매니저가 저위험 notice를 위험하다고 판단하면 답 대신 에스컬레이션.
  - 신규: `wait_is_risky`/`wait_excerpt` 헬퍼, `build_notice_prompt` awaiting-user 분기, `_emit_wait_notice`.
  - 검증: 더미 패널 2개로 저위험("proceed? y/n")→notice 발행+매니저 패널에 pane id·발췌·send-keys 지시 전달 확인, 고위험("DELETE all files")→notice 0·human-only NOTE 확인, 멱등(재실행 시 재발행 0), 프롬프트 해소 후 플래그 클리어+정상 release 확인. 문서(DESIGN §4·§7, tmux-handoff 대기 라우팅, agents.md #2, aimux-up 매니저 온보딩) 갱신.

- [x] **T26. 최초 실행 시 워커 개수 선택 + 워커 우선순위 재정렬** (후속)
  - 문제: 런처가 항상 고정 워커 3개(gemini·opencode·qwen)를 기동 → 가벼운 작업에도 전체 패널이 떠 자원·화면 낭비. 워커 순서도 opencode 우선이 아님.
  - 해결: `aimux-up`에서 매니저(claude) 고정 + `WORKER_POOL`을 우선순위(opencode→gemini→qwen)로 정의. 최초 실행 시 풀 상위에서 N개(1..3)만 기동. 개수 출처: `AWM_WORKERS`(지정 시) → 미지정+터미널이면 대화형 프롬프트 → 비대화형이면 전체. 첫 워커=split h(우측 컬럼 개시), 나머지=v. `AWM_CONFIG` 주면 전체 로스터 대체(선택 생략).
  - 신규: `choose_worker_count`(범위 클램프·비숫자 방어·tty 프롬프트), `MANAGER_ENTRY`/`WORKER_POOL`.
  - 검증: `bash -n` 통과. 로스터 빌드 1/2/3 → split(h,v,v) 정상, 개수 검증(5→3 클램프, 0→1, abc→기본3, 미지정 비대화형→3) 확인. 문서(DESIGN §6·§7, aimux-up 헤더·주석) 갱신.

- [x] **T27. ideation 사전 단계(/ideate) 하네스 반영** (후속)
  - 문제: `~/Work/ideation2Project`에서 개발한 "모호한 희망→발산→수렴→PROJECT.md" 사전 구체화 컴포넌트가 기본 하네스에 미반영. ideate 단계가 워크플로(CLAUDE.md)에 미연결.
  - 해결: `REFLECTION.md` 매니페스트대로 `claude/ideate.md`(흐름 계약), `templates/ideate/`(project-draft·valuation-rubric·gate-checklist) 복사. 스킬 본체는 **단일 소스**로 Claude Code 표준 위치 `.claude/skills/ideate/`(SKILL·flow·gate + methods 9)에 실제 파일로 배치 — 심볼릭 링크 없이 폴더를 통째로 복사해도(다른 계정·서버) `/ideate`가 그대로 동작하도록 자가완결. 워크플로 결합: CLAUDE.md §1에 **시작 시점 진입 분기**(모호한 희망→ideate / 구체적 스펙→intake, 사용자에게 물어봄) + §2 표 행 + §3 스켈레톤 분기, `intake.md` 상단 안내, `claude/README.md` 갱신(스킬 위치 명시).
  - 검증: 복사 파일 목록·내용 일치(`diff -r` 0건). 폴더 내 심볼릭 링크 0개·절대경로 참조 0개(이식성). 모든 `claude/skills/ideate` 경로 참조를 `.claude/skills/ideate`로 갱신(ideate.md·gate-checklist), 저장소 상대참조(templates/ideate/*, AIMemory/bin/aimux, AIMemory/agents.md) 존재 확인. ideation2Project는 직접 수정 0건.
  - 미반영(의도): ideation2Project의 작업 산출물(AIMemory/handoff_*·proposal_*, CHECKLIST-ideate.md, REFLECTION.md)은 그 repo 고유 아티팩트라 복사 제외.

- [x] **T28. 복사 시 안 맞는 하네스 문서 분리 — README·CHECKLIST 템플릿화** (후속)
  - 문제: 폴더를 복사해 새 프로젝트를 시작하면 루트 `README.md`(하네스 자기소개)·`CHECKLIST.md`(하네스 개발 이력 T1~T27)가 그 프로젝트와 맞지 않음. 단 `plan.md`는 이미 README/CHECKLIST를 *프로젝트* 문서로 취급 → 불일치.
  - 해결(README): `README.md`는 하네스 개요로 유지(캐노니컬 repo 첫 화면)하되 상단에 "복사 시 교체됨" 배너 추가. 프로젝트 README 템플릿 `templates/project/README.md`(`{{필드}}` placeholder) 신설. `intake.md §3.6`·`ideate.md S4`가 PROJECT.md 필드로 채워 루트 README.md를 덮어쓰도록 결합(하네스 자체 개발 시엔 건너뜀).
  - 해결(CHECKLIST): 하네스 개발 이력을 `git mv CHECKLIST.md HARNESS-CHANGELOG.md`로 분리(헤더에 용도 명시). `CHECKLIST.md`는 빈 프로젝트 체크리스트 템플릿으로 신규 작성(plan이 채움). 교차참조 갱신: DESIGN.md(개요·파일맵·이력 3곳), README.md(이력 줄·디렉터리 트리).
  - 검증: `git mv` 이력 보존. 잔존 "CHECKLIST.md=이력" 참조 0건. 템플릿 placeholder ↔ PROJECT.md 필드 1:1. intake/ideate 양쪽에 README 렌더 단계 명시.

- [x] **T29. 권한 대기 위험도 오판 + 대기상태 가시화 + 매니저 직접작업 게이트** (후속, svgstructure 피드백)
  - 문제 ①(위험 오판): `AIMUX_WAIT_RISK_PATTERN`에 `don.t ask again|always allow|allow all`이 포함 → "Yes, and don't ask again" 같은 UI 옵션은 거의 모든 권한 프롬프트에 떠서 단순 권한 요청까지 항상 고위험으로 분류 → 사람에게 불필요 에스컬레이션.
  - 문제 ②(실패 오인): 매니저가 읽는 상태판 `aimux agents`(`cmd_agents`)가 권한 대기 패널을 `idle`로 표기(화면 정지) → 디스패처(`process_inflight`)는 `pane_waiting`으로 대기를 인지하는데 매니저는 "무응답 완료=실패"로 오인.
  - 문제 ③(매니저 과도 직접작업): 매니저가 워커 포화 시 직접 작업하도록 허용 → 사용자는 "실질 작업은 모두 워커, 매니저는 2회+ 오류+사용자 승인 시에만 직접" 원함.
  - 해결 ①: 위험 패턴에서 UI 문구 3종(`don.t ask again|always allow|allow all`) 제거 — 위험도는 프롬프트 UI가 아니라 **배후 동작**(삭제/비가역/외부노출/자격증명)으로 판정. 파괴적 마커(delete/rm/overwrite/format/push/deploy/credential 등)는 유지. 주석에 판정 기준 명시.
  - 해결 ②: `cmd_agents`에 세 번째 상태 `waiting` 추가(`pane_waiting` 우선 검사 → `idle`/`busy`). 대기 패널은 더 이상 `idle`로 안 보임 → 매니저가 완료/실패로 오인 안 함. 헤더 주석·`agents` 사용법 갱신.
  - 해결 ③: 매니저 직접작업 게이트 문서화 — 구현/통합/테스트/검증 등 **실질 작업은 전부 위임**, 매니저는 분해·라우팅·증거기반 수락/재배분 판단만. 직접 수행은 **(a) 해당 유닛 위임이 2회+ 실패 AND (b) 사용자 명시 승인** 둘 다일 때만(저위험 프롬프트 대리 응답은 작업 아님=승인 불요). 반영: tmux-handoff.md Roles·loop#5, agents.md 규칙4·claude-code 노트.
  - 검증: `bash -n` 통과(source·copy). 위험 라인에서 UI 문구 3종 제거 확인, WAIT_PATTERN의 "don't ask again"은 대기 감지용으로 유지(의도). `state=waiting` 분기 확인. svgstructure 복사본에 3파일 동기화(agents.md의 프로젝트 고유 Learnings 1줄 보존).

- [x] **T30. 매니저·워커 객관식 선택 + 역할별 세션 브리프 생성** (후속, svgstructure 피드백)
  - 문제: 런처가 매니저=claude 고정, 시작 시 워커 *개수*만 선택 → 매니저를 다른 CLI(opencode/codex 등)로 바꾸거나 claude를 워커로 쓸 수 없었음. 또한 역할이 CLI 종류에 1:1 고정(claude→CLAUDE.md, opencode/codex→AGENTS.md=워커 브리프…) → 매니저를 opencode로 골라도 그 CLI가 자동으로 읽는 파일이 "너는 워커다"라고 말하는 충돌.
  - 해결(후보 풀): 편집 가능한 단일 출처 `AIMemory/agents.roster` 신설 — `[manager]`/`[worker]` 두 섹션, 각 줄 `label | command`(모델 태그 포함, 콜론 허용). `AWM_ROSTER`로 교체, 파일 없으면 내장 fallback 풀.
  - 해결(선택): `aimux-up`이 기동 시 ① `[manager]`에서 매니저 1명 객관식 → ② `[worker]`에서 워커 다중 선택(번호/이름, `all`). `AWM_MANAGER`(label/index)·`AWM_WORKERS`(label/index 목록 또는 `all`)로 프롬프트 생략(이전 숫자 "워커 개수" 의미를 대체). 매니저 pane은 어떤 CLI를 골라도 항상 `manager`로 명명(워커가 `--to manager` 반환 보장).
  - 해결(브리프): 커밋된 `CLAUDE.md`/`AGENTS.md`/`GEMINI.md`/`QWEN.md`는 **무수정**(사람용 하니스 진입점 보호). 대신 역할 템플릿 `AIMemory/briefs/{manager,worker}.md`를 신설하고, 선택된 역할에 맞춰 세션 state 디렉터리(`.aimux/<session>/briefs/`)로 렌더링(pane 역할·CLI 헤더 주입) → 각 pane의 `@awm_init_file`(INITS)을 생성 브리프로 지정 → 온보딩이 그걸 1차로 읽게 함. 생성 브리프 + 온보딩 메시지가 역할의 권위 → 어떤 CLI든 매니저/워커로 기동 가능.
  - 신규/변경: `agents.roster`, `briefs/manager.md`·`briefs/worker.md`(CLI-agnostic). `aimux-up`: `load_roster`/`choose_manager`/`choose_workers`/`gen_brief` 추가, `choose_worker_count`·`MANAGER_ENTRY`·`WORKER_POOL` 제거. 문서: DESIGN §6·§7·§9·§10, README(빠른시작·레이아웃·환경변수·파일맵), agents.md(규칙5·claude-code 노트=양역할).
  - 검증: `bash -n` 통과. 함수 단위 테스트 — 로스터 파싱(매니저3·워커5), `choose_manager`(label `codex`/index `2`/기본), `choose_workers`(`claude,gemini`/`1 4`/`all`/오입력→fallback all) 모두 정상. 커밋된 CLAUDE.md/AGENTS.md/GEMINI.md/QWEN.md 변경 0건 확인.

- [x] **T31. 독립 실행 ↔ 멀티 실행 양립 + codex 1급 지원** (후속, svgstructure 피드백)
  - 문제 ①(독립 실행 깨짐): 커밋된 자동로드 브리프 `AGENTS.md`/`GEMINI.md`/`QWEN.md`가 첫 줄부터 "You are running as a worker ... Wait for a handoff"로 워커 프레이밍 → 같은 폴더에서 CLI를 **단독**으로 띄우면 독립 작업이 아니라 워커로 멈춰 대기. (claude는 CLAUDE.md라 무관.)
  - 문제 ②(codex 설정 부재): codex가 로스터에 추가됐으나 동작에 필요한 설정(모델·승인·샌드박스·프로젝트 trust) 안내·통합 부재. codex는 `AGENTS.md`를 브리프로 읽고(opencode와 공유) 설정은 `~/.codex/config.toml`을 읽으며 복사된 프로젝트는 trust 프롬프트가 뜸.
  - 해결 ①: 세 브리프를 **역할 중립**으로 재작성 — 기본=독립 에이전트(PROJECT.md/CLAUDE.md 따라 프로젝트 규칙 적용, 자율 수행), 상단에 **aimux override** 주석(aimux 세션이면 pane의 `ROLE:` 메시지 + 세션 브리프가 이 파일을 덮어씀). 멀티 모드는 온보딩 메시지가 권위라 안 깨짐. CLAUDE.md는 사용자 지시대로 무수정.
  - 해결 ②: `templates/codex/config.toml` 신설(모델·approval_policy·sandbox_mode·project_doc_max_bytes·`[projects."<경로>"].trust_level` 권장값 + 적용법 주석, 시크릿 없음/경로 placeholder). `aimux-up`의 `AWM_AUTO_APPROVE`를 case 분기로 확장 — codex에 `--dangerously-bypass-approvals-and-sandbox` 부착(claude는 기존 `--dangerously-skip-permissions`). 글로벌 `~/.codex`(auth.json 등)는 **무수정**. 로스터에 codex 셋업 주석 추가.
  - 검증: `bash -n` 통과. 독립 모드 시뮬 — opencode/gemini/qwen 단독 기동 시 워커 프레이밍 0건(중립 확인), aimux override 주석 존재 확인. `AWM_AUTO_APPROVE=1`로 codex 커맨드에 bypass 플래그 부착, claude에 skip-permissions 부착, qwen/gemini/opencode 워커엔 미부착 확인. config.toml 시크릿·하드코딩 경로 0건.

- [x] **T32. 중복작업 차단(참여 신호 보강) + 대기 프롬프트 stale 답 차단** (후속, ITnewsSummary 테스트 피드백)
  - 문제 ①(중복작업): idle 해제 전 "참여(engagement)" 판정이 work.log 증가에만 의존 → work.log를 안 쓰는 CLI(gemini/qwen/opencode/codex 등)는 실제로 일을 끝냈어도 "미수신"으로 오판돼 재촉(nudge: "do the work") → **같은 핸드오프를 재수행**. 이어 unacked 해제 + freed-notice까지 겹쳐 매니저도 재검증/재배정 → 중복 증폭. 매니저 pane도 반환 판정 후 NOTE 미기록이면 "UNPROCESSED return" 재촉 → 재판정.
  - 문제 ②(대기 중 사용자 입력 → stale 주입): 워커가 사용자 프롬프트에 막히면 저위험 wait-notice가 **첫 감지 사이클에 즉시** 매니저로 발사. 실제 사용자가 직접 답해 프롬프트가 사라져도 notice는 취소되지 않고, 매니저가 뒤늦게 stale 발췌를 근거로 `send-keys` → 이미 진행 중인 pane에 낡은 답('y'/'1' 등)이 **새 입력으로 주입** → 엉뚱한 수행.
  - 해결 ①: CLI 비의존 참여 신호 `saw_busy` 추가 — 전달은 idle pane에만 하므로, 전달 후 한 번이라도 busy로 관찰되면 paste에 반응한 것. 해제 판정을 (work.log 증가 **OR** saw_busy)로 변경 → 참여했으면 `idle-stable`(+무응답이면 "검증하라" notice만), **재촉=재작업은 두 신호 모두 0일 때(진짜 미제출)만**.
  - 해결 ②(3중 차단): ⑴ `AIMUX_WAIT_NOTICE_CYCLES`(기본 2) 연속 대기 관찰 후에만 저위험 notice 발사(사용자 우선 유예; 고위험 표면화는 주입이 없으므로 즉시), ⑵ 프롬프트가 먼저 풀리면 큐에 남은 미전달 wait-notice **자동 취소**(`wait_notice_file` 추적, 에피소드 플래그 리셋), ⑶ notice 본문에 "답하기 전 `tmux capture-pane`으로 그 프롬프트가 **아직 떠 있는지** 재확인, 사라졌으면 아무 키도 보내지 말 것" 지시. 대기 중 `wait_streak`는 acted 전까지만 기록(파일 비대 방지).
  - 변경: `aimux`(process_inflight 참여판정·대기 에피소드·`_emit_wait_notice` 경로 반환·notice 프롬프트), 문서 DESIGN §3·§4·§7, tmux-handoff.md(Engagement check·Stale-answer protection·Tuning).
  - 검증: `bash -n` 통과. 함수 스텁 시나리오 테스트 21건 전부 PASS — A) busy 관찰+로그 0 워커 → idle-stable 해제·nudge 0회·verify notice 1건, B) 한 번도 busy 아님 → nudge 1회 후 unacked, C) 유예 내 사용자 응답 → notice 미생성·플래그 리셋, D) 유예 초과 → notice 1건(에피소드당 1회), 사용자 선응답 시 미전달 notice 큐에서 삭제, E) 고위험 → 즉시 표면화·매니저 notice 0건.

- [x] **T33. 전달 제출 검증 — paste 후 Enter 미등록 문제** (후속, ITnewsSummary 테스트 피드백)
  - 문제: `deliver()`가 `paste-buffer` 직후 같은 순간에 `send-keys Enter`를 보냄. TUI CLI(codex 등)는 멀티라인 bracketed paste를 비동기로 소화하므로 그 Enter가 paste에 삼켜지거나 무시됨 → 입력창에 "[Pasted Content 1512 chars]"만 남고 **제출이 안 됨**(종종 발생). 한참 뒤 re-nudge가 수습하지만 그만큼 지연 + nudge 의존.
  - 해결: deliver를 제출-검증 루프로 교체 — paste 후 `AIMUX_ENTER_SETTLE`(0.4s) 대기(TUI가 paste를 소화할 시간) → Enter → settle 대기 → **화면 tail 해시가 변했는지 확인**(입력창 비워짐/에이전트 동작 시작 = 제출됨). 변화 없으면 Enter 재시도, 최대 `AIMUX_ENTER_TRIES`(3)회. 끝까지 실패하면 `↵ STUCK?` 피드 + work.log NOTE 남기고 기존 engagement/re-nudge 백스톱에 위임. 라이브 피드에 `↵ RETRY` 표시.
  - 변경: `aimux`(deliver·설정 2종), 문서 DESIGN §4(제출 검증 bullet)·§7, tmux-handoff.md Tuning.
  - 검증: `bash -n` 통과, 기존 시나리오 테스트 21건 PASS 유지. 실제 tmux 세션 스모크 테스트 — bash 패널에 단일줄·멀티라인 deliver 모두 rc=0 + 명령 실행 흔적 4건 확인(첫 Enter에 제출, RETRY 미발생).

- [x] **T34. 매니저 대역외 종결 선언(`aimux resolve`) — 종결 후 재조사 중복 차단** (후속, ITnewsSummary 테스트 피드백)
  - 문제: 매니저가 idle 워커를 먼저 발견해 산출물을 직접 검증·수락(대역외 종결)해도 디스패처는 모름 → 이후 idle-stable 해제 시 freed-notice("무응답 — 검증하라")를 또 보내고, 워커의 늦은 response도 그대로 전달 → 매니저가 **이미 닫은 유닛을 재검증/재판정**(중복작업 재발).
  - 해결: `aimux resolve <req-id> [--note]` 신설 — 매니저가 수락 즉시 실행. 효과 3중: ① inflight면 `resolved` 사유로 즉시 해제 + freed-notice **미발행**(release_inflight·process_inflight 양쪽에 resolved 분기), ② 큐에 이미 앉은 그 요청의 notice(orig_id)·늦은 response(reply_to)를 `superseded`로 드롭, ③ 이후 enqueue되는 후속물도 전달 시점(`deliver_pending`)에 `resolved.ids` 대조로 드롭. **비정상(미완료)이면 resolve 안 함** = 기존 흐름(응답 대기→notice) 유지 — 사용자 요구 둘 다 충족.
  - 매니저 학습 경로: freed-notice 본문에 "이미 직접 검증·수락했다면 재검증 말고 `aimux resolve <id>`만 실행(다음부터는 수락 즉시 실행하면 notice 자체가 안 옴)" 추가, `briefs/manager.md` Idle≠done 섹션·tmux-handoff.md(해제 사유·Idle is not success·Monitor 루프)에 사용 규칙 명시.
  - 계측: `aimux report`에서 `resolved`=completed로 집계(response-seen과 동급), release_reasons에 `resolved`·`superseded` 표기(human+JSON).
  - 검증: `bash -n` 통과. 시나리오 테스트 36건 전부 PASS(기존 21 + 신규 15) — F) inflight resolve → `resolved` 해제·notice 0건·resolved.ids 기록, G) 큐의 notice+늦은 response 일괄 드롭(superseded 2건), H) resolve **이후** enqueue된 response도 전달 시점 드롭(paste 0회), I) resolve가 디스패처 사이클과 경합해도 다음 사이클에 `resolved`로 해제·notice 0건.

- [x] **T35. `aimux shell` — 멀티에이전트 시작·종료 단일 명령** (후속, 사용 편의 피드백)
  - 문제: 시작은 `aimux-up`, 종료는 `aimux down --yes` 두 명령을 따로 입력해야 했음.
  - 해결: `aimux shell [project-dir]` 신설 — `aimux-up`으로 기동(선택 UI 동일)+attach 후, detach(Ctrl-b d) 시 질문: **finalize&종료 [Y] / 그대로 두기 [n] / 재접속 [a]**(a는 다음 detach에 다시 질문). 세션 안에서 이미 `down --yes` 했으면 그냥 깨끗이 종료. 자기 세션 식별은 런처가 새로 기록하는 `.aimux/last-session`(timestamp 세션명이라 내용 변화=이번 기동) 또는 `AWM_SESSION`으로; 런처가 조기 실패하면 종료 제안 안 함(타 세션 오살 방지).
  - 안전장치: `AWM_SHELL_ON_DETACH=down|keep|ask`(기본 ask)로 비대화 제어, tty를 못 읽으면 **keep**(조용히 죽이지 않음). tmux 내부에서 실행하면 수명주기 감독이 불가(switch-client 즉시 반환)라 경고 후 aimux-up으로 위임.
  - 변경: `aimux`(cmd_shell·usage·main), `aimux-up`(last-session 기록 1줄), README 빠른시작·환경변수, DESIGN §6, tmux-handoff.md 런처 절.
  - 검증: `bash -n` 2종 통과, 기존 시나리오 36건 PASS 유지. 신규 shell 테스트 14건 전부 PASS — S1) 런처 조기실패 → 종료 제안 없음+exit code 전파, S2) 세션이 내부에서 이미 종료 → 깨끗한 exit, S3) `down` 모드 → 실제 tmux 세션 end-to-end 종료(final run-summary 스냅샷+work.log 기록 확인), S4) `keep` 모드 → 세션 유지+재접속/사후 종료 명령 안내 출력, S5) tty 없음+ask → keep(무단 종료 없음).

- [x] **T36. 대기 감지 스크롤백 오판 수정 + 디스패처 사망 포렌식·자동 재기동** (후속, tttt 테스트 피드백 "dispatcher가 죽는 현상")
  - 진단(work.log 증거 기반): 디스패처(PID 1346)는 자체적으로 죽지 않았음 — 11:35 "Dispatcher stopped"는 시그널 트랩 로그, 즉 그 시점까지 생존. 실제 사건: ① `pane_waiting()`이 `-S -40`으로 **스크롤백까지 캡처** → 워커 %1이 이미 답한 프롬프트("Esc to cancel")가 히스토리에 남아 **영구 waiting/HIGH-RISK로 오판** → wait-hold가 안 풀려 step-2 전달 정체. ② 매니저가 정체를 "디스패처 사망"으로 **오진**, `dispatch --force` 재시작 → --force가 살아있던 1346을 kill → `exec`로 떠 있던 dispatch 패널이 통째로 닫힘 = 사용자에게 "디스패처가 죽는 현상"으로 보임.
  - 수정 1(근본 원인): wait 감지 3종(`pane_waiting`/`wait_is_risky`/`wait_excerpt`)을 **가시 화면만** 캡처하는 `visible_screen()`으로 교체 — 지금 막힌 프롬프트는 정의상 화면에 보이므로 스크롤백을 봐선 안 됨. idle 안정성 해시(`tail_hash`)는 스크롤백 포함 유지(무해).
  - 수정 2(포렌식): cmd_dispatch에 EXIT 트랩 추가 — 시그널 정상 종료가 아닌 모든 종료를 "Dispatcher EXITED unexpectedly (rc=N)"로 work.log에 기록 → dispatch 패널이 사라져도 원인이 남음.
  - 수정 3(자가 회복): `aimux-up`의 dispatch 패널을 `exec` 대신 **재기동 래퍼**로 실행 — 비정상(rc≠0) 종료 시 2초 후 같은 패널에서 자동 재시작, 정상 종료(Ctrl-C/--force 인계/down)는 rc=0으로 루프 탈출(셸 복귀, 패널 유지).
  - 수정 4(오진 방지): `briefs/manager.md`·tmux-handoff.md에 정체 진단 절차 명시 — `aimux status`가 "running (lock held)"면 디스패처 생존(정체는 전달 게이트 문제, `aimux agents`의 waiting/busy 확인); "lock free"일 때만 재시작; dispatch 패널 kill·lock 보유 중 `--force` 금지.
  - 변경: `aimux`(visible_screen+wait 3종, EXIT 트랩), `aimux-up`(재기동 래퍼), briefs/manager.md, tmux-handoff.md, DESIGN §4.
  - 검증: `bash -n` 2종 통과, 기존 시나리오 36건 + shell 14건 PASS 유지. 신규 T36 스모크 13건 전부 PASS(실제 tmux) — ①프롬프트를 스크롤백으로 밀어낸 패널: `-S -40` 캡처엔 프롬프트 잔존 확인 후 `pane_waiting`=아니오(버그 재현 차단), 가시 화면의 진짜 프롬프트는 waiting 검출+발췌 정상. ②dispatch_once가 rc=3으로 죽으면 "EXITED unexpectedly (rc=3)" 기록, TERM 정상 종료는 "stopped"만 기록. ③래퍼 패널에서 kill -9 → 2초 후 새 PID로 자동 재기동+화면에 "exited rc=137" 안내, TERM 정상 종료 → 루프 탈출·패널 생존.

- [x] **T37. 매니저 분해·배정 병렬화 정책 — 워커 idle 최소화** (후속, tttt 테스트 피드백 "단계적 묶음 배정 경향")
  - 문제: 매니저가 작업을 "step 1 → step 2 → step 3" 순차 묶음으로 한 워커에 차례로 배정 — 서술 순서를 의존성으로 착각해 실제로는 독립인 단위들까지 직렬화 → 나머지 워커들이 장시간 idle(tttt에서 관찰: build step을 하나씩 순차 발주).
  - 해결(행동 정책 4곳 명문화): ① **의존성 기준 분해** — 다른 단위의 산출물을 실제 소비하는 단위만 직렬화, 나머지는 전부 ready; ② **핸드오프 1건=1단위** — "A 하고 B 하고 C" 묶음 금지(병렬성 은닉 + 하위 실패가 묶음 전체 차단); ③ **ready 단위 일괄 살포** — 막히지 않은 단위는 한 번에 전부 idle 워커들로, 반환이 올 때마다 풀린 단위를 같은 턴에 즉시 후속 배정(ready-queue 유지); ④ **"ready 있는데 idle = 라우팅 실패"** — 전부 직렬로 보이면 더 쪼갬(구현 vs 테스트 하네스 vs 문서, 모듈별; 완료 단위 검증은 다른 워커의 다음 단위 빌드와 병행).
  - 변경: `briefs/manager.md`(신규 "Decompose for parallelism" 섹션), `aimux-up`(매니저 온보딩 메시지), tmux-handoff.md(루프 1·2단계), DESIGN §5.
  - 검증: `bash -n`(aimux-up) 통과, 시나리오 36건 + shell 14건 + T36 스모크 13건 PASS 유지(가이드 문서 변경이라 디스패처 로직 영향 없음). tttt 4종 동기화.

→ **[사용자 검토 지점]**

---

## (이전 완료 작업) 가이드 프로파일 재구성

생성일  : 2026-05-22
목표    : claude 가이드를 (A) 프로파일 시스템으로 재구성 + (B) 영어 본문 + 한국어 요약 형태로 전환
진행    : 7/7 완료

> 글로벌 위치 이전(원래 2단계)은 사용자 결정으로 제외. 폴더 복사 방식 유지.

---

## 수행 단계

### A. 구조 재구성 — 프로파일 시스템

- [x] **A1. `claude/core.md` + `claude/profiles/{dev,research,docs,data}.md` 신규 작성**
  - 검증 기준
    - `core.md`는 모든 프로젝트 공통 cross-cutting 규칙만 포함 (응답 형식·계획·검증 골격 링크).
    - 4개 프로파일 파일이 각 도메인(dev/research/docs/data)이 다루는 작업 흐름·산출물·도구 규칙을 분리해서 가진다.
    - 한 프로파일 파일 = 100~200줄 이내 (지나치게 크면 분해 신호).
  - 롤백 지점: 신규 파일 삭제로 원복.

- [x] **A2. 기존 도메인 편향 부분을 적절한 profile로 이전**
  - 대상
    - 현 `CLAUDE.md §5` (외부 산출물 — SQLite/Excel/Telegram/JSONL) → `profiles/data.md`로 흡수.
    - 현 `implement.md §5` (크롤링·스크래핑) → `profiles/data.md`로 흡수.
    - 다이어그램 규칙(현 `CLAUDE.md §5` 하단)은 cross-cutting이므로 `core.md`로 이전.
  - 검증 기준
    - `CLAUDE.md`·`implement.md` 본문에 데이터·스크래핑 편향 표현이 남아 있지 않음.
    - 이전된 내용이 해당 profile에서 검색 가능.
  - 롤백 지점: 이전 본문 백업 복원.

- [x] **A3. `PROJECT.md`에 `profile` 필드 추가 + `intake.md`에 자동 추천 절차 추가**
  - 검증 기준
    - `PROJECT.md`에 `profile: dev | research | docs | data` (또는 multi) 필드가 명시되어 있음.
    - `intake.md`에 "요청 메모 키워드로 profile 추천 → 사용자 확인" 단계가 추가됨.
  - 롤백 지점: 두 파일 이전 버전 복원.

- [x] **A4. `CLAUDE.md` 워크플로우 재정비**
  - 검증 기준
    - §1에 "PROJECT.md → profile 확인 → `core.md` + 해당 profile 로딩" 흐름 명시.
    - §2 표가 core·profile 구조에 맞게 갱신.
    - §3 워크플로우 골격이 새 구조 반영.
    - `CLAUDE.md` 자체 분량이 늘지 않음 (현재와 비슷하거나 줄어듦).
  - 롤백 지점: `CLAUDE.md` 이전 본문.

→ **[사용자 검토 지점]** A 단계 완료 후 구조 확인 받고 B 진행.

---

### B. 언어 분리 — 영어 본문 + 한국어 머리말 요약

- [x] **B1. `CLAUDE.md` + `claude/core.md` 변환**
  - 검증 기준
    - 각 파일 상단에 `## 요약 (사용자용)` 절 3~5줄 한국어.
    - 본문 영어.
    - 응답 언어 규칙("Korean for user-facing output, English for reasoning")이 영어 본문 안에 명시.
  - 롤백 지점: 한국어 버전 백업.

- [x] **B2. `claude/profiles/*.md` 전체 변환**
  - 검증 기준: 4개 프로파일 모두 동일 포맷 (한국어 머리말 + 영어 본문).
  - 롤백 지점: 백업 복원.

- [x] **B3. 나머지 cross-cutting 가이드 변환**
  - 대상: `claude/{intake,plan,implement,verify,token-efficiency,llm-performance,model-routing}.md`
  - 제외: `PROJECT.md`, `claude/README.md` (사용자 진입점 → 한국어 유지)
  - 검증 기준: 대상 7개 파일 모두 한국어 머리말 + 영어 본문.
  - 롤백 지점: 백업 복원.

→ **[사용자 최종 검토 지점]**

---

## 진행 이력

- 2026-05-22 — A1단계 완료: core.md + profiles/{dev,research,docs,data}.md 신규 작성
- 2026-05-22 — A2단계 완료: CLAUDE.md §4·§5 제거, implement.md §5 제거 및 번호 조정, 참조 파일 4개 갱신
- 2026-05-22 — A3단계 완료: PROJECT.md에 profile 필드 추가, intake.md §3.3 Profile 추천 절차 삽입
- 2026-05-22 — A4단계 완료: CLAUDE.md §1·§2·§3 재정비 (core·profile 로딩 흐름), claude/README.md 갱신
- 2026-05-22 — B1단계 완료: CLAUDE.md + core.md 영어 본문 + 한국어 요약 머리말로 변환
- 2026-05-22 — B2단계 완료: profiles/{dev,research,docs,data}.md 4개 영어화
- 2026-05-22 — B3단계 완료: intake·plan·implement·verify·token-efficiency·llm-performance·model-routing 7개 영어화
