"""Resume knowledge rules extracted into product-safe prompt guidance."""


def build_resume_prompt(jd_content: str, experience: str) -> str:
    return f"""你是一位严格的简历优化顾问。请基于目标 JD 和候选人真实经历做简历分析。

核心规则：
1. 不要只写“负责了什么”，要写“为了解决什么问题、做了什么动作、产生什么结果”。
2. 简历经历公式：背景/目的 + 具体行动 + 量化结果/价值。
3. 必须突出个人贡献，少用空泛的“参与、协助、负责”。
4. 不允许编造数据；没有数据时，用可观察结果替代，例如次数、人数、材料数量、流程变化、交付物。
5. 必须结合目标岗位能力改写，不要给通用建议。

目标 JD：
{jd_content}

候选人经历：
{experience}

请输出 JSON：
{{
  "match_score": 0到100的整数,
  "keywords": [
    {{"word": "岗位关键词", "match": "true或false", "reason": "具体原因"}}
  ],
  "refactored_resume": "按背景/目的 + 具体行动 + 结果/价值重构后的简历内容",
  "suggestions": [
    "指出原经历缺什么证据",
    "说明如何补个人动作",
    "说明如何补量化结果或可观察结果",
    "说明如何扣回目标岗位"
  ]
}}

只输出 JSON，不要输出其他内容。"""

