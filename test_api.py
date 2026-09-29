import sys
sys.path.insert(0, 'F:/脉衡界_完整备份_20260806/backend')
import os
os.chdir('F:/脉衡界_完整备份_20260806/backend')

# 测试加载医案
from app import load_cases
data = load_cases()
print('Loaded {} cases'.format(len(data.get('cases', []))))
print('Categories: {}'.format(len(data.get('categories', []))))

# 测试搜索逻辑
cases = data.get('cases', [])
query = '咳嗽'
scored = []
import json
for case in cases:
    case_text = json.dumps(case, ensure_ascii=False).lower()
    if query.lower() in case_text:
        scored.append(case)
print('Search "咳嗽" found {} cases'.format(len(scored)))
for c in scored[:3]:
    print('  {}: {} - {}'.format(c['case_id'], c['diagnosis'].get('disease', ''), c['diagnosis'].get('syndrome', '')))

# 测试获取单个医案
print('\n--- Test get case C001 ---')
for case in cases:
    if case.get('case_id') == 'C001':
        print('case_id:', case.get('case_id'))
        print('chief_complaint:', case.get('chief_complaint'))
        print('diagnosis:', case.get('diagnosis'))
        print('treatment:', case.get('treatment'))
        print('ai_learning_points:', case.get('ai_learning_points', '')[:100])
        break