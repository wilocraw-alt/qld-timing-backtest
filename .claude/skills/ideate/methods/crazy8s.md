# crazy8s.md — Crazy 8s (고속 발산)

## 요약 (사용자용)

**8분 동안 8개 아이디어를 강제로 쏟아내는** 시간 제한 발산법. 첫 아이디어에 갇히는 걸 방지하고, 양이 질을 압도하게 해 예상치 못한 방향을 터뜨림. 모호도가 높고 "백지 상태"에서 시작할 때 적합.

**When to use (이럴 때 적합)**: 아이디어가 하나도 없거나 하나만 떠오르는 "백지/고착" 상태. 모호도 Vague~Fuzzy. 빠른 발산이 필요할 때. S2 아이디어 발산의 첫 단계로 사용.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"이 희망에 대해 가능한 모든 방향을 8분 안에 훑으면 무엇이 나오는가?"** 최종 아이디어 중 최소 3개는 처음 생각과 다른 범주여야 함.

## How to run

1. State the challenge as a single question: "어떻게 ~할 수 있을까?"
2. Set an 8-minute timer (or equivalent timebox for the agent).
3. Generate exactly 8 distinct ideas — no judging, no filtering, no elaborating. One short sentence each.
4. If an idea doesn't come, force something: take the previous idea and invert/absurdify/split it.
5. After 8 minutes: review. Cluster, eliminate duplicates, flag the 3 most promising.

## Worker prompt

```
질문: "<희망을 질문 형태로>"

Crazy 8s를 적용하세요:
1. 정확히 8개의 아이디어를 생성 (각 1문장, 번호 1~8)
2. 판단/평가 금지 — 일단 전부 쏟아낼 것
3. 막히면 직전 아이디어를 반전/분할/확장

산출: 8개 아이디어 목록 + 상위 3개.
```

## Output shape

```
Challenge: <질문>
Ideas (Crazy 8s):
1. <idea1>
2. <idea2>
...
8. <idea8>

Top 3: <3, 7, 2> — <간단 이유>
```
