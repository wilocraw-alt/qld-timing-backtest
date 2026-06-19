# scamper.md — SCAMPER (아이디어 확장)

## 요약 (사용자용)

기존 아이디어/제품/프로세스에 **7가지 조작 연산(Substitute·Combine·Adapt·Modify·Put to other uses·Eliminate·Reverse)**을 적용해 다양한 변형을 창출. "이걸 어떻게 바꿀까?"가 핵심 질문. 구체적인 대상이 있고 그 변주를 보고 싶을 때 적합.

**When to use (이럴 때 적합)**: 이미 어느 정도 구체화된 대상(기능·제품·프로세스)이 있고, 그 **변형/개선/재활용** 아이디어를 원할 때. 모호도 Fuzzy~Clear.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"이 대상을 변형할 수 있는 가장 가치 있는 방향은 무엇인가?"** 최종 선택된 변형이 기존 대비 명확한 개선점을 가져야 함.

## How to run

1. Describe the target clearly (the current idea/product/process).
2. Apply each of the 7 SCAMPER operations:
   - **S**ubstitute: 무엇을 다른 것으로 바꿀 수 있나? (재료, 사람, 규칙, 장소)
   - **C**ombine: 무엇과 결합할 수 있나? (기능, 대상, 팀)
   - **A**dapt: 무엇을 빌려올 수 있나? (다른 도메인의 유사 사례)
   - **M**odify: 확대/축소/강화할 것은? (스케일, 빈도, 강도)
   - **P**ut to other uses: 다른 목적으로 사용할 수 있나? (기존과 다른 사용자/맥락)
   - **E**liminate: 무엇을 제거/단순화할 수 있나? (불필요한 기능, 단계)
   - **R**everse: 순서/역할/관점을 뒤집으면? (사용자↔제공자, 상향↔하향)
3. For each operation, generate at least 1 concrete idea.
4. Eliminate noise/duplicates and rank the top 3 most promising variants.

## Worker prompt

```
대상: "<희망/대상 요약>"

SCAMPER를 적용하세요 (각 연산당 최소 1개 아이디어):
- Substitute: 무엇을 대체?
- Combine: 무엇과 결합?
- Adapt: 무엇을 차용?
- Modify: 무엇을 확대/축소/강화?
- Put to other uses: 다른 용도?
- Eliminate: 무엇을 제거/단순화?
- Reverse: 어떻게 뒤집을까?

상위 3개 변형을 랭킹하고 이유를 붙이세요.
```

## Output shape

```
SCAMPER results:
| Operation | Idea | Brief |
|-----------|------|-------|
| Substitute | ... | ... |
| Combine | ... | ... |
...

Top 3:
1. <idea> — reason
2. <idea> — reason
3. <idea> — reason
```
