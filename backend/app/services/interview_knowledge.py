"""Interview feedback knowledge rules.

The user-facing report must not feel like a reusable scoring template.
Each section should respond to the current question type and the candidate's
actual answer.
"""

from typing import Dict, List


JOB_SCENARIOS = {
    "robot": "机器人调试、传感器标定、路径规划、现场故障排查或安全测试",
    "ai": "数据处理、模型评测、RAG/微调、上线部署、成本或效果优化",
    "lowAltitude": "低空物流、园区巡检、文旅航线、应急救援或飞行任务调度",
    "material": "实验设计、材料表征、性能验证、工艺优化或量产放大",
    "pm": "用户访谈、需求拆解、MVP 设计、指标验证或版本迭代",
}

JOB_ACTIONS = {
    "robot": "定位问题、调整参数或方案、验证稳定性和安全边界",
    "ai": "定义指标、处理数据、评测效果、控制成本并推动上线",
    "lowAltitude": "做合规检查、航线/资源调度、异常处理和任务记录",
    "material": "设计实验、控制变量、分析数据并验证材料性能",
    "pm": "发现用户问题、拆需求、定优先级、验证结果并迭代",
}

VALUE_MARKERS = ["解决", "提升", "降低", "优化", "完成", "上线", "转化", "增长", "成本", "效率", "稳定"]
TRUST_MARKERS = ["数据", "指标", "结果", "验证", "负责", "具体", "流程", "风险", "合规", "安全"]
MATCH_MARKERS = ["岗位", "公司", "业务", "用户", "场景", "需求", "适合", "价值", "运营", "产品"]

PM_SCENE_MARKERS = ["投递前", "面试前", "求职", "简历", "信息差", "焦虑"]
PM_METRIC_MARKERS = ["完成率", "留存", "转化", "反馈质量", "点击率", "使用时长", "满意度"]
PM_AI_BOUNDARY_MARKERS = ["模型", "波动", "兜底", "解释", "可编辑", "边界", "AI"]
ROBOT_DELIVERY_MARKERS = ["现场", "部署", "调试", "接管", "故障", "恢复", "标定", "传感器", "稳定"]
BUSINESS_CHAIN_MARKERS = ["流量", "产品", "交付"]


def build_interview_prompt(job_name: str, question: str, answer: str) -> str:
    return f"""你是一位严格但友好的真实面试教练，正在分析「{job_name}」岗位候选人的文字回答。

产品目标：用户求职时间很紧，前台只展示短反馈。你必须给出能立刻修改回答的反馈，不要写长篇报告。

内部判断框架：
0. 岗位相关性：是否围绕当前岗位和当前问题；明显跑题要直接指出。
1. 价值感：是否证明自己解决过具体问题、创造过结果。
2. 信任感：是否有真实场景、个人动作、数据、验证记录或异常处理。
3. 匹配度：是否把经历和「{job_name}」岗位要求连接起来。

面试问题：
{question}

候选人回答：
{answer}

请只输出 JSON：
{{
  "quick_judgement": "本题结论，最多25个中文字，直接说核心问题",
  "most_important_fix": "最该补的一点，最多35个中文字，必须具体",
  "rewrite_example": "下一版回答示例，80-140个中文字，不要编造虚假数字",
  "follow_up_question": "面试官可能追问的一句话，最多35个中文字",
  "hit_points": ["回答里具体做对了什么，没有就给空数组"],
  "missed_points": ["具体缺什么证据、细节或岗位连接"],
  "rewrite_advice": ["下一版具体怎么补，必须可执行"],
  "sample_rewrite": "可参考的更好回答，80-140个中文字",
  "summary": "一句话指出当前回答最大问题"
}}

硬性要求：
- 不要输出分数，不要输出等级。
- 不要说“逻辑清晰、表达不错、建议使用STAR”这种模板话。
- 每条反馈都必须基于候选人的原回答；原回答没有的信息不能假装存在。
- 如果候选人没有真实经历，允许给“模拟表达框架”，但不能编造公司名、项目名、数据。
- 如果答非所问：quick_judgement 写“答非所问，需要重答”，hit_points 为空，most_important_fix 指出要回到当前问题。
- 前四个字段是前台默认展示内容，必须短、狠、可执行。
- 只输出 JSON，不要输出其他内容。"""


def _has_any(text: str, words: List[str]) -> bool:
    return any(word in text for word in words)


