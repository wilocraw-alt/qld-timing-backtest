# how-might-we.md — HMW (문제 재구성)

## 요약 (사용자용)

**문제를 기회로 재구성**하는 방법. "어떻게 하면 ~할 수 있을까?"라는 긍정적 질문으로 문제를 리프레이밍해 해결 방향을 넓힘. 문제는 명확하지만 해결 방향이 막막할 때 적합.

**When to use (이럴 때 적합)**: 문제가 명확히 정의됐는데 ("X가 안 됨"), 해결 방향이 하나도 안 떠오를 때. 모호도 Fuzzy. 문제 재정의 자체가 필요한 상황.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"이 문제를 가장 생산적인 질문 형태로 바꾸면 무엇인가?"** 각 HMW 질문이 서로 다른 해결 방향을 열어야 함.

## How to run

1. State the problem as a negative fact: "X가 안 된다 / X가 부족하다".
2. Reframe it as "How Might We <긍정적 목표>?"
   - "How" — 확정적 해결이 아닌 탐색임을 연다
   - "Might" — 실패 가능성을 허용한다
   - "We" — 혼자가 아닌 팀/공동의 과제임을 상기
3. Generate **at least 5 different HMW questions** from the same problem, each from a different angle:
   - 반전: "HMW X의 반대 상황을 만들까?"
   - 제거: "HMW X 없이 목표를 달성할까?"
   - 분할: "HMW X의 특정 부분만 해결할까?"
   - 확장: "HMW X를 10배 더 좋게 만들까?"
   - 사용자 전환: "HMW 다른 사용자가 이 문제를 해결할까?"
4. Each HMW question is a new idea direction; cluster related questions.

## Worker prompt

```
문제: "<희망/문제 요약>"

HMW를 적용하세요:
1. 문제를 한 문장으로 ("안 되는 것")
2. 5개 이상의 "How Might We <긍정 목표>?" 질문 생성 (다양한 각도에서)
3. 각 질문이 열어주는 해결 방향을 1문장씩 기록

산출: 문제문 → HMW 질문 목록(각각 해결 방향 포함).
```

## Output shape

```
Problem statement: <부정문>
HMW questions:
1. HMW <질문1>? → <해결 방향>
2. HMW <질문2>? → <해결 방향>
...
```
