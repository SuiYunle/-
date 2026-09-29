import json
import re

# 读取 bingli1.txt
with open('data/bingli1.txt', 'r', encoding='utf-8') as f:
    content1 = f.read()

# 读取 bingli2.txt  
with open('data/bingli2.txt', 'r', encoding='utf-8') as f:
    content2 = f.read()

# 解析函数
def parse_cases(text, start_id=1):
    cases = []
    case_pattern = r'## 病例[一二三四五六七八九十\d]+：([^#\n]+)'
    matches = list(re.finditer(case_pattern, text))
    
    for i, match in enumerate(matches):
        case_title = match.group(1).strip()
        start = match.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        case_text = text[start:end]
        
        case_id = f'C{start_id + i:03d}'
        case = {'case_id': case_id, 'title': case_title}
        
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

cases1 = parse_cases(content1, 1)
cases2 = parse_cases(content2, 9)

all_cases = cases1 + cases2

# 转换为 cases.json 格式
def convert_to_json_format(cases):
    json_cases = []
    for case in cases:
        # 从 basic_info 解析患者信息
        patient_info = {}
        basic = case.get('basic_info', '')
        for line in basic.split('\n'):
            line = line.strip()
            if line.startswith('- **'):
                parts = line[4:].split('**')
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = parts[1].strip().lstrip(':：')
                    patient_info[key] = value
        
        # 解析诊断信息
        diagnosis = {}
        diag_text = case.get('diagnosis_analysis', '')
        for line in diag_text.split('\n'):
            line = line.strip()
            if line.startswith('- **'):
                parts = line[4:].split('**')
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = parts[1].strip().lstrip(':：')
                    if key == '辨病':
                        diagnosis['disease'] = value
                    elif key == '辨证':
                        diagnosis['syndrome'] = value
                    elif key == '病位':
                        diagnosis['location'] = value
                    elif key == '病性':
                        diagnosis['nature'] = value
                    elif key == '病机':
                        diagnosis['pathogenesis'] = value
        
        # 解析处方
        treatment = {}
        presc = case.get('prescription', '')
        if '方药' in presc:
            treatment['herbal_medicine'] = presc
        if '用法' in presc:
            treatment['usage'] = presc.split('用法')[-1].strip()
        if '方义' in presc:
            treatment['formula_analysis'] = presc.split('方义')[-1].strip()
        
        # 从医嘱提取饮食和生活建议
        advice = case.get('medical_advice', '')
        dietary = []
        lifestyle = []
        for line in advice.split('\n'):
            line = line.strip().lstrip('- ')
            if any(kw in line for kw in ['饮食', '忌食', '宜食', '食疗']):
                dietary.append(line)
            elif any(kw in line for kw in ['保暖', '休息', '运动', '作息', '调畅', '情志', '艾灸', '按摩']):
                lifestyle.append(line)
        
        if dietary:
            treatment['dietary_advice'] = '；'.join(dietary)
        if lifestyle:
            treatment['lifestyle_advice'] = '；'.join(lifestyle)
        
        # 构建标准格式
        json_case = {
            "case_id": case['case_id'],
            "patient_info": {
                "age": patient_info.get('年龄', ''),
                "gender": patient_info.get('性别', ''),
                "occupation": patient_info.get('职业', ''),
                "medical_history": patient_info.get('既往病史', patient_info.get('病史', ''))
            },
            "chief_complaint": case.get('chief_complaint', '').strip(),
            "present_illness": case.get('present_illness', '').strip(),
            "physical_examination": {
                "general_condition": "",
                "tongue": "",
                "pulse": "",
                "other_signs": ""
            },
            "diagnosis": diagnosis,
            "treatment": treatment,
            "outcome": case.get('followup', '').strip(),
            "follow_up": case.get('followup', '').strip(),
            "source": "中医病例数据库",
            "ai_learning_points": case.get('ai_points', '').strip()
        }
        
        # 解析望闻切诊
        insp = case.get('inspection', '')
        for line in insp.split('\n'):
            line = line.strip().lstrip('- ')
            if '舌' in line and '象' in line:
                json_case['physical_examination']['tongue'] = line.split('：')[-1].split(':')[-1].strip()
            elif '神色' in line or '面色' in line:
                json_case['physical_examination']['general_condition'] = line.split('：')[-1].split(':')[-1].strip()
            elif '咽' in line or '喉' in line:
                json_case['physical_examination']['other_signs'] = line.split('：')[-1].split(':')[-1].strip()
        
        palpa = case.get('palpation', '')
        for line in palpa.split('\n'):
            line = line.strip().lstrip('- ')
            if '脉' in line and '象' in line:
                json_case['physical_examination']['pulse'] = line.split('：')[-1].split(':')[-1].strip()
            elif '按诊' in line:
                json_case['physical_examination']['other_signs'] += '；' + line.split('：')[-1].split(':')[-1].strip()
        
        json_cases.append(json_case)
    
    return json_cases