def _present_terms(text: str, words: List[str], limit: int = 4) -> List[str]:
    return [word for word in words if word in text][:limit]


def _answer_specific_hits(question: str, answer: str, job_type: str) -> List[str]:
    hits: List[str] = []

    if job_type == "pm":
        scenes = _present_terms(answer, PM_SCENE_MARKERS)
        metrics = _present_terms(answer, PM_METRIC_MARKERS)
        ai_boundaries = _present_terms(answer, PM_AI_BOUNDARY_MARKERS)

        if scenes:
            hits.append(f"你把产品经理的判断落到了具体用户场景：{ '、'.join(scenes) }，这比只说“理解用户”更具体。")
        if metrics:
            hits.append(f"你没有停在功能描述，而是用 { '、'.join(metrics) } 这类指标说明怎么验证产品价值。")
        if ai_boundaries:
            hits.append(f"你提到了 { '、'.join(ai_boundaries) }，说明你知道 AI 产品不能把判断完全交给模型。")
        if all(word in answer for word in ["用户", "业务", "上线"]):
            hits.append("你把 PM 工作串成了用户问题、业务目标和上线结果，而不是只停留在画原型或写 PRD。")

    if job_type == "robot":
        delivery_terms = _present_terms(answer, ROBOT_DELIVERY_MARKERS)
        if delivery_terms:
            hits.append(f"你把机器人岗位落到了真实交付问题：{ '、'.join(delivery_terms) }，这比只讲算法模块更接近业务现场。")
        if all(word in answer for word in BUSINESS_CHAIN_MARKERS):
            hits.append("你明确拆了流量、产品、交付三层，能看出你在用业务链路理解机器人项目。")
        if _has_any(answer, ["任务成功率", "接管次数", "故障恢复", "单次任务耗时"]):
            hits.append("你给出了可验证指标，例如任务成功率、接管次数或故障恢复时间，反馈会更可信。")

    if not hits:
        if _has_any(answer, VALUE_MARKERS):
            hits.append("你有表达解决问题或带来结果的意识，但还需要把结果落到更具体的场景和指标上。")
        if _has_any(answer, TRUST_MARKERS):
            hits.append("你提到了流程、数据或验证方式，这些信息能增强可信度。")
        if _has_any(answer, MATCH_MARKERS):
            hits.append("你有尝试把回答扣回岗位或业务场景，但还需要进一步说明个人证据。")

    return hits


def _answer_specific_misses(question: str, answer: str, job_type: str) -> List[str]:
    misses: List[str] = []

    if job_type == "pm":
        if not any(word in answer for word in ["我做过", "我负责", "我参与", "我推动"]):
            misses.append("这版仍然偏岗位理解，缺少一段你亲自做过或推动过的产品经历，所以说服力还不够。")
        if not _has_any(answer, ["取舍", "优先级", "砍掉", "MVP", "版本"]):
            misses.append("产品经理面试会追问取舍，你需要补一句你会如何定 MVP 优先级，而不是只说完整流程。")
        if not _has_any(answer, ["验证", "指标", "数据", "用户反馈"]):
            misses.append("还需要说明上线后怎么判断方案有效，例如看数据、用户反馈或任务完成情况。")

    if job_type == "robot":
        if not _has_any(answer, ["我负责", "我定位", "我调整", "我验证", "我建立"]):
            misses.append("机器人岗位很看个人排障能力，需要说清你具体负责哪一步，而不是只描述团队或系统。")
        if not _has_any(answer, ["指标", "成功率", "延迟", "接管", "恢复", "稳定"]):
            misses.append("还缺少稳定性验证指标，例如任务成功率、延迟、接管次数或故障恢复时间。")

    if len(answer.strip()) < 120:
        misses.append("回答偏短，信息量不足，至少需要补充一个具体经历或模拟任务。")

    return misses


def _answer_specific_advice(question: str, answer: str, job_type: str) -> List[str]:
    if job_type == "pm":
        return [
            "下一版按“用户场景-核心痛点-产品动作-验证指标-风险兜底”回答。",
            "补一个你亲自参与的产品例子，说明你负责了需求拆解、原型、数据验证或迭代中的哪一环。",
            "把 AI 产品边界说成具体机制：结果解释、用户可编辑、异常兜底、人工确认或反馈闭环。",
        ]
    if job_type == "robot":
        return [
            "下一版按“现场场景-系统问题-我的动作-验证指标-下一步改法”回答。",
            "补清你在感知、定位、规划、控制、硬件或网络链路中具体负责哪一步。",
            "用任务成功率、接管次数、故障恢复时间或安全边界验证结果。",
        ]
    return []


def _question_focus(question: str, job_type: str) -> Dict[str, List[str] | str]:
    if all(word in question for word in ["流量", "产品", "交付"]):
        return {
            "hit": [
                "你开始把算法岗位放进业务链路里思考，而不是只讲模型本身。",
                "如果回答里能区分流量、产品、交付三层，就已经抓住了这题的基本框架。",
            ],
            "missed": [
                "这题必须明确说明“流量-产品-交付”各自怎么创造价值，不能只说 AI 能提升业务。",
                "必须选择一个优先优化环节，并解释为什么它比另外两环更优先。",
            ],
            "advice": [
                "第一句直接拆链路：流量负责获客，产品负责体验，交付负责稳定上线和结果兑现。",
                "第二句给优先级：例如优先交付，因为没有稳定交付，流量和产品体验都无法转化成业务结果。",
                "第三句给策略：建立指标、排查链路、控制成本、上线监控、持续迭代。",
            ],
            "sample": "我会优先优化交付环节，因为 AI 项目如果停在 demo，无法稳定上线、监控成本和验证效果，就不能真正创造业务价值。",
        }
    if any(word in question for word in ["冲突", "平衡", "取舍", "效果", "成本"]):
        return {
            "hit": [
                "如果你提到效果、成本、速度或稳定性之间的矛盾，就抓住了这题的业务取舍方向。",
                "这题看重的是决策方法，不是技术名词堆叠。",
            ],
            "missed": [
                "需要说清冲突双方是什么，例如效果 vs 成本、准确率 vs 时延、体验 vs 资源。",
                "需要说明你用什么指标做判断，以及最后如何选择。",
            ],
            "advice": [
                "按“冲突是什么-判断指标-取舍动作-验证结果”组织。",
                "给出一个具体案例或模拟案例，不要只说会综合考虑。",
                "结尾说明这个取舍如何服务业务目标。",
            ],
            "sample": "当效果和成本冲突时，我会先看业务目标是否要求高准确率，再用小样本实验比较不同方案的成本、时延和效果，最后选择业务可接受的平衡点。",
        }
    if any(word in question for word in ["目标公司", "岗位", "适合"]):
        return {
            "hit": [
                "如果你说明了岗位解决什么问题，就比单纯说感兴趣更有效。",
                "如果你把个人经历和岗位要求连接起来，就能形成初步匹配度。",
            ],
            "missed": [
                "需要更具体地说明你研究过这个岗位，而不是只讲你对方向感兴趣。",
                "需要拿一段经历证明你适合，而不是只说愿意学习。",
            ],
            "advice": [
                "按“岗位核心-我的相关经历-我能带来的价值”回答。",
                "补一个能证明岗位能力的经历，例如数据处理、模型评测、上线部署或成本优化。",
                "最后说明这段经历如何降低公司的培养成本或用人风险。",
            ],
            "sample": "我理解这个岗位需要把算法能力转成业务结果，我适合的原因是我能把问题拆成数据、模型、评测和上线几个环节，并用结果验证。",
        }
    if any(word in question for word in ["成就感", "最成功", "最硬核"]):
        return {
            "hit": [
                "这题适合展示你解决过的具体困难。",
                "如果回答里有难点、行动和结果，就能形成可信故事。",
            ],
            "missed": [
                "不能只说项目名称，需要讲清当时最难的点。",
                "需要说明你的关键动作和结果变化，否则成就感没有证据。",
            ],
            "advice": [
                "按 STAR+L 回答：场景、任务、行动、结果，再连接岗位价值。",
                "重点放在你亲自推动的动作，不要把团队成果直接当成个人成果。",
                "用一个指标或可观察结果收尾。",
            ],
            "sample": "当时最大难点是数据质量不稳定，我先定位异常来源，再调整清洗规则和评测集，最后让结果更稳定，并把这套方法复用到后续任务。",
        }
    scenario = JOB_SCENARIOS.get(job_type, JOB_SCENARIOS["ai"])
    action = JOB_ACTIONS.get(job_type, JOB_ACTIONS["ai"])
    return {
        "hit": [
            "如果你能把回答落到具体任务，就比只讲岗位理解更有说服力。",
            "这题需要展示你能把问题拆成流程、动作和结果。",
        ],
        "missed": [
            f"需要落到一个具体任务，可以围绕 {scenario} 展开。",
            "需要说明你个人负责什么动作，以及这个动作带来什么结果。",
        ],
        "advice": [
            f"补一个具体场景：{scenario}。",
            f"补个人动作：{action}。",
            "补结果或下一步改法：说明结果如何验证、下一步如何优化。",
        ],
        "sample": "我会先明确任务目标和约束，再拆解执行步骤，过程中记录问题，最后用结果和验证记录证明方案有效。",
    }


