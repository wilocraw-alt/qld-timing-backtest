# jobs-to-be-done.md — JTBD (고용할 과업)

## 요약 (사용자용)

사용자가 특정 제품/서비스를 **"고용(hire)"**하는 이유는 그 제품이 해결해주는 **과업(Job)** 때문이라는 전제. 기능이 아니라 **진행 상황(Progress)**과 **동기**에 초점. 사용자 관점에서 진짜 가치를 이해해야 할 때 적합.

**When to use (이럴 때 적합)**: 희망이 "사용자에게 가치를 주고 싶다"는 목적을 포함할 때. 모호도 Fuzzy~Clear. 사용자/수요자의 관점이 중요할 때.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"사용자가 이 희망을 통해 진정으로 해결하려는 과업(Job)은 무엇인가?"** 기능적 과업 + 감정적/사회적 과업을 모두 드러내야 함.

## How to run

1. **Identify the user/stakeholder** who would "hire" the outcome.
2. **Define the Job-to-be-Done**: what progress is the user trying to make? Format: "When <상황>, I want to <동기>, so I can <바라는 결과>."
3. Break into three job layers:
   - **Functional**: what practical task is accomplished?
   - **Emotional**: how does the user want to feel?
   - **Social**: how does the user want to be seen by others?
4. **Current solution**: what do they "hire" now? (even a workaround)
5. **Gap**: what's missing in the current hire that a new solution could address?
6. Derive 2–3 idea directions from the gap.

## Worker prompt

```
희망사항: "<요약>"
주요 사용자/이해관계자: <추정 또는 질문 필요>

JTBD를 적용하세요:
1. 대표 사용자 1명 특정
2. Job-to-be-Done 정의: "When __, I want to __, so I can __"
3. 과업 분해: 기능적 · 감정적 · 사회적
4. 현재 고용하고 있는 해결책
5. 갭(Gap): 무엇이 부족한가?
6. 갭에서 파생된 아이디어 방향 2~3개

산출: JTBD 정의 + 3개 층위 과업 + 갭 분석 + 아이디어 방향.
```

## Output shape

```
User/Stakeholder: <대상>
JTBD: "When <상황>, I want to <동기>, so I can <결과>"

Jobs:
- Functional: <기능적 과업>
- Emotional: <감정적 과업>
- Social: <사회적 과업>

Current hire: <현재 사용중인 해결책>
Gap: <부족한 점>

Idea directions:
1. <방향1>
2. <방향2>
```
