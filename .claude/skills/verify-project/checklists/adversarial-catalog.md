# adversarial-catalog.md — 경계·악성·heavy 케이스 카탈로그 (T4)

T4에서 **대상·표면에 맞게 선별·구체화**하는 재사용 케이스 목록. 모든 케이스는 `SKILL.md`의
**안전 계약** 하에 실행한다: 악성 페이로드는 **데이터로만** 주입(호스트 미실행), heavy는 상한,
파괴적 부작용 금지, 사후 무결성 확인. 무음 상한 금지(자른 것은 보고).

분류 코드: `BD`(boundary) · `ML`(malicious) · `TY`(type/format) · `HV`(heavy).

---

## BD — 경계값
- BD-empty: 빈 입력 / 빈 바디 / 0건 컬렉션.
- BD-min-max: 최소·최대 길이, 수치 경계(0, -1, MAX_INT, 부동소수 극값).
- BD-boundary-off: off-by-one(상한+1, 하한-1), 페이지네이션 경계.
- BD-unicode: 멀티바이트·이모지·결합문자·RTL·제로폭, 매우 긴 단일 토큰.
- BD-path-range: 포트/인덱스/범위 인자의 경계(허용범위 밖) — 명시 검증 있는지.

## ML — 악성 (데이터로만, 절대 실행 금지)
- ML-cmd-injection: `; rm -rf /`, `$(...)`, 백틱 — 셸로 흘러드는지(미실행, 거부/이스케이프 확인).
- ML-sql-injection: `'; DROP TABLE x;--`, `' OR '1'='1` — 파라미터화 여부, 사후 DB 무결성.
- ML-path-traversal: `../../etc/passwd`, 절대경로, `%2e%2e` 인코딩 — 경로검증/차단(라이브 404 vs 함수단위 결함 **구분**).
- ML-xss: `<script>`, `onerror=`, `javascript:` — 출력 이스케이프(web).
- ML-ssrf/redirect: 내부주소·`file://`·메타데이터 IP를 URL 입력에.
- ML-deserialization: 조작된 pickle/yaml/json 구조(과대중첩 포함).
- ML-authz: 권한 밖 리소스 접근 시도(IDOR), 누락된 인증.
- ML-template/expr: SSTI(`{{7*7}}`), 표현식 주입.

## TY — 타입·포맷 오류
- TY-wrong-type: 문자열 자리에 객체/배열, 숫자 자리에 문자열.
- TY-malformed: 깨진 JSON/CSV/멀티파트, 잘못된 Content-Type, 인코딩 불일치.
- TY-missing-required: 필수 필드 누락 / 알 수 없는 추가 필드.
- TY-null-nan: null/None/NaN/Infinity, 빈 파일 업로드.
- 기대: 거부 시 명확한 4xx/검증오류(스택트레이스·500 노출 아님).

## HV — 부하·heavy (상한 명시)
- HV-concurrency: 동시 N 요청(예: 10·50) — 성공률·지연·자원경합·데드락.
- HV-volume: 대용량 페이로드/대량 행(상한 내) — 메모리·타임아웃·스트리밍.
- HV-rate: 짧은 시간 다수 요청 — rate-limit/백프레셔 동작.
- HV-soak(축약): 반복 호출 시 자원 누수(핸들·연결·임시파일 orphan) — 사후 확인.
- HV-resource-leak: 실패 경로에서 자원 해제(연결·포트·락) 되는지.

---

## 판정 축
- **안전 처리**: 거부(4xx/검증오류)·이스케이프·격리·상한 적용 + 사후 무결성 유지.
- **취약**: 실행됨·데이터 손상·정보노출(스택·비밀)·자원고갈·orphan 잔존.
- 라이브 차단(HTTP 라우팅단)과 **함수단위 결함**은 모두 기록하되 **구분**(STEP1 경로순회 사례: 라이브 404였으나 함수단위 결함은 유효).

## 사후 무결성 체크리스트
- 컴포넌트 헬스(전부 살아있는지), 로그 치명오류 없음.
- 데이터: 핵심 테이블 행수 불변(DROP/DELETE 피해 없음), 시드 무결.
- 자원: orphan 컨테이너/프로세스/임시파일/열린 포트 없음.
