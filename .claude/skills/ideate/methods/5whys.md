# 5whys.md — 5 Whys (근본 원인 추적)

## 요약 (사용자용)

희망이나 문제의 **겉모습**이 아니라 **진짜 근본 원인**을 파고드는 방법. "왜?"를 5번 반복해 표면 증상의 아래 숨은 층위를 드러냄. 문제가 명확한데 근본 원인이 불분명할 때 적합.

**When to use (이럴 때 적합)**: 희망이 "X가 안 돼서 고쳐야 함"처럼 **특정 문제/불만**에서 시작할 때. 모호도 Vague~Fuzzy. 원인을 모르는데 해결을 먼저 상상하고 있을 때.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"이 희망의 진짜 동기는 무엇인가?"** 각 답변(why)이 하나의 층위를 제거해 마지막 5번째 why가 근본 원인을 드러내야 함.

## How to run

1. State the initial wish/problem as a single sentence: "우리는 X를 원한다 / X가 문제다".
2. Ask **Why?** — answer concretely, not abstractly.
3. Take the answer and ask **Why?** again.
4. Repeat until the answer stops revealing new layers (usually 5 iterations; the real number is "until the root cause is exposed").
5. The final answer is the root cause. Restate the original wish in terms of this root cause.
6. Record the chain: each why→because pair.

## Worker prompt

```
희망사항: "<요약>"

위 희망의 근본 원인/동기를 찾기 위해 5 Whys를 적용하세요.
- 1 Why: "<희망>" → Because:
- 2 Why: 위 답변 → Because:
- (5회 반복, 더 이상 새로운 층위가 안 나오면 거기서 stop)
- 최종: 근본 원인은 무엇인가?
- 재진술: 근본 원인을 고려한 새로운 희망 서술

산출: Why 체인 + 최종 근본 원인 + 재진술문.
```

## Output shape

```
Root cause: <한 문장>
Why chain:
1. Why <initial> → Because <layer1>
2. Why <layer1> → Because <layer2>
...
Restated wish: <root cause 기반 재정의>
```
