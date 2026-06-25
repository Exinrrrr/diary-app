"""自动格式化 — 将行程流水账转为结构化日记"""

from typing import Optional

# 时间段关键词
TIME_KEYWORDS = {
    'morning':   ['早上', '上午', '早晨', '晨', '早起', '早餐', '早饭'],
    'afternoon': ['下午', '午后'],
    'noon':      ['中午', '午饭', '午餐', '午休', '午'],
    'evening':   ['晚上', '晚饭', '晚餐', '傍晚', '夜里', '夜间', '夜晚'],
}

# 时间段标签
PERIOD_LABELS = {
    'morning':   '早上',
    'noon':      '午饭',
    'afternoon': '下午',
    'evening':   '晚上',
    'uncategorized': '其他',
}

# 时间段 emoji
PERIOD_EMOJI = {
    'morning':   '🌅',
    'noon':      '🍽️',
    'afternoon': '☀️',
    'evening':   '🌙',
    'uncategorized': '📝',
}

# 活动关键词 → emoji 映射
ACTIVITY_EMOJI = {
    # 参观考察
    '参观': '🏛️', '考察': '🏛️', '访问': '🏛️', '博物馆': '🏛️',
    '恭王府': '🏯', '故宫': '🏯', '天安门': '🏯', '长城': '🏯',
    # 工作
    '会议': '💼', '开会': '💼', '讨论': '💼', '工作': '💼',
    '入职': '💼', '开幕': '🎉', '实习': '💼',
    # 餐饮
    '吃饭': '🍜', '午饭': '🍜', '晚饭': '🍜', '食堂': '🍜',
    '烤鸭': '🦆', '餐厅': '🍜', '涮涮锅': '🍲', '锅包肉': '🥩',
    '铁锅炖': '🍲', '顺德菜': '🍲', '双皮奶': '🍮',
    # 出行
    '骑车': '🚴', '单车': '🚴', '共享单车': '🚴',
    '地铁': '🚇', '打车': '🚗', '出行': '🚗', '机场': '✈️',
    '飞机': '✈️', '酒店': '🏨', '入住': '🏨',
    # 学习
    '学习': '📚', '看书': '📚', '培训': '📚', '校史馆': '📚',
    '清华': '🎓', '大学': '🎓',
    # 天气
    '下雨': '🌧️', '雨': '🌧️',
    # 公园/户外
    '公园': '🌳', '景山': '🌳', '什刹海': '🌊', '社区': '🏘️',
    # 拍照打卡
    '拍照': '📸', '打卡': '📸', '照片': '📸',
    # 购物
    '超市': '🛒', '买': '🛍️', '手信': '🎁',
    # 团建/社交
    '团建': '🎉', '聚会': '🎉',
    # 其他
    '介绍': '📋', '参观': '🏛️',
}


def classify_time_period(line: str) -> str:
    """识别一行文本属于哪个时间段"""
    for period, keywords in TIME_KEYWORDS.items():
        for kw in keywords:
            if kw in line:
                return period
    return 'uncategorized'


def find_activity_emoji(line: str) -> Optional[str]:
    """根据关键词匹配活动 emoji，匹配最长关键词优先"""
    best = None
    best_len = 0
    for keyword, emoji in ACTIVITY_EMOJI.items():
        if keyword in line and len(keyword) > best_len:
            best = emoji
            best_len = len(keyword)
    return best


def auto_format(raw_text: str) -> str:
    """
    将原始行程文本自动排版为结构化 markdown 日记。

    输入示例：
        早上去社区参观
        下午开会讨论了项目进展
        午饭吃了食堂

    输出：按时间段分组的 markdown，带 emoji
    """
    if not raw_text or not raw_text.strip():
        return ''

    # 1. 拆分为行
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

    # 2. 分类
    classified = {
        'morning': [],
        'noon': [],
        'afternoon': [],
        'evening': [],
        'uncategorized': [],
    }

    for line in lines:
        period = classify_time_period(line)
        classified[period].append(line)

    # 3. 生成 markdown
    output_parts = []
    # 按时间顺序输出
    order = ['morning', 'noon', 'afternoon', 'evening']

    for period in order:
        items = classified[period]
        if not items:
            continue
        emoji = PERIOD_EMOJI[period]
        label = PERIOD_LABELS[period]
        output_parts.append(f'## {emoji} {label}\n')
        for item in items:
            activity_emoji = find_activity_emoji(item)
            prefix = f'{activity_emoji} ' if activity_emoji else ''
            output_parts.append(f'- {prefix}{item}')
        output_parts.append('')  # 空行分隔

    # 处理未分类的
    if classified['uncategorized']:
        output_parts.append(f'## 📝 其他\n')
        for item in classified['uncategorized']:
            activity_emoji = find_activity_emoji(item)
            prefix = f'{activity_emoji} ' if activity_emoji else ''
            output_parts.append(f'- {prefix}{item}')
        output_parts.append('')

    return '\n'.join(output_parts).strip()
