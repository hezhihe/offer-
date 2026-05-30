# Resume Knowledge Base

## Product Principle

Resume feedback should not only say whether a resume is good or bad. It should transform weak descriptions into evidence-based descriptions.

## Core Resume Formula

Use this formula for experience bullets:

```text
Context / Purpose + Specific Action + Quantified Result / Value
```

The candidate should not only write what they did. They should write what problem they solved and what value they created.

## Weak Resume Patterns

Flag these patterns:

- Only lists responsibilities
- No scene or purpose
- No personal contribution
- No quantified result
- No business or user value
- No link to target role
- Uses broad words like “参与、负责、协助” without details

## Strong Resume Patterns

Encourage these elements:

- Clear purpose
- Specific personal action
- Quantified output
- Efficiency, growth, cost, quality, conversion, exposure, retention, accuracy, stability, or satisfaction metrics
- Role-matched keywords

## Role Matching Rules

For operations roles, look for:

- traffic
- conversion
- retention
- process
- data review
- user feedback
- activity execution

For administrative / coordination roles, look for:

- coordination
- process control
- zero error
- efficiency improvement
- documentation
- cross-team communication

For technical roles, look for:

- problem solving
- implementation
- debugging
- optimization
- deployment
- reliability

For product roles, look for:

- user problem
- requirement analysis
- MVP
- metric
- iteration
- validation

## Resume Feedback Output Format

The model should return:

```json
{
  "problem": "原句的问题",
  "missing_evidence": ["缺少的证据"],
  "rewrite_strategy": ["怎么补"],
  "rewritten_example": "改写示例",
  "role_match_reason": "为什么更匹配目标岗位"
}
```

## Rewrite Example

Weak:

> 负责公众号运营，撰写推文，做活动宣传。

Better:

> 为校园活动制定公众号宣传方案，独立完成活动预告、赛程和复盘推文，结合海报和短视频进行多渠道分发；通过优化选题和发布时间提升内容曝光，并用阅读量、报名人数和互动数据复盘宣传效果。

If actual metrics are available, replace generic value with numbers.

## Product Reminder

Do not invent fake metrics. If the user has no data, ask them to estimate from available evidence or use observable outputs such as number of posts, events, users served, materials delivered, or process improvements.

