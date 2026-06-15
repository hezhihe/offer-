# Interview Knowledge Base

## Product Principle

Mock interview feedback should help candidates improve, not judge them with abstract scores.

The interface should explain:

1. What the answer hit
2. What the answer missed
3. How to rewrite the answer
4. Why the rewrite is better

## Core Interview Logic

Interview performance is not just about saying the right words. The candidate needs to make the interviewer believe three things:

1. Value: this person can solve problems
2. Trust: this person is reliable and low-risk
3. Match: this person fits this role and this company

Use this working formula:

```text
Hiring probability = Value signal x Trust signal x Match signal
```

Do not show this as a mathematical score to users. Use it as internal reasoning.

## What Companies Actually Look For

Companies are not only checking grades, certificates, or whether the candidate sounds polished. They care about:

- Can this person solve real problems?
- Can this person execute and land work?
- Is this person low risk?
- Is this person stable and reliable?
- Can this person learn and improve?
- Can this person quickly become useful?

## Good Answer Structure

For self-introduction and motivation questions:

```text
Who I am
What I have done
What value I can bring
Why I fit this role
```

For experience questions:

```text
Scene / Task
Action
Result
Learning / Link to role
```

This is STAR plus a final role connection.

## Bad Answer Patterns

Flag these clearly:

- Only says attitude, not evidence
- Only says interest, not role understanding
- Lists duties without problems solved
- Uses “we” but hides personal contribution
- No concrete scene
- No action
- No result
- No metric or observable outcome
- No link to the target role

## Feedback Output Format

The model should return:

```json
{
  "hit_points": ["..."],
  "missed_points": ["..."],
  "rewrite_advice": ["..."],
  "sample_rewrite": "..."
}
```

Do not ask the model to return public-facing scores.

## Rewrite Standard

A useful rewrite should include:

1. Direct answer to the question
2. One concrete scene
3. Candidate's personal action
4. Result or value
5. Link back to company or role

## Example Feedback Rule

If a candidate says:

> 我对这个岗位很感兴趣，也愿意学习。

Do not say:

> 回答比较积极，但还可以更具体。

Say:

> 你表达了兴趣，但没有证明你理解岗位，也没有说明你能带来什么价值。下一版需要补充一个具体经历：你曾经解决过什么问题、做了什么动作、产生了什么结果，再说明这件事为什么能证明你适合这个岗位。

