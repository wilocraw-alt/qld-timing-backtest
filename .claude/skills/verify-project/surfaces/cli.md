# surface: cli — 명령행 도구 드라이버

## Detect
- `console_scripts`/`bin` 엔트리포인트, `argparse`/`click`/`typer`/`cobra`, `__main__.py`.
- README가 `tool <subcommand> --flags` 사용법을 안내.

## Driver — subprocess 호출·캡처
- 정상 케이스별로 인자/플래그/stdin → stdout·stderr·exit code 캡처:
  ```bash
  <tool> <subcmd> --flag value </dev/null; echo "[exit $?]"
  # 또는 stdin 주입
  printf '%s' "$INPUT" | <tool> <subcmd>; echo "[exit $?]"
  ```
- 부작용 있는 명령(파일생성·삭제)은 **임시 작업디렉토리**에서, 호스트 오염 금지.

## 케이스별 캡처 규칙
- 케이스마다: 명령행 / 기대(출력·exit) / 실측(stdout·stderr 발췌·exit) / pass-fail.
- 증거 = 출력 코드블록. mermaid(인자 파싱 → 실행 → 출력/종료코드).
- 종료코드 규약(0=성공, 비0=오류 유형)이 문서와 일치하는지도 케이스로.

## 흔한 함정
- 색상/TTY 의존 출력은 `--no-color`나 파이프로 안정화.
- 긴 실행은 타임아웃을 걸어 매달림 방지.
