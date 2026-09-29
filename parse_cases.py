import json
import re

# 读取 bingli1.txt
with open('data/bingli1.txt', 'r', encoding='utf-8-sig') as f:
    content1 = f.read()

# 读取 bingli2.txt  
with open('data/bingli2.txt', 'r', encoding='utf-8-sig') as f:
    content2 = f.read()

# 简单的解析函数
def parse_cases(text):
    cases = []
    # 按病例分割
    case_pattern = r'## 病例[一二三四五六七八九十\d]+：([^#\n]+)'
    matches = list(re.finditer(case_pattern, text))
    
    for i, match in enumerate(matches):
        case_title = match.group(1).strip()
        start = match.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        case_text = text[start:end]
        
        case = {'case_id': f'C{i+1:03d}', 'title': case_title}
        
        # 解析各个章节
        sections = {
            'basic_info': r'### 基本信息\n(.*?)(?=###|\Z)',
            'chief_complaint': r'### 主诉\n(.*?)(?=###|\Z)',
            'present_illness': r'### 问诊摘要\n(.*?)(?=###|\Z)',
            'inspection': r'### 望诊\n(.*?)(?=###|\Z)',
            'auscultation': r'### 闻诊\n(.*?)(?=###|\Z)',
            'palpation': r'### 切诊\n(.*?)(?=###|\Z)',
            'four_diagnosis': r'### 四诊合参\n(.*?)(?=###|\Z)',
            'diagnosis_analysis': r'### 辨证分析\n(.*?)(?=###|\Z)',
            'treatment_principle': r'### 治法\n(.*?)(?=###|\Z)',
            'prescription': r'### 处方\n(.*?)(?=###|\Z)',
            'medical_advice': r'### 医嘱与调护\n(.*?)(?=###|\Z)',
            'followup': r'### 复诊记录\([^)]+\)\n(.*?)(?=###|\Z)',
            'ai_points': r'### 【AI学习要点】\n(.*?)(?=###|\Z)',
        }
        
        for key, pattern in sections.items():
            m = re.search(pattern, case_text, re.DOTALL)
            if m:
                case[key] = m.group(1).strip()
        
        cases.append(case)
    
    return cases

cases1 = parse_cases(content1)
cases2 = parse_cases(content2)

print(f'bingli1: {len(cases1)} cases')
print(f'bingli2: {len(cases2)} cases')

# 显示第一个病例的结构
if cases1:
    print(json.dumps(cases1[0], ensure_ascii=False, indent=2)[:2000])