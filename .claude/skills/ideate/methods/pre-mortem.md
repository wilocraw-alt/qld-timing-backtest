# pre-mortem.md — Pre-mortem (사전 실패 분석)

## 요약 (사용자용)

프로젝트 **시작 전에 "이미 실패했다"고 가정**하고 그 원인을 역추적하는 방법. 낙관적 편향을 깨고 잠재 위험을 조기에 발견. 아이디어가 어느 정도 구체화된 후(수렴 단계) 사용.

**When to use (이럴 때 적합)**: 아이디어가 확정 직전이고, 장밋빛 전망만 나오고 있을 때. S3 수렴 단계에서 선정 후보 1~2개에 대한 스트레스 테스트용. 모호도 Fuzzy~Clear.

**Answers (결박 미지수)**: 이 방법이 반드시 답해야 할 하나의 미지수 — **"이 프로젝트가 실패한다면 가장 유력한 원인 3가지는 무엇인가?"** 각 원인에 대해 발생 확률 + 예방 조치가 구체적이어야 함.

## How to run

1. **Set the scene**: "It is <6 months from now>. The project was launched but failed spectacularly. Write the obituary."
2. **Brainstorm failure causes**: list at least 5 reasons why the project failed. No filtering.
3. **Rank by probability**: top 3 most likely failure modes.
4. **For each**: design a prevention/mitigation strategy.
5. **Go/no-go recommendation**: given the failure modes and mitigations, does the project still make sense? Or does it need restructuring first?

## Worker prompt

```
아이디어: "<후보 아이디어 요약>"

Pre-mortem을 적용하세요:
1. "이 프로젝트가 6개월 후 실패했다"고 가정
2. 실패 원인 최소 5개 발산
3. 상위 3개 고확률 원인 선정
4. 각 원인별 예방/완화 전략
5. Go/No-Go 판단

산출: 실패 원인 목록 → 상위 3개 + 완화 전략 → 최종 권장.
```

## Output shape

```
Premise: <아이디어> — "Failed 6 months later."

Failure causes:
1. <원인1>
2. <원인2>
...

Top 3 most likely:
| Cause | Probability | Mitigation |
|-------|------------|------------|
| ... | High/Med/Low | ... |
| ... | ... | ... |

Recommendation: Go / No-Go / Restructure (<이유>)
```