def _first_text(items: List[str], default: str, max_len: int = 42) -> str:
    for item in items:
        text = str(item).strip()
        if text:
            return text[:max_len]
    return default


def _build_quick_feedback_fields(hit_points: List[str], missed_points: List[str], rewrite_advice: List[str], sample_rewrite: str, question: str, answer: str) -> Dict[str, str]:
    text = answer.strip()
    if not text or len(text) < 8:
        return {
            "quick_judgement": "回答无效，需要重答",
            "most_important_fix": "先正面回答问题，再补场景和动作",
            "rewrite_example": "下一版先正面回答问题，再补具体场景、个人动作和结果。",
            "follow_up_question": "你能举一个真实例子吗？",
        }

    quick_judgement = _first_text(missed_points, "方向基本相关，但证据不够", 25)
    most_important_fix = _first_text(missed_points, "补清楚你的个人动作和验证结果", 35)
    rewrite_source = sample_rewrite or _first_text(rewrite_advice, "按场景、动作、结果重写这一题", 140)
    follow_up = "这个结果你是怎么验证的？"

    if hit_points and not missed_points:
        quick_judgement = "方向可用，继续补强证据"
    if any(word in most_important_fix for word in ["答非所问", "跑题"]):
        quick_judgement = "答非所问，需要重答"
        follow_up = "请重新围绕本题回答。"

    return {
        "quick_judgement": quick_judgement,
        "most_important_fix": most_important_fix,
        "rewrite_example": str(rewrite_source).strip()[:160] or "下一版先正面回答问题，再补具体场景、个人动作和结果。",
        "follow_up_question": follow_up,
    }


def build_rule_based_interview_feedback(question: str, answer: str, job_type: str, assessment: Dict) -> Dict:
    """Build concrete qualitative fallback feedback without exposing scores."""
    focus = _question_focus(question, job_type)
    text = answer.strip()

    hit_points: List[str] = _answer_specific_hits(question, text, job_type) or list(focus["hit"])
    missed_points: List[str] = _answer_specific_misses(question, text, job_type) or list(focus["missed"])
    rewrite_advice: List[str] = _answer_specific_advice(question, text, job_type) or list(focus["advice"])

    if not _has_any(text, VALUE_MARKERS):
        missed_points.append("回答里还缺少“我能解决什么问题、带来什么结果”的价值证明。")

    if not _has_any(text, TRUST_MARKERS):
        missed_points.append("缺少让人相信你可靠的证据，例如个人动作、流程、数据、验证记录或异常处理。")

    if not (_has_any(text, MATCH_MARKERS) or assessment.get("relevance", 0) >= 4):
        missed_points.append("回答和目标岗位的连接还不够明显，需要明确这段经历为什么匹配岗位。")

    if "我" not in text and "本人" not in text:
        missed_points.append("个人贡献不够清楚，需要说明“我具体做了什么”。")

    sample_rewrite = str(focus["sample"])

    quick_fields = _build_quick_feedback_fields(
        hit_points,
        missed_points,
        rewrite_advice,
        sample_rewrite,
        question,
        text,
    )

    return {
        "score": int(assessment.get("total", 0)),
        "is_relevant": assessment.get("relevance", 0) > 0,
        "strict_reason": "定性反馈分析",
        "dimensions": [
            {"label": "回答亮点", "score": 0, "comment": "?".join(hit_points)},
            {"label": "提升方向", "score": 0, "comment": "?".join(missed_points)},
            {"label": "行动建议", "score": 0, "comment": "?".join(rewrite_advice)},
        ],
        "suggestion": quick_fields["most_important_fix"],
        "hit_points": hit_points,
        "missed_points": missed_points,
        "rewrite_advice": rewrite_advice,
        "sample_rewrite": sample_rewrite,
        "summary": quick_fields["quick_judgement"],
        **quick_fields,
    }
