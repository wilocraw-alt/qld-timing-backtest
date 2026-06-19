# first-principles.md — First Principles (기초 분해)

## 요약 (사용자용)

기존 가정을 모두 벗어던지고 **가장 기본적인 진리(기초 원리)**까지 분해한 후, 거기서부터 새롭게 재조립. "원래 그래왔다"는 관성에서 벗어나 혁신적 아이디어가 필요할 때. 모호도가 높고 "틀을 깨야" 할 때 적합.

**When to use (이럴 때 적합)**: 희망이 너무 관습에 갇혀 있거나, "다들 이렇게 하니까"라는 전제가 느껴질 때. 모호도 Vague~Fuzzy. 기존 솔루션에 만족하지 못할 때.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"이 희망을 구성하는 분해 불가능한 기본 요소는 무엇인가?"** 재조립 결과가 기존 접근과 근본적으로 달라야 함.

## How to run

1. **Identify current assumptions**: list everything taken for granted about the wish. At least 5 assumptions.
2. **Break down to fundamentals**: for each assumption, ask "Is this really true? Can it be decomposed further?" until you hit a first-principle truth (physics, math, invariant human need).
3. **Rebuild from fundamentals**: combine the fundamental truths into a NEW approach that does not depend on the original assumptions.
4. **Compare**: new approach vs. the conventional approach on effort, risk, novelty.

## Worker prompt

```
희망사항: "<요약>"

First Principles를 적용하세요:
1. 현재 접근/가정 5개 이상 나열
2. 각 가정을 기초 진리까지 분해 ("정말인가? 더 쪼갤 수 있나?")
3. 기초 진리만으로 새 접근 재조립
4. 기존 접근과 비교 (노력·위험·참신성)

산출: 가정 목록 → 분해 결과 → 재조립안 → 비교표.
```

## Output shape

```
Current assumptions:
1. <가정1> → fundamental: <진리>
2. <가정2> → fundamental: <진리>
...

New approach (from fundamentals):
<구체적 서술>

Comparison:
| 항목 | 기존 접근 | 새 접근 |
|------|-----------|---------|
| 노력 | ... | ... |
| 위험 | ... | ... |
| 참신성 | ... | ... |
```
