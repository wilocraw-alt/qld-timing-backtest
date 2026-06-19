# surface: api — HTTP/gRPC API 드라이버

## Detect
- HTTP 서버지만 UI 없음(FastAPI/Flask/Express/gin 라우트, OpenAPI/swagger, `/api/...`).
- 또는 gRPC `.proto` + 서버 스텁.
- README가 엔드포인트/스키마를 안내, 브라우저 UI 언급 없음.

## Driver — 요청/응답 캡처
- 엔드포인트 목록을 라우트·OpenAPI에서 추출, 정상 케이스별 요청을 구성:
  ```bash
  curl -sS -X POST "http://localhost:PORT/api/<route>" \
    -H 'Content-Type: application/json' \
    -d '{"...": "..."}' -w '\n[http %{http_code} %{time_total}s]\n'
  ```
- 복잡하면 httpx 스크립트로 상태코드·헤더·본문·지연을 구조적으로 기록.
- gRPC면 `grpcurl`로 메서드 호출.

## 케이스별 캡처 규칙
- 케이스마다: 요청(메서드·경로·바디) / 기대(상태·스키마) / 실측(상태·본문 발췌·지연) / pass-fail.
- 증거 = 응답 코드블록(비밀·토큰 마스킹). 흐름 mermaid(클라 → 라우트 → 의존성 → 응답).
- 스키마 정합(응답이 문서/OpenAPI와 일치)도 케이스로.

## 흔한 함정
- 인증 필요한 엔드포인트는 토큰을 `.env`에서 읽되 **출력 금지**.
- 비결정 본문은 키 존재·타입으로 단언.