json_cases = convert_to_json_format(all_cases)

# 保存
output = {
    "name": "中医病例数据库",
    "description": "标准化中医病例数据，包含症状、体征、诊断、治疗方案等信息，共20个典型病例",
    "template": {
        "case_id": "病例ID",
        "patient_info": {
            "age": "年龄",
            "gender": "性别",
            "occupation": "职业",
            "medical_history": "既往病史"
        },
        "chief_complaint": "主诉",
        "present_illness": "现病史",
        "physical_examination": {
            "general_condition": "一般情况",
            "tongue": "舌象",
            "pulse": "脉象",
            "other_signs": "其他体征"
        },
        "diagnosis": {
            "disease": "疾病诊断",
            "syndrome": "证候诊断",
            "western_diagnosis": "西医诊断（如有）"
        },
        "treatment": {
            "herbal_medicine": "中药方剂",
            "acupuncture": "针灸治疗（如有）",
            "dietary_advice": "饮食建议",
            "lifestyle_advice": "生活方式建议"
        },
        "outcome": "治疗结果",
        "follow_up": "随访情况"
    },
    "cases": json_cases,
    "categories": [
        {"id": "cat1", "name": "内科疾病", "cases": [c['case_id'] for c in json_cases if c['diagnosis'].get('disease') in ['感冒', '咳嗽', '胃痛', '不寐', '头痛', '便秘', '眩晕', '胸痹', '水肿', '消渴', '黄疸', '淋证', '郁证', '痹证', '耳鸣', '哮病']]},
        {"id": "cat2", "name": "妇科疾病", "cases": [c['case_id'] for c in json_cases if c['diagnosis'].get('disease') in ['痛经', '崩漏']]},
        {"id": "cat3", "name": "儿科疾病", "cases": [c['case_id'] for c in json_cases if c['diagnosis'].get('disease') in ['泄泻', '厌食']]},
        {"id": "cat4", "name": "呼吸系统疾病", "cases": [c['case_id'] for c in json_cases if c['diagnosis'].get('disease') in ['感冒', '咳嗽', '哮病']]},
        {"id": "cat5", "name": "消化系统疾病", "cases": [c['case_id'] for c in json_cases if c['diagnosis'].get('disease') in ['胃痛', '便秘']]},
        {"id": "cat6", "name": "心血管系统疾病", "cases": [c['case_id'] for c in json_cases if c['diagnosis'].get('disease') in ['胸痹', '头痛']]},
        {"id": "cat7", "name": "内分泌系统疾病", "cases": [c['case_id'] for c in json_cases if c['diagnosis'].get('disease') in ['消渴']]},
    ]
}

with open('data/cases.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"成功生成 {len(json_cases)} 个病例到 cases.json")
for c in json_cases:
    print(f"  {c['case_id']}: {c['diagnosis'].get('disease', '未知')} - {c['diagnosis'].get('syndrome', '未知')}")