# surface: lib — 라이브러리/패키지 드라이버

## Detect
- 실행표면 없이 import해서 쓰는 패키지(`pyproject`/`setup.py`의 패키지, npm 라이브러리, public API 모듈).
- README가 "install 후 import/require해서 함수·클래스 사용"을 안내. 서버/CLI 엔트리포인트 없음.

## Driver — pytest 또는 import-and-call
- 기존 테스트가 있으면 먼저 실행:
  ```bash
  pytest -q            # 또는 npm test / go test ./...
  ```
- 정상 케이스 = **공개 API 호출**의 입출력 단언:
  ```python
  import target_pkg
  out = target_pkg.public_fn(valid_input)
  assert out == expected   # 또는 형태/타입/불변식 단언
  ```
- 공개 API를 README/`__all__`/export에서 식별, 대표 함수·클래스마다 happy-path 케이스.

## 케이스별 캡처 규칙
- 케이스마다: 호출(함수·인자) / 기대 / 실측(반환·예외) / pass-fail.
- 증거 = 테스트 출력 또는 REPL 트랜스크립트. mermaid(입력 → API → 반환/예외).
- 계약(타입힌트·docstring·스키마) 정합도 케이스로.

## 흔한 함정
- 실행표면이 없으므로 T3는 본질적으로 단위/통합 테스트 — 보고서에 "표면=lib, 함수단위 검증"임을 명시.
- 부작용(파일·네트워크) 있는 API는 격리/모킹.
