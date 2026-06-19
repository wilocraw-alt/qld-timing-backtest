# analogies.md — Analogies (유추·비유 전이)

## 요약 (사용자용)

**전혀 다른 도메인**의 성공 패턴·구조·원리를 현재 문제에 가져오는 방법. "이 문제를 해결한 다른 분야의 사례는?"이 핵심 질문. 틀에 박힌 접근을 깨고 전혀 다른 해결책을 얻고 싶을 때 적합.

**When to use (이럴 때 적합)**: 같은 도메인의 해결책만 반복해서 나올 때 (고착). 모호도 Vague~Fuzzy. 창의적 도약이 필요할 때. S2에서 SCAMPER·Crazy 8s 이후 심화 발산용.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"다른 분야에서 이 문제와 동형 구조를 가진 사례는 무엇이며, 그 해결책을 어떻게 전이할 수 있는가?"** 2개 이상의 이종 도메인에서 가져온 유추여야 함.

## How to run

1. **Abstract the problem**: strip domain specifics; express the core challenge as a general pattern/relationship (e.g., "많은 후보 중 가장 좋은 하나를 골라야 함").
2. **Identify distant domains**: pick 2–3 domains that are structurally similar but substantively different (e.g., biology, sports, military, games, cooking, market economics).
3. **For each domain**: find a case where the abstracted pattern was solved — describe the mechanism.
4. **Transfer**: map the domain-specific mechanism back to the original problem — what would it look like?
5. **Synthesize**: combine the best mechanisms from all domains into a hybrid approach.

## Worker prompt

```
원래 문제/희망: "<요약>"

Analogies를 적용하세요:
1. 문제를 일반 패턴으로 추상화
2. 이종 도메인 2~3개 선정 (생물학·스포츠·게임·시장경제 등)
3. 각 도메인에서 동형 문제의 해결 메커니즘
4. 원래 문제로의 전이 (각 메커니즘을 적용하면?)
5. 혼성 접근 제안

산출: 추상화 패턴 → 도메인별 사례 → 전이 결과 → 혼성안.
```

## Output shape

```
Abstracted pattern: <일반화된 문제 서술>

| Domain | Case | Mechanism | Transfer to our problem |
|--------|------|-----------|------------------------|
| <도메인1> | ... | ... | ... |
| <도메인2> | ... | ... | ... |
| <도메인3> | ... | ... | ... |

Hybrid approach: <혼성안>
```
