UPDATE public.jobs
SET capital = CASE company
    WHEN '优必选科技' THEN '上市机器人企业'
    WHEN '大疆创新' THEN '大型科技企业'
    WHEN '宁德时代' THEN '头部新能源企业'
    WHEN '商汤科技' THEN '上市AI企业'
    WHEN '比亚迪' THEN '头部车企'
    WHEN '云从科技' THEN '上市AI企业'
    WHEN '埃斯顿自动化' THEN '上市自动化企业'
    WHEN '亿航智能' THEN '上市eVTOL企业'
    WHEN '光威复材' THEN '上市新材料企业'
    WHEN '科大讯飞' THEN '上市AI企业'
    WHEN '小鹏汇天' THEN '成长型飞行汽车企业'
    WHEN '天合光能' THEN '上市新能源企业'
    WHEN '顺丰无人机' THEN '大型物流集团业务'
    WHEN '新松机器人' THEN '上市机器人企业'
    ELSE capital
END
WHERE company IN (
    '优必选科技',
    '大疆创新',
    '宁德时代',
    '商汤科技',
    '比亚迪',
    '云从科技',
    '埃斯顿自动化',
    '亿航智能',
    '光威复材',
    '科大讯飞',
    '小鹏汇天',
    '天合光能',
    '顺丰无人机',
    '新松机器人'
);
