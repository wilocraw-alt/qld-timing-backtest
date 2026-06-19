# surface: tui — 터미널 UI 드라이버

## Detect
- 풀스크린 터미널 앱(curses/blessed/textual/bubbletea), 키 입력 기반 화면 갱신.
- README가 "터미널에서 실행해 키로 조작"을 안내.

## Driver — pexpect / tmux 캡처
- pexpect로 키 입력 주입 + 화면 캡처:
  ```python
  import pexpect
  child = pexpect.spawn("<tui-app>", encoding="utf-8", dimensions=(40, 120))
  child.expect("<예상 프롬프트/화면 텍스트>")
  child.send("j")        # 키 조작
  # child.read_nonblocking 으로 화면 스냅샷
  ```
- 또는 tmux 세션에 띄우고 `tmux send-keys` + `tmux capture-pane -p`로 화면 텍스트 캡처(스크린샷 대용).

## 케이스별 캡처 규칙
- 케이스마다: 키 시퀀스 / 기대 화면 / 실측(capture-pane 텍스트 발췌) / pass-fail.
- 증거 = 캡처된 화면 텍스트 블록(또는 가능하면 터미널 스크린샷). mermaid(키 입력 → 상태전이 → 화면).

## 흔한 함정
- 화면 크기(행·열)에 따라 레이아웃이 달라짐 → dimensions 고정.
- pexpect/tmux 둘 다 어려우면 핵심 로직을 lib처럼 함수단위로 검증하고 그렇게 명시.
