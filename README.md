# qld-timing-backtest

규칙 기반 레버리지 ETF 적립 및 타이밍 투자 전략의 백테스트 검증과 라이브 데일리 어드바이저 시스템입니다.

---

## 핵심 결론

- **강세장(2011~2026)**: 타이밍 및 로테이션 전략이 단순 보유(Buy & Hold)에 패배하며, 시장 이탈 자체가 손해를 야기했습니다.
- **폭락장(2000 닷컴 시나리오)**: 무방비로 3배 레버리지를 보유할 경우 변동성 손실(Decay)로 인해 -97% 전멸 수준에 이르렀으나, 추세추종 타이밍 전략은 +147~339%로 역전 성과를 냈습니다.
- **최종 추천 전략**: 강세장의 수익을 누리면서도 최악의 시장 붕괴에서 생존할 수 있도록 설계된 **SOXL 60%(120일선 ±3% 완충 밴드) + QLD 40% 월 $300 소수점 적립·리밸런싱** 전략을 제시합니다.
- 상세한 분석 과정과 결론은 [RESEARCH.md](RESEARCH.md)에서 확인하실 수 있습니다.

---

## 데일리 어드바이저 & 웹사이트

- **데일리 어드바이저**: `backtest/live/daily_advisor.py` 스크립트를 통해 매일 전일 종가 기준으로 "오늘 미국장에 살 주식과 수량"을 자동 산출합니다.
- **웹사이트 및 PWA**: GitHub Actions를 통해 매일 자동으로 갱신되는 전용 웹페이지를 제공합니다. 휴대폰 브라우저에서 아래 URL에 접속한 뒤 '홈 화면에 추가'를 선택하면 standalone 앱(PWA)처럼 편리하게 오늘의 신호와 목표 비중을 조회할 수 있습니다.
- **배포 URL**: https://wilocraw-alt.github.io/qld-timing-backtest/ <!-- 배포 후 확정 -->

---

## 빠른 시작 / 재현

### 실행 환경
- Python 3.8
- 의존성 라이브러리: `pandas`, `numpy`, `yfinance`, `matplotlib`, `pyyaml`
  > [!IMPORTANT]
  > Python 3.8 환경에서 `yfinance` 임포트 오류를 방지하기 위해 `multitasking==0.0.11` 핀 고정을 강력히 권장합니다.

### 실행 명령어
```bash
# 의존성 라이브러리 설치
pip install -r backtest/requirements.txt

# 오늘 미국장 매매 신호 및 수량 미리보기 (상태 저장 안 함)
python backtest/live/daily_advisor.py --dry-run

# 정기납입 5개 전략 백테스트 실행
python backtest/contrib_run.py

# 다자산 14개 전략 및 OOS 기간 검증 실행
python backtest/portfolio_run.py

# 2000년 닷컴 위기 재현 시나리오 백테스트 실행
python backtest/dotcom_scenario.py

# 확률가중 기반 전략 기대값 분석 실행
python backtest/recommendation.py

# 120일선/200일선 및 휩쏘 완화 변형 전략 비교 실행
python backtest/ma_whipsaw.py

# 최종 결합전략(SOXL60/QLD40) 4개 시나리오 검증 실행
python backtest/final_strategy.py
```

### 매일 매매 신호 자동 실행 (cron 등록 예시)
매일 KST 15:00(미국장 개장 전)에 어드바이저를 실행하여 로그를 기록하도록 설정할 수 있습니다.
```text
0 15 * * * cd /path/to/repo && /usr/bin/python3 backtest/live/daily_advisor.py >> backtest/live/advisor.log 2>&1
```

---

## 문서 가이드

- [RESEARCH.md](RESEARCH.md): 아이디어 발굴부터 백테스트 결과, 최종 포트폴리오 도출까지의 전체 연구 과정 및 리포트 가이드.
- [backtest/output/report_final_strategy_ko.md](backtest/output/report_final_strategy_ko.md): 휩쏘 필터를 반영한 최종 추천 전략(안 1~4)의 상세 수치 및 성과 비교.
- [backtest/output/report_easy_ko.md](backtest/output/report_easy_ko.md): 레버리지 타이밍 전략의 핵심 개념을 직관적으로 설명한 대중용 가이드북.

---

## 면책 고지

본 저장소의 모든 분석 및 데이터는 과거 백테스트 결과를 기반으로 한 연구 자료이며, 어떠한 경우에도 **투자 조언이 아닙니다**. 레버리지 ETF는 강한 변동성 손실(Decay) 위험이 동반되므로 장기 횡보 또는 하락 시 원금의 큰 손실을 초래할 수 있습니다. 실제 투자에 따른 판단과 모든 책임은 전적으로 투자자 본인에게 있습니다.

---

이 저장소는 make_Harness 스캐폴드를 사용하여 생성되었습니다. 스캐폴드 및 멀티에이전트 오케스트레이션(aimux) 아키텍처에 대한 상세 설계는 [DESIGN.md](DESIGN.md)를 참조하십시오.
