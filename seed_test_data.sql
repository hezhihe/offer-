-- ===== 1. 创建测试账号 =====

INSERT INTO public.users_data (phone, hashed_password, nickname) VALUES ('13800001111', '$2b$12$vKzoGz4gt1qX92w1tIbgNOot.xVatG5ztDEP42WiJo3kSK4b3Fp6e', '张同学') ON CONFLICT (phone) DO NOTHING;
INSERT INTO public.users_data (phone, hashed_password, nickname) VALUES ('13800002222', '$2b$12$WXOThYQOjjFgPzjNLyMvw.L89RbxuXIV5bk1M9neU7WoMTYnnqZKC', '李同学') ON CONFLICT (phone) DO NOTHING;
INSERT INTO public.users_data (phone, hashed_password, nickname) VALUES ('13800003333', '$2b$12$CgAfsFO4ux7ptKEfoq2twOxhGT82UrlxS3jQAbPT8YKLjk0L7Hvs2', '王同学') ON CONFLICT (phone) DO NOTHING;

-- ===== 2. 简历分析历史 =====

INSERT INTO public.resume_history (user_phone, job_title, original_jd, original_resume, match_score, keywords, reconstructed_resume) VALUES ('13800001111', 'AI算法工程师', '要求: Python, PyTorch, Transformer, NLP, 大模型微调', '张同学|某211计算机本科|Python项目经验|PyTorch图像分类', 68, '[{"word": "Python", "match": "true", "reason": "有Python项目经验"}, {"word": "PyTorch", "match": "true", "reason": "有PyTorch课设"}, {"word": "Transformer", "match": "false", "reason": "未体现相关经验"}, {"word": "NLP", "match": "false", "reason": "未涉及NLP项目"}, {"word": "大模型", "match": "false", "reason": "暂无大模型经验"}]', '【优化后简历】
个人概况：张同学，某211计算机本科

专业技能：
- Python：✅ 已匹配
- PyTorch：✅ 已匹配

项目经验：
1. 图像分类项目（STAR法则重构，S：课程设计 T：独立完成猫狗图像分类 A：使用PyTorch搭建CNN模型，调参优化 R：分类准确率达到88%）

优化建议：
1. 补充NLP或大模型相关项目经验
2. 量化项目成果，添加准确率等指标');
INSERT INTO public.resume_history (user_phone, job_title, original_jd, original_resume, match_score, keywords, reconstructed_resume) VALUES ('13800001111', '产品经理', '要求: 用户调研, 需求分析, Axure, PRD, 数据分析', '张同学|某211计算机本科|做过校园二手交易小程序|调查过100个同学需求|用墨刀画过原型', 72, '[{"word": "用户调研", "match": "true", "reason": "调查过100个同学"}, {"word": "需求分析", "match": "true", "reason": "分析过用户痛点"}, {"word": "Axure", "match": "false", "reason": "未使用Axure"}, {"word": "PRD", "match": "false", "reason": "未体现PRD经验"}, {"word": "数据分析", "match": "false", "reason": "未体现数据分析能力"}]', '【优化后简历】
个人概况：张同学，某211计算机本科

专业技能：
- 用户调研：✅ 已匹配（100人调研）
- 原型设计：⚠️ 建议补充（墨刀→Axure）

优化建议：
1. 将小程序经历用STAR法则重构
2. 建议学习Axure并做1-2个高保真原型
3. 补充PRD文档撰写经验');
INSERT INTO public.resume_history (user_phone, job_title, original_jd, original_resume, match_score, keywords, reconstructed_resume) VALUES ('13800002222', '机器人算法工程师', '要求: ROS, SLAM, C++, 运动控制, 路径规划', '李同学|某985机器人工程硕士|ROS开发经验2年|参与SLAM导航项目|C++/Python熟练', 85, '[{"word": "ROS", "match": "true", "reason": "2年ROS开发经验"}, {"word": "SLAM", "match": "true", "reason": "参与SLAM导航项目"}, {"word": "C++", "match": "true", "reason": "C++熟练"}, {"word": "运动控制", "match": "false", "reason": "未明确体现"}, {"word": "路径规划", "match": "true", "reason": "导航项目涉及"}]', '【优化后简历】
个人概况：李同学，某985机器人工程硕士

项目经验（STAR重构）：
1. 移动机器人SLAM导航系统（S：实验室项目 T：实现室内自主导航 A：基于ROS搭建整套框架，融合激光雷达与IMU R：定位精度<5cm，成功部署演示）

优化建议：
1. 补充运动控制相关项目或课程
2. 项目成果量化：列出定位精度、导航成功率等指标
3. 突出ROS开发深度，不要只说''熟练''');
INSERT INTO public.resume_history (user_phone, job_title, original_jd, original_resume, match_score, keywords, reconstructed_resume) VALUES ('13800002222', '前端开发工程师', '要求: Vue, React, TypeScript, Webpack, 性能优化', '李同学|某985机器人工程硕士|用过Vue写课程项目|了解React|做过简单的响应式页面', 55, '[{"word": "Vue", "match": "true", "reason": "有Vue课程项目"}, {"word": "React", "match": "true", "reason": "了解React"}, {"word": "TypeScript", "match": "false", "reason": "未涉及"}, {"word": "性能优化", "match": "false", "reason": "未体现"}, {"word": "Webpack", "match": "false", "reason": "未使用"}]', '【优化后简历】
个人概况：李同学，某985机器人工程硕士（跨专业）

优化建议：
1. 跨专业求职需重点展示前端项目
2. 建议做1-2个完整前端项目（部署上线）
3. 学习TypeScript并应用到项目中');
INSERT INTO public.resume_history (user_phone, job_title, original_jd, original_resume, match_score, keywords, reconstructed_resume) VALUES ('13800003333', '新媒体运营', '要求: 内容创作, 排版设计, 数据分析, 用户增长, 热点追踪', '王同学|某二本新闻学本科|运营过个人公众号3000粉丝|会PS和剪映|写过10万+阅读文章', 78, '[{"word": "内容创作", "match": "true", "reason": "10万+阅读文章"}, {"word": "排版设计", "match": "true", "reason": "会PS"}, {"word": "数据分析", "match": "false", "reason": "未体现数据能力"}, {"word": "用户增长", "match": "true", "reason": "3000粉丝增长经验"}, {"word": "热点追踪", "match": "false", "reason": "未明确体现"}]', '【优化后简历】
个人概况：王同学，某二本新闻学本科

核心亮点：
- 个人公众号3000粉丝，单篇最高10万+阅读
- 熟练使用PS、剪映等创作工具

优化建议：
1. 10万+文章要说清楚是谁写的、什么主题、做了什么
2. 补充数据分析能力（如阅读量分析、用户画像等）
3. 建议补充多平台运营经验（抖音/小红书/B站）');

-- ===== 3. 面试历史 =====

INSERT INTO public.interview_history (user_phone, job_type, questions, answers, scores, total_score, avg_score, advice) VALUES ('13800001111', 'AI算法', '["请自我介绍一下", "你了解Transformer吗", "你在项目里用过哪些深度学习框架"]', '["我叫张同学，计算机专业...", "Transformer是一种基于注意力机制的...", "我主要用PyTorch，做过图像分类..."]', '[6, 8, 7]', 75, 25.0, '整体表现不错，逻辑清晰。建议：1. 自我介绍控制在60秒内 2. Transformer回答可结合具体项目 3. 深度学习框架可谈使用心得');
INSERT INTO public.interview_history (user_phone, job_type, questions, answers, scores, total_score, avg_score, advice) VALUES ('13800002222', '机器人', '["请自我介绍一下", "描述一下ROS的核心概念", "SLAM的原理是什么"]', '["我是李同学，机器人工程硕士...", "ROS的核心是节点通信...", "SLAM是同时定位与建图..."]', '[9, 8, 9]', 88, 29.3, '专业基础扎实，回答有深度。建议：1. 多结合实践项目举例 2. SLAM回答可以加上实际场景');
INSERT INTO public.interview_history (user_phone, job_type, questions, answers, scores, total_score, avg_score, advice) VALUES ('13800003333', '新媒体', '["请自我介绍一下", "你怎样做内容选题", "如何评估一篇内容的效果"]', '["我是王同学，新闻学专业...", "我会从热点和用户需求出发...", "主要通过阅读量、转发量..."]', '[7, 8, 6]', 72, 24.0, '有实践经验，数据意识可以加强。建议：1. 数据分析能力需要提升 2. 可展示具体增长数据');

-- ===== 完成 =====

-- 复制以上 SQL 到 Supabase SQL Editor 执行

