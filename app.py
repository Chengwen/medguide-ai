import json
import os
from collections import Counter
from copy import deepcopy
from pathlib import Path

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RULES_PATH = DATA_DIR / "rules.json"
SAMPLE_CASES_PATH = DATA_DIR / "sample_cases.json"
APP_VERSION = "2026.04.18"
DEFAULT_OPENAI_MODEL = "minimax/minimax-m2.5:free"
DEFAULT_OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_APP_URL = "https://medguide-ai-demo.streamlit.app/"

RISK_ORDER = {
    "emergency": 4,
    "see_doctor_soon": 3,
    "outpatient": 2,
    "home_observation": 1,
}

RISK_LABELS = {
    "zh": {
        "emergency": "紧急处理",
        "see_doctor_soon": "尽快线下就医",
        "outpatient": "普通门诊",
        "home_observation": "居家观察",
    },
    "en": {
        "emergency": "Emergency Care",
        "see_doctor_soon": "See a Doctor Soon",
        "outpatient": "Outpatient Visit",
        "home_observation": "Home Observation",
    },
}

RISK_HELP = {
    "zh": {
        "emergency": "建议立即前往急诊或寻求紧急医疗帮助。",
        "see_doctor_soon": "建议尽快到线下医疗机构就诊，避免拖延。",
        "outpatient": "当前更适合普通门诊或专科门诊进一步评估。",
        "home_observation": "当前可先观察，但若症状加重应尽快就医。",
    },
    "en": {
        "emergency": "Go to the emergency department or seek urgent medical help immediately.",
        "see_doctor_soon": "Visit an in-person medical provider soon and avoid delaying care.",
        "outpatient": "An outpatient or specialist clinic visit is more appropriate at this stage.",
        "home_observation": "You may observe at home for now, but seek care if symptoms get worse.",
    },
}

RISK_ALERT_TYPE = {
    "emergency": "error",
    "see_doctor_soon": "warning",
    "outpatient": "info",
    "home_observation": "success",
}

DEPARTMENT_LABELS = {
    "zh": {
        "emergency": "急诊",
        "general": "全科门诊",
        "respiratory": "呼吸科",
        "gastroenterology": "消化科",
        "dermatology": "皮肤科",
    },
    "en": {
        "emergency": "Emergency",
        "general": "General Practice",
        "respiratory": "Respiratory",
        "gastroenterology": "Gastroenterology",
        "dermatology": "Dermatology",
    },
}

CATEGORY_LABELS = {
    "zh": {
        "respiratory": "呼吸道症状",
        "digestive": "消化道症状",
        "skin": "皮肤问题",
        "general": "一般症状",
    },
    "en": {
        "respiratory": "Respiratory Symptoms",
        "digestive": "Digestive Symptoms",
        "skin": "Skin Concerns",
        "general": "General Symptoms",
    },
}

SEX_LABELS = {
    "zh": {"female": "女", "male": "男", "other": "其他 / 不便说明"},
    "en": {"female": "Female", "male": "Male", "other": "Other / Prefer not to say"},
}

PREGNANCY_LABELS = {
    "zh": {"not_applicable": "不适用", "no": "否", "yes": "是"},
    "en": {"not_applicable": "Not applicable", "no": "No", "yes": "Yes"},
}

WARNING_SIGN_LABELS = {
    "zh": {
        "fever": "发热",
        "pain": "疼痛",
        "bleeding": "出血",
        "breathing_difficulty": "呼吸困难",
    },
    "en": {
        "fever": "Fever",
        "pain": "Pain",
        "bleeding": "Bleeding",
        "breathing_difficulty": "Breathing difficulty",
    },
}

DEMO_USERS = {
    "demo": {
        "password": "demo123",
        "name": {"zh": "演示用户", "en": "Demo User"},
        "role": {"zh": "课程演示账号", "en": "Course Demo Account"},
    },
    "nurse": {
        "password": "triage123",
        "name": {"zh": "导诊人员", "en": "Triage Staff"},
        "role": {"zh": "医护 / 前台复核", "en": "Clinical Review"},
    },
}

CATEGORY_KEYWORDS = {
    "respiratory": ["咳嗽", "发烧", "发热", "胸痛", "气短", "呼吸", "cough", "fever", "chest", "breath", "sputum"],
    "digestive": ["腹痛", "胃", "呕吐", "腹泻", "便血", "abdominal", "stomach", "vomit", "diarrhea", "stool"],
    "skin": ["皮疹", "红疹", "瘙痒", "皮肤", "过敏", "rash", "itch", "skin", "allergy", "red"],
}

FOLLOW_UP_QUESTIONS = {
    "respiratory": [
        {
            "id": "breathing_difficulty",
            "label": {"zh": "是否有呼吸困难", "en": "Are you having difficulty breathing?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "chest_pain",
            "label": {"zh": "是否有胸痛", "en": "Do you have chest pain?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "sputum",
            "label": {"zh": "是否咳痰", "en": "Are you coughing up sputum?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "sputum_color",
            "label": {"zh": "痰液颜色", "en": "What color is the sputum?"},
            "type": "selectbox",
            "options": ["none", "clear", "yellow_green", "bloody"],
            "option_labels": {
                "zh": {"none": "无", "clear": "透明 / 白色", "yellow_green": "黄色 / 绿色", "bloody": "带血"},
                "en": {"none": "None", "clear": "Clear / White", "yellow_green": "Yellow / Green", "bloody": "Blood-stained"},
            },
        },
        {
            "id": "max_temperature",
            "label": {"zh": "体温最高多少度", "en": "What was your highest temperature?"},
            "type": "selectbox",
            "options": ["unknown", "none", "mild", "moderate", "high"],
            "option_labels": {
                "zh": {"unknown": "未测量", "none": "无发热", "mild": "37.5-38.0", "moderate": "38.1-39.0", "high": "39.0以上"},
                "en": {"unknown": "Not measured", "none": "No fever", "mild": "37.5-38.0 C", "moderate": "38.1-39.0 C", "high": "Above 39.0 C"},
            },
        },
    ],
    "digestive": [
        {
            "id": "vomiting",
            "label": {"zh": "是否呕吐", "en": "Have you been vomiting?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "diarrhea",
            "label": {"zh": "是否腹泻", "en": "Do you have diarrhea?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "blood_in_stool",
            "label": {"zh": "是否便血", "en": "Is there blood in the stool?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "pain_location",
            "label": {"zh": "腹痛位置", "en": "Where is the abdominal pain located?"},
            "type": "selectbox",
            "options": ["unclear", "upper", "around_navel", "right_lower", "whole_abdomen"],
            "option_labels": {
                "zh": {"unclear": "不明确", "upper": "上腹部", "around_navel": "脐周", "right_lower": "右下腹", "whole_abdomen": "全腹部"},
                "en": {"unclear": "Not sure", "upper": "Upper abdomen", "around_navel": "Around the navel", "right_lower": "Lower right abdomen", "whole_abdomen": "Whole abdomen"},
            },
        },
        {
            "id": "cannot_eat_or_drink",
            "label": {"zh": "是否无法进食或饮水", "en": "Are you unable to eat or drink?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
    ],
    "skin": [
        {
            "id": "itching",
            "label": {"zh": "是否瘙痒", "en": "Is it itchy?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "wound_or_discharge",
            "label": {"zh": "是否有渗液或破损", "en": "Is there discharge or broken skin?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "spread_speed",
            "label": {"zh": "皮疹扩散速度", "en": "How fast is the rash spreading?"},
            "type": "selectbox",
            "options": ["none", "slow", "fast"],
            "option_labels": {"zh": {"none": "无明显扩散", "slow": "缓慢", "fast": "较快"}, "en": {"none": "No obvious spread", "slow": "Slow", "fast": "Fast"}},
        },
        {
            "id": "skin_fever",
            "label": {"zh": "是否伴随发热", "en": "Is it accompanied by fever?"},
            "type": "radio",
            "options": ["no", "yes"],
            "option_labels": {"zh": {"no": "否", "yes": "是"}, "en": {"no": "No", "yes": "Yes"}},
        },
        {
            "id": "allergen_contact",
            "label": {"zh": "是否近期接触过过敏源", "en": "Have you recently been exposed to an allergen?"},
            "type": "radio",
            "options": ["unknown", "no", "yes"],
            "option_labels": {"zh": {"unknown": "不确定", "no": "否", "yes": "是"}, "en": {"unknown": "Not sure", "no": "No", "yes": "Yes"}},
        },
    ],
}

QUESTION_BY_ID = {
    question["id"]: question
    for questions in FOLLOW_UP_QUESTIONS.values()
    for question in questions
}


def tr(lang: str, zh_text: str, en_text: str) -> str:
    return zh_text if lang == "zh" else en_text


def localized_value(value, lang: str):
    if isinstance(value, dict):
        return value.get(lang) or value.get("en") or value.get("zh") or ""
    return value


def language_name(value: str) -> str:
    return "中文" if value == "zh" else "English"


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def apply_theme_css():
    st.markdown(
        """
        <style>
        :root {
            --medguide-primary: #4a90e2;
            --medguide-primary-soft: rgba(74, 144, 226, 0.12);
            --medguide-primary-border: rgba(74, 144, 226, 0.28);
        }

        .stApp {
            background: linear-gradient(180deg, #f6f9fd 0%, #eef5fc 100%);
        }

        h1, h2, h3 {
            color: #172033;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid var(--medguide-primary-border);
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--medguide-primary-border);
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 12px 28px rgba(23, 32, 51, 0.06);
        }

        .medguide-pill {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: var(--medguide-primary-soft);
            color: var(--medguide-primary);
            font-weight: 700;
            margin-right: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def default_state():
    return {
        "language": "zh",
        "authenticated": False,
        "current_user": None,
        "stage": "home",
        "patient": None,
        "follow_up_answers": {},
        "result": None,
        "review": {},
        "ai_summary": None,
        "completed_assessments": [],
        "selected_sample_id": "",
        "last_result_signature": None,
    }


def init_state():
    for key, value in default_state().items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)


def clear_intake_widgets():
    for key in list(st.session_state.keys()):
        if key.startswith("intake_") or key.startswith("followup_"):
            del st.session_state[key]


def reset_workflow():
    preserved = {
        "language": st.session_state.get("language", "zh"),
        "authenticated": st.session_state.get("authenticated", False),
        "current_user": deepcopy(st.session_state.get("current_user")),
        "completed_assessments": deepcopy(st.session_state.get("completed_assessments", [])),
    }
    for key, value in default_state().items():
        st.session_state[key] = deepcopy(value)
    st.session_state.update(preserved)
    st.session_state["stage"] = "home"
    clear_intake_widgets()


def logout():
    lang = st.session_state.get("language", "zh")
    for key, value in default_state().items():
        st.session_state[key] = deepcopy(value)
    st.session_state["language"] = lang
    clear_intake_widgets()


def detect_category(chief_complaint: str, warning_signs=None) -> str:
    text = (chief_complaint or "").lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword.lower() in text)

    if warning_signs and "breathing_difficulty" in warning_signs:
        scores["respiratory"] += 2
    if warning_signs and "bleeding" in warning_signs:
        scores["digestive"] += 1

    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score > 0 else "general"


def risk_label(risk_level: str, lang: str) -> str:
    return RISK_LABELS[lang].get(risk_level, risk_level)


def department_label(department: str, lang: str) -> str:
    return DEPARTMENT_LABELS[lang].get(department, department)


def category_label(category: str, lang: str) -> str:
    return CATEGORY_LABELS[lang].get(category, category)


def answer_label(question_id: str, answer: str, lang: str) -> str:
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        return str(answer)
    return question.get("option_labels", {}).get(lang, {}).get(answer, str(answer))


def question_label(question_id: str, lang: str) -> str:
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        return question_id
    return localized_value(question["label"], lang)


def set_risk(current: str, target: str) -> str:
    return target if RISK_ORDER[target] > RISK_ORDER[current] else current


def evaluate_case(patient: dict, follow_up_answers: dict, lang: str) -> dict:
    category = detect_category(patient.get("chief_complaint", ""), patient.get("warning_signs", []))
    risk_level = "home_observation" if patient.get("severity", 3) <= 2 else "outpatient"
    red_flags = []
    reasons = []
    warning_signs = set(patient.get("warning_signs", []))

    if patient.get("severity", 3) >= 4:
        risk_level = set_risk(risk_level, "see_doctor_soon")
        reasons.append(tr(lang, "症状严重程度较高。", "Symptom severity is relatively high."))

    if {"pain", "breathing_difficulty"}.issubset(warning_signs):
        risk_level = set_risk(risk_level, "emergency")
        red_flags.append(tr(lang, "胸痛或疼痛伴呼吸困难。", "Pain or chest discomfort with breathing difficulty."))

    if "bleeding" in warning_signs:
        risk_level = set_risk(risk_level, "see_doctor_soon")
        red_flags.append(tr(lang, "存在出血相关警示。", "Bleeding-related warning sign is present."))

    if category == "respiratory":
        if follow_up_answers.get("breathing_difficulty") == "yes" and follow_up_answers.get("chest_pain") == "yes":
            risk_level = set_risk(risk_level, "emergency")
            red_flags.append(tr(lang, "追问中同时出现胸痛与呼吸困难。", "Follow-up indicates both chest pain and breathing difficulty."))
        elif follow_up_answers.get("breathing_difficulty") == "yes" or follow_up_answers.get("max_temperature") == "high":
            risk_level = set_risk(risk_level, "see_doctor_soon")
            red_flags.append(tr(lang, "存在明显呼吸困难或高热风险。", "Possible obvious breathing difficulty or high fever risk."))
        elif "fever" in warning_signs or follow_up_answers.get("max_temperature") in {"moderate", "high"}:
            risk_level = set_risk(risk_level, "see_doctor_soon")
            reasons.append(tr(lang, "呼吸道症状伴发热，建议尽快线下评估。", "Respiratory symptoms with fever suggest in-person assessment soon."))

    if category == "digestive":
        if follow_up_answers.get("blood_in_stool") == "yes" or follow_up_answers.get("cannot_eat_or_drink") == "yes":
            risk_level = set_risk(risk_level, "see_doctor_soon")
            red_flags.append(tr(lang, "消化道症状伴便血或无法进食饮水。", "Digestive symptoms with blood in stool or inability to eat or drink."))
        elif follow_up_answers.get("vomiting") == "yes" and follow_up_answers.get("diarrhea") == "yes":
            risk_level = set_risk(risk_level, "outpatient")
            reasons.append(tr(lang, "存在呕吐和腹泻，需要关注脱水风险。", "Vomiting and diarrhea may increase dehydration risk."))

    if category == "skin":
        if follow_up_answers.get("spread_speed") == "fast" and follow_up_answers.get("skin_fever") == "yes":
            risk_level = set_risk(risk_level, "see_doctor_soon")
            red_flags.append(tr(lang, "皮疹快速扩散并伴随发热。", "The rash is spreading quickly and is accompanied by fever."))
        elif follow_up_answers.get("wound_or_discharge") == "yes":
            risk_level = set_risk(risk_level, "outpatient")
            reasons.append(tr(lang, "存在破损或渗液，建议门诊评估。", "Broken skin or discharge suggests outpatient assessment."))
        elif follow_up_answers.get("allergen_contact") == "yes" and patient.get("severity", 3) <= 2:
            risk_level = set_risk(risk_level, "home_observation")
            reasons.append(tr(lang, "症状较轻且可能与过敏源接触有关。", "Symptoms are mild and may be related to allergen exposure."))

    if not reasons and not red_flags:
        reasons.append(tr(lang, "当前未发现明显红旗症状。", "No obvious red-flag symptoms are detected."))

    department_by_category = {
        "respiratory": "respiratory",
        "digestive": "gastroenterology",
        "skin": "dermatology",
        "general": "general",
    }
    department = "emergency" if risk_level == "emergency" else department_by_category.get(category, "general")

    summary = tr(
        lang,
        f"用户主诉：{patient.get('chief_complaint', '未填写')}；持续时间：{patient.get('duration', '未填写')}；严重程度：{patient.get('severity', '未填写')}/5。",
        f"Chief complaint: {patient.get('chief_complaint', 'Not provided')}; duration: {patient.get('duration', 'Not provided')}; severity: {patient.get('severity', 'Not provided')}/5.",
    )

    return {
        "category": category,
        "risk_level": risk_level,
        "department": department,
        "summary": summary,
        "reasons": reasons,
        "red_flags": red_flags,
        "needs_human_review": risk_level in {"emergency", "see_doctor_soon"} or bool(red_flags),
    }


def record_result(patient: dict, follow_up_answers: dict, result: dict):
    signature = json.dumps(
        {"patient": patient, "follow_up_answers": follow_up_answers, "risk_level": result.get("risk_level")},
        ensure_ascii=False,
        sort_keys=True,
    )
    if st.session_state.get("last_result_signature") == signature:
        return

    st.session_state["completed_assessments"].append(
        {
            "patient": deepcopy(patient),
            "follow_up_answers": deepcopy(follow_up_answers),
            "result": deepcopy(result),
        }
    )
    st.session_state["last_result_signature"] = signature


def format_follow_up_answers(follow_up_answers: dict, lang: str) -> str:
    if not follow_up_answers:
        return tr(lang, "无追问记录", "No follow-up answers")
    return "\n".join(
        f"- {question_label(question_id, lang)}: {answer_label(question_id, answer, lang)}"
        for question_id, answer in follow_up_answers.items()
    )


def get_openai_api_key() -> str:
    for key_name in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        env_key = os.getenv(key_name, "")
        if env_key:
            return env_key

    try:
        return st.secrets.get("OPENROUTER_API_KEY", "") or st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return ""


def get_openai_model() -> str:
    try:
        secret_model = st.secrets.get("OPENROUTER_MODEL", "") or st.secrets.get("OPENAI_MODEL", "")
    except Exception:
        secret_model = ""
    return os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL") or secret_model or DEFAULT_OPENAI_MODEL


def get_openai_base_url() -> str:
    try:
        secret_base_url = st.secrets.get("OPENAI_BASE_URL", "") or st.secrets.get("OPENROUTER_BASE_URL", "")
    except Exception:
        secret_base_url = ""
    return os.getenv("OPENAI_BASE_URL") or os.getenv("OPENROUTER_BASE_URL") or secret_base_url or DEFAULT_OPENAI_BASE_URL


def openai_ready() -> bool:
    return OpenAI is not None and bool(get_openai_api_key())


def ai_config_status(lang: str) -> str:
    sdk_ok = OpenAI is not None
    key_ok = bool(get_openai_api_key())
    model = get_openai_model()
    base_url = get_openai_base_url()

    if sdk_ok and key_ok:
        return tr(
            lang,
            f"已检测到 OpenRouter / OpenAI-compatible 配置。模型：{model}；Base URL：{base_url}",
            f"OpenRouter / OpenAI-compatible configuration detected. Model: {model}; Base URL: {base_url}",
        )

    missing = []
    if not sdk_ok:
        missing.append(tr(lang, "openai Python 包未安装", "openai Python package is not installed"))
    if not key_ok:
        missing.append(tr(lang, "未读取到 OPENROUTER_API_KEY / OPENAI_API_KEY", "OPENROUTER_API_KEY / OPENAI_API_KEY was not found"))

    return tr(
        lang,
        "AI API 未启用：" + "；".join(missing) + "。将使用本地兜底摘要。",
        "AI API is not enabled: " + "; ".join(missing) + ". Local fallback summary will be used.",
    )


def build_ai_summary_prompt(patient: dict, follow_up_answers: dict, result: dict, lang: str) -> str:
    language_instruction = "Chinese" if lang == "zh" else "English"
    payload = {
        "patient": patient,
        "follow_up_answers": follow_up_answers,
        "system_result": result,
    }
    return f"""
Write a concise pre-consultation summary in {language_instruction}.

Requirements:
- Do not diagnose disease.
- Do not recommend medication or treatment.
- Keep it suitable for triage staff and course demonstration.
- Include: main complaint, key follow-up findings, red flags, risk level, suggested department, and human-review note.
- Use clear bullet points.

Input data:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


def generate_local_ai_summary(patient: dict, follow_up_answers: dict, result: dict, lang: str) -> str:
    follow_up_text = format_follow_up_answers(follow_up_answers, lang)
    red_flags = result["red_flags"] or [tr(lang, "未发现明显红旗症状。", "No obvious red-flag findings detected.")]
    red_flag_text = "\n".join(f"- {item}" for item in red_flags)
    reason_text = "\n".join(f"- {item}" for item in result["reasons"])

    if lang == "zh":
        return f"""
**AI 智能摘要（本地兜底版）**

- 主诉：{patient.get("chief_complaint", "未填写")}
- 持续时间：{patient.get("duration", "未填写")}
- 严重程度：{patient.get("severity", "未填写")}/5
- 追问要点：
{follow_up_text}
- 红旗症状：
{red_flag_text}
- 系统判断：{risk_label(result["risk_level"], lang)}，建议科室为 {department_label(result["department"], lang)}
- 判断依据：
{reason_text}
- 人工复核：本摘要仅用于预问诊整理，不构成诊断；若为高风险或信息不完整，应交由医护人员复核。
""".strip()

    return f"""
**AI Smart Summary (local fallback)**

- Chief complaint: {patient.get("chief_complaint", "Not provided")}
- Duration: {patient.get("duration", "Not provided")}
- Severity: {patient.get("severity", "Not provided")}/5
- Follow-up highlights:
{follow_up_text}
- Red-flag findings:
{red_flag_text}
- System output: {risk_label(result["risk_level"], lang)}, suggested department: {department_label(result["department"], lang)}
- Reasoning:
{reason_text}
- Human review: This summary is for pre-consultation organization only. It is not a diagnosis; high-risk or incomplete cases should be reviewed by staff.
""".strip()


def generate_openai_summary(patient: dict, follow_up_answers: dict, result: dict, lang: str) -> str:
    client = OpenAI(
        api_key=get_openai_api_key(),
        base_url=get_openai_base_url(),
        default_headers={
            "HTTP-Referer": DEFAULT_APP_URL,
            "X-OpenRouter-Title": "MedGuide AI",
        },
    )
    response = client.chat.completions.create(
        model=get_openai_model(),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful medical triage writing assistant for an academic prototype. "
                    "You organize information only and never provide diagnosis, medication, or treatment advice."
                ),
            },
            {"role": "user", "content": build_ai_summary_prompt(patient, follow_up_answers, result, lang)},
        ],
        max_tokens=450,
    )
    return response.choices[0].message.content or ""


def generate_ai_summary(patient: dict, follow_up_answers: dict, result: dict, lang: str) -> tuple[str, str]:
    if openai_ready():
        try:
            return generate_openai_summary(patient, follow_up_answers, result, lang), "openai"
        except Exception as error:
            fallback = generate_local_ai_summary(patient, follow_up_answers, result, lang)
            return f"{fallback}\n\n{tr(lang, '提示：OpenRouter / OpenAI-compatible API 调用失败，已使用本地兜底摘要。错误：', 'Note: OpenRouter / OpenAI-compatible API call failed, so local fallback was used. Error: ')}{error}", "fallback"

    return generate_local_ai_summary(patient, follow_up_answers, result, lang), "fallback"


def load_sample_into_widgets(sample: dict, lang: str):
    patient = sample["patient"]
    st.session_state["intake_age"] = patient["age"]
    st.session_state["intake_sex"] = patient["sex"]
    st.session_state["intake_pregnancy"] = patient["pregnancy"]
    st.session_state["intake_chief_complaint"] = localized_value(patient["chief_complaint"], lang)
    st.session_state["intake_duration"] = localized_value(patient["duration"], lang)
    st.session_state["intake_severity"] = patient["severity"]
    st.session_state["intake_warning_signs"] = patient["warning_signs"]
    st.session_state["intake_history"] = localized_value(patient["history"], lang)
    st.session_state["intake_medications"] = localized_value(patient["medications"], lang)
    st.session_state["intake_allergies"] = localized_value(patient["allergies"], lang)


def render_login(lang: str):
    language_col, _ = st.columns([1, 3])
    with language_col:
        selected_language = st.selectbox(
            tr(lang, "界面语言", "Interface Language"),
            ["zh", "en"],
            index=0 if st.session_state["language"] == "zh" else 1,
            format_func=language_name,
            key="login_language",
        )
        if selected_language != st.session_state["language"]:
            st.session_state["language"] = selected_language
            st.rerun()

    st.title("MedGuide AI")
    st.subheader(tr(lang, "登录到医疗智能预问诊原型", "Sign in to the AI Pre-Consultation Prototype"))
    st.info(
        tr(
            lang,
            "课程原型阶段不需要连接数据库。这里使用演示账号完成登录流程，方便展示用户入口和权限边界。",
            "A database is not required for this course prototype. This demo login shows the user entry point and access boundary.",
        )
    )

    left, right = st.columns([1.0, 1.0])
    with left:
        with st.form("login_form"):
            username = st.text_input(tr(lang, "用户名", "Username"), placeholder="demo")
            password = st.text_input(tr(lang, "密码", "Password"), type="password", placeholder="demo123")
            submitted = st.form_submit_button(tr(lang, "登录", "Sign in"), type="primary", use_container_width=True)

        if submitted:
            user = DEMO_USERS.get(username.strip())
            if user and password == user["password"]:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = {
                    "username": username.strip(),
                    "name": user["name"],
                    "role": user["role"],
                }
                st.session_state["stage"] = "home"
                st.success(tr(lang, "登录成功，正在进入系统。", "Signed in successfully. Opening the app."))
                st.rerun()
            else:
                st.error(tr(lang, "用户名或密码不正确。", "Incorrect username or password."))

    with right:
        st.markdown(f"### {tr(lang, '演示账号', 'Demo Accounts')}")
        st.write(f"- `demo` / `demo123`: {tr(lang, '普通演示用户', 'General demo user')}")
        st.write(f"- `nurse` / `triage123`: {tr(lang, '导诊复核用户', 'Triage review user')}")
        st.caption(
            tr(
                lang,
                "真实部署时应替换为数据库、医院账号系统或第三方身份认证服务。",
                "For real deployment, replace this with a database, hospital account system, or third-party authentication provider.",
            )
        )


def render_sidebar(sample_cases, rules_data, lang: str):
    st.sidebar.title("MedGuide AI")
    st.sidebar.caption(tr(lang, "医疗智能预问诊与风险分诊助手", "AI Pre-Consultation and Risk Triage Assistant"))
    st.sidebar.caption(f"{tr(lang, '原型版本', 'Prototype version')}: {APP_VERSION}")

    current_user = st.session_state.get("current_user")
    if current_user:
        st.sidebar.success(f"{tr(lang, '当前用户', 'Current user')}: {localized_value(current_user['name'], lang)}")
        st.sidebar.caption(localized_value(current_user["role"], lang))
        if st.sidebar.button(tr(lang, "退出登录", "Sign out"), use_container_width=True):
            logout()
            st.rerun()

    selected_language = st.sidebar.selectbox(
        tr(lang, "界面语言", "Interface Language"),
        ["zh", "en"],
        index=0 if st.session_state["language"] == "zh" else 1,
        format_func=language_name,
    )
    if selected_language != st.session_state["language"]:
        st.session_state["language"] = selected_language
        st.rerun()

    stage_labels = {
        "home": tr(lang, "首页", "Home"),
        "intake": tr(lang, "基础信息", "Intake"),
        "followup": tr(lang, "动态追问", "Follow-up"),
        "result": tr(lang, "分诊结果", "Result"),
        "review": tr(lang, "人工复核", "Review"),
        "dashboard": tr(lang, "评估看板", "Dashboard"),
    }
    st.sidebar.write(f"{tr(lang, '当前页面', 'Current page')}: **{stage_labels.get(st.session_state['stage'], stage_labels['home'])}**")
    progress = {"home": 0.1, "intake": 0.3, "followup": 0.55, "result": 0.8, "review": 0.95, "dashboard": 1.0}
    st.sidebar.progress(progress.get(st.session_state["stage"], 0.1))

    sample_ids = [""] + [sample["id"] for sample in sample_cases]
    current_sample = st.session_state.get("selected_sample_id", "")
    default_index = sample_ids.index(current_sample) if current_sample in sample_ids else 0
    selected_sample_id = st.sidebar.selectbox(
        tr(lang, "载入示例案例", "Load sample case"),
        sample_ids,
        index=default_index,
        format_func=lambda value: "" if not value else localized_value(next(sample["name"] for sample in sample_cases if sample["id"] == value), lang),
    )

    if st.sidebar.button(tr(lang, "填入示例数据", "Fill sample data"), use_container_width=True):
        if selected_sample_id:
            sample = next(sample for sample in sample_cases if sample["id"] == selected_sample_id)
            st.session_state["selected_sample_id"] = selected_sample_id
            load_sample_into_widgets(sample, lang)
            st.session_state["stage"] = "intake"
            st.rerun()
        else:
            st.sidebar.warning(tr(lang, "请先选择一个示例案例。", "Please select a sample case first."))

    if st.sidebar.button(tr(lang, "重新开始", "Reset"), use_container_width=True):
        reset_workflow()
        st.rerun()

    with st.sidebar.expander(tr(lang, "红旗规则概览", "Red-flag rules"), expanded=False):
        for rule in rules_data.get("general_rules", []):
            st.write(f"- {localized_value(rule['label'], lang)}")


def render_home(sample_cases, lang: str):
    st.title("MedGuide AI")
    st.subheader(tr(lang, "医疗智能预问诊与风险分诊助手", "AI Pre-Consultation and Risk Triage Assistant"))
    st.info(
        tr(
            lang,
            "本系统用于课程项目演示，帮助用户在正式就诊前完成症状整理与风险初筛。",
            "This course-project prototype helps users organize symptoms and complete initial risk screening before seeing a clinician.",
        )
    )
    st.warning(
        tr(
            lang,
            "若存在胸痛、呼吸困难、意识不清或大出血等紧急症状，请立即前往急诊。",
            "If there is chest pain, breathing difficulty, confusion, or heavy bleeding, go to the emergency department immediately.",
        )
    )

    left, right = st.columns([1.3, 1.0])
    with left:
        st.markdown(
            "\n".join(
                [
                    f"### {tr(lang, '原型目标', 'Prototype Goals')}",
                    f"- {tr(lang, '提高初步问诊的信息完整度', 'Improve completeness of early symptom collection')}",
                    f"- {tr(lang, '缩短人工初筛时间', 'Reduce manual intake time')}",
                    f"- {tr(lang, '提供一致性的风险分级建议', 'Provide consistent risk triage suggestions')}",
                    f"- {tr(lang, '强调 AI 辅助而不是替代医生', 'Emphasize AI assistance rather than replacing clinicians')}",
                ]
            )
        )
    with right:
        st.markdown(
            "\n".join(
                [
                    f"### {tr(lang, '适用场景', 'Supported Scenarios')}",
                    f"- {CATEGORY_LABELS[lang]['respiratory']}",
                    f"- {CATEGORY_LABELS[lang]['digestive']}",
                    f"- {CATEGORY_LABELS[lang]['skin']}",
                ]
            )
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(tr(lang, "开始预问诊", "Start Pre-Consultation"), type="primary", use_container_width=True):
            st.session_state["stage"] = "intake"
            st.rerun()
    with col2:
        if st.button(tr(lang, "查看示例案例", "View Sample Cases"), use_container_width=True):
            st.session_state["stage"] = "dashboard"
            st.rerun()

    st.markdown("---")
    st.markdown(f"### {tr(lang, '演示案例预览', 'Sample Case Preview')}")
    preview_cols = st.columns(len(sample_cases))
    for col, sample in zip(preview_cols, sample_cases):
        with col:
            st.markdown(f"**{localized_value(sample['name'], lang)}**")
            st.caption(localized_value(sample["patient"]["chief_complaint"], lang))
            st.write(f"{tr(lang, '预期分诊', 'Expected triage')}: {risk_label(sample['expected_risk_level'], lang)}")


def render_intake(lang: str):
    st.title(tr(lang, "基础信息采集", "Basic Intake Information"))
    st.caption(tr(lang, "请填写对初步分诊有帮助的信息。", "Please provide information that helps with initial triage."))

    with st.form("intake_form"):
        left, right = st.columns(2)
        with left:
            age = st.number_input(tr(lang, "年龄", "Age"), min_value=1, max_value=120, value=st.session_state.get("intake_age", 25))
            sex = st.selectbox(
                tr(lang, "性别", "Sex"),
                ["female", "male", "other"],
                key="intake_sex",
                format_func=lambda value: SEX_LABELS[lang][value],
            )
            pregnancy = st.selectbox(
                tr(lang, "是否怀孕（如适用）", "Pregnancy status (if applicable)"),
                ["not_applicable", "no", "yes"],
                key="intake_pregnancy",
                format_func=lambda value: PREGNANCY_LABELS[lang][value],
            )
            chief_complaint = st.text_area(
                tr(lang, "主诉症状", "Chief complaint"),
                value=st.session_state.get("intake_chief_complaint", ""),
                key="intake_chief_complaint",
                placeholder=tr(lang, "例如：咳嗽三天，伴随低烧", "Example: cough for 3 days with low fever"),
            )
            duration = st.text_input(
                tr(lang, "症状持续时间", "Symptom duration"),
                value=st.session_state.get("intake_duration", ""),
                key="intake_duration",
                placeholder=tr(lang, "例如：3天", "Example: 3 days"),
            )

        with right:
            severity = st.slider(
                tr(lang, "症状严重程度（1-5）", "Symptom severity (1-5)"),
                1,
                5,
                value=st.session_state.get("intake_severity", 3),
                key="intake_severity",
            )
            warning_signs = st.multiselect(
                tr(lang, "当前是否有以下警示症状", "Current warning signs"),
                list(WARNING_SIGN_LABELS[lang].keys()),
                default=st.session_state.get("intake_warning_signs", []),
                key="intake_warning_signs",
                format_func=lambda value: WARNING_SIGN_LABELS[lang][value],
            )
            history = st.text_area(
                tr(lang, "既往病史", "Medical history"),
                value=st.session_state.get("intake_history", ""),
                key="intake_history",
                placeholder=tr(lang, "例如：哮喘 / 胃病 / 过敏体质", "Example: asthma / gastritis / allergy history"),
            )
            medications = st.text_area(
                tr(lang, "当前用药情况", "Current medications"),
                value=st.session_state.get("intake_medications", ""),
                key="intake_medications",
                placeholder=tr(lang, "例如：退烧药 / 抗过敏药", "Example: fever medicine / antihistamine"),
            )
            allergies = st.text_area(
                tr(lang, "过敏史", "Allergies"),
                value=st.session_state.get("intake_allergies", ""),
                key="intake_allergies",
                placeholder=tr(lang, "例如：青霉素过敏", "Example: penicillin allergy"),
            )

        st.caption(
            tr(
                lang,
                "本页面只收集预问诊信息，不提供诊断结论。若出现紧急症状，请优先急诊。",
                "This page only collects pre-consultation information. It does not provide diagnosis. Seek emergency care for urgent symptoms.",
            )
        )
        submitted = st.form_submit_button(tr(lang, "下一步：进入动态追问", "Next: Follow-up Questions"), type="primary", use_container_width=True)

    if submitted:
        if not chief_complaint.strip() or not duration.strip():
            st.error(tr(lang, "请至少填写主诉症状和持续时间。", "Please provide at least the chief complaint and duration."))
            return

        patient = {
            "age": age,
            "sex": sex,
            "pregnancy": pregnancy,
            "chief_complaint": chief_complaint.strip(),
            "duration": duration.strip(),
            "severity": severity,
            "warning_signs": warning_signs,
            "history": history.strip() or tr(lang, "未填写", "Not provided"),
            "medications": medications.strip() or tr(lang, "未填写", "Not provided"),
            "allergies": allergies.strip() or tr(lang, "未填写", "Not provided"),
        }
        st.session_state["patient"] = patient
        st.session_state["follow_up_answers"] = {}
        st.session_state["result"] = None
        st.session_state["review"] = {}
        st.session_state["ai_summary"] = None
        st.session_state["stage"] = "followup"
        st.rerun()


def render_followup(lang: str):
    patient = st.session_state.get("patient")
    if not patient:
        st.session_state["stage"] = "intake"
        st.rerun()

    category = detect_category(patient["chief_complaint"], patient["warning_signs"])
    questions = FOLLOW_UP_QUESTIONS.get(category, [])

    st.title(tr(lang, "动态追问", "Dynamic Follow-up"))
    st.caption(f"{tr(lang, '当前识别的症状类别', 'Detected symptom category')}: {category_label(category, lang)}")
    st.markdown(f"### {tr(lang, '当前主诉', 'Current Chief Complaint')}")
    st.write(patient["chief_complaint"])

    if not questions:
        st.info(tr(lang, "当前症状类别暂无专门追问，将直接生成初步结果。", "No targeted follow-up is available for this category. You can generate a preliminary result directly."))
        if st.button(tr(lang, "直接生成结果", "Generate Result"), type="primary"):
            result = evaluate_case(patient, {}, lang)
            st.session_state["follow_up_answers"] = {}
            st.session_state["result"] = result
            st.session_state["ai_summary"] = None
            record_result(patient, {}, result)
            st.session_state["stage"] = "result"
            st.rerun()
        return

    with st.form("followup_form"):
        answers = {}
        for question in questions:
            question_id = question["id"]
            labels = question["option_labels"][lang]
            options = question["options"]
            if question["type"] == "radio":
                answers[question_id] = st.radio(
                    localized_value(question["label"], lang),
                    options,
                    key=f"followup_{question_id}",
                    format_func=lambda value, labels=labels: labels[value],
                    horizontal=True,
                )
            else:
                answers[question_id] = st.selectbox(
                    localized_value(question["label"], lang),
                    options,
                    key=f"followup_{question_id}",
                    format_func=lambda value, labels=labels: labels[value],
                )

        submitted = st.form_submit_button(tr(lang, "结束追问并生成结果", "Finish and Generate Result"), type="primary", use_container_width=True)

    if submitted:
        result = evaluate_case(patient, answers, lang)
        st.session_state["follow_up_answers"] = answers
        st.session_state["result"] = result
        st.session_state["ai_summary"] = None
        record_result(patient, answers, result)
        st.session_state["stage"] = "result"
        st.rerun()


def render_result(lang: str):
    patient = st.session_state.get("patient")
    follow_up_answers = st.session_state.get("follow_up_answers", {})
    result = st.session_state.get("result")

    if not patient or not result:
        st.session_state["stage"] = "intake"
        st.rerun()

    st.title(tr(lang, "分诊结果", "Triage Result"))
    risk_level = result["risk_level"]
    alert = getattr(st, RISK_ALERT_TYPE.get(risk_level, "info"))
    alert(f"{risk_label(risk_level, lang)}: {RISK_HELP[lang][risk_level]}")

    col1, col2, col3 = st.columns(3)
    col1.metric(tr(lang, "风险等级", "Risk Level"), risk_label(risk_level, lang))
    col2.metric(tr(lang, "建议科室", "Recommended Department"), department_label(result["department"], lang))
    col3.metric(tr(lang, "是否建议人工复核", "Human Review Suggested"), tr(lang, "是", "Yes") if result["needs_human_review"] else tr(lang, "否", "No"))

    st.markdown(f"### {tr(lang, '结构化问诊摘要', 'Structured Summary')}")
    st.write(result["summary"])

    st.markdown(f"### {tr(lang, 'AI 智能摘要', 'AI Smart Summary')}")
    if openai_ready():
        st.caption(ai_config_status(lang))
    else:
        st.warning(ai_config_status(lang))

    if st.button(tr(lang, "生成 AI 摘要", "Generate AI Summary"), type="primary", use_container_width=True):
        summary_text, summary_source = generate_ai_summary(patient, follow_up_answers, result, lang)
        st.session_state["ai_summary"] = {"text": summary_text, "source": summary_source}

    if st.session_state.get("ai_summary"):
        source_label = tr(lang, "真实 OpenRouter / OpenAI-compatible API", "real OpenRouter / OpenAI-compatible API") if st.session_state["ai_summary"]["source"] == "openai" else tr(lang, "本地兜底逻辑", "local fallback logic")
        st.info(f"{tr(lang, '摘要来源', 'Summary source')}: {source_label}")
        st.markdown(st.session_state["ai_summary"]["text"])

    st.markdown(f"### {tr(lang, '判断依据', 'Reasoning')}")
    for reason in result["reasons"]:
        st.write(f"- {reason}")

    st.markdown(f"### {tr(lang, '红旗症状提示', 'Red-Flag Findings')}")
    if result["red_flags"]:
        for flag in result["red_flags"]:
            st.write(f"- {flag}")
    else:
        st.write(tr(lang, "未发现明显红旗症状。", "No obvious red-flag findings detected."))

    st.markdown(f"### {tr(lang, '追问记录', 'Follow-up Answers')}")
    if follow_up_answers:
        for question_id, answer in follow_up_answers.items():
            st.write(f"- {question_label(question_id, lang)}: **{answer_label(question_id, answer, lang)}**")
    else:
        st.write(tr(lang, "没有追问记录。", "No follow-up answers recorded."))

    st.caption(
        tr(
            lang,
            "免责声明：本结果仅用于课程原型演示，不构成医疗建议，不替代专业医生诊断。",
            "Disclaimer: This result is only for a course prototype demonstration. It is not medical advice and does not replace professional diagnosis.",
        )
    )

    export_payload = {
        "patient": patient,
        "follow_up_answers": follow_up_answers,
        "result": result,
        "ai_summary": st.session_state.get("ai_summary"),
        "app_version": APP_VERSION,
    }
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            tr(lang, "导出摘要（JSON）", "Export Summary (JSON)"),
            data=json.dumps(export_payload, ensure_ascii=False, indent=2),
            file_name="medguide_result.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        if st.button(tr(lang, "进入人工复核", "Open Human Review"), use_container_width=True):
            st.session_state["stage"] = "review"
            st.rerun()
    with col3:
        if st.button(tr(lang, "查看看板", "View Dashboard"), use_container_width=True):
            st.session_state["stage"] = "dashboard"
            st.rerun()
    with col4:
        if st.button(tr(lang, "重新问诊", "New Intake"), use_container_width=True):
            reset_workflow()
            st.session_state["stage"] = "intake"
            st.rerun()


def render_review(lang: str):
    patient = st.session_state.get("patient")
    follow_up_answers = st.session_state.get("follow_up_answers", {})
    result = st.session_state.get("result")

    if not patient or not result:
        st.session_state["stage"] = "intake"
        st.rerun()

    st.title(tr(lang, "医护 / 前台复核", "Human Review"))
    st.caption(tr(lang, "这一页用于强调 AI 辅助与人工兜底。", "This page highlights AI assistance with human oversight."))

    left, right = st.columns([1.1, 1.0])
    with left:
        st.markdown(f"### {tr(lang, '患者基本信息摘要', 'Patient Summary')}")
        st.write(f"- {tr(lang, '年龄', 'Age')}: {patient['age']}")
        st.write(f"- {tr(lang, '性别', 'Sex')}: {SEX_LABELS[lang][patient['sex']]}")
        st.write(f"- {tr(lang, '主诉', 'Chief complaint')}: {patient['chief_complaint']}")
        st.write(f"- {tr(lang, '系统风险等级', 'System risk level')}: {risk_label(result['risk_level'], lang)}")
        st.write(f"- {tr(lang, '系统建议科室', 'System department')}: {department_label(result['department'], lang)}")

        st.markdown(f"### {tr(lang, '追问记录', 'Follow-up Answers')}")
        if follow_up_answers:
            for question_id, answer in follow_up_answers.items():
                st.write(f"- {question_label(question_id, lang)}: **{answer_label(question_id, answer, lang)}**")
        else:
            st.write(tr(lang, "没有追问记录。", "No follow-up answers recorded."))

    with right:
        department_keys = list(DEPARTMENT_LABELS[lang].keys())
        default_department_index = department_keys.index(result["department"]) if result["department"] in department_keys else 1
        final_department = st.selectbox(
            tr(lang, "人工确认科室", "Final Department"),
            department_keys,
            index=default_department_index,
            format_func=lambda value: DEPARTMENT_LABELS[lang][value],
        )
        final_action = st.radio(
            tr(lang, "人工处理结论", "Final Action"),
            ["accept", "adjust", "take_over"],
            format_func=lambda value: {
                "zh": {"accept": "采纳系统建议", "adjust": "调整后采纳", "take_over": "人工接管"},
                "en": {"accept": "Accept system suggestion", "adjust": "Accept with adjustment", "take_over": "Human takeover"},
            }[lang][value],
        )
        review_notes = st.text_area(
            tr(lang, "复核备注", "Review Notes"),
            placeholder=tr(lang, "例如：建议优先联系线下门诊确认。", "Example: Recommend confirming with an in-person clinic first."),
        )

        if st.button(tr(lang, "保存复核结果", "Save Review"), type="primary", use_container_width=True):
            st.session_state["review"] = {
                "final_department": final_department,
                "final_action": final_action,
                "review_notes": review_notes.strip() or tr(lang, "无补充说明", "No additional notes"),
            }
            st.success(tr(lang, "复核结果已保存。", "Review result saved."))

    review = st.session_state.get("review", {})
    if review:
        st.markdown(f"### {tr(lang, '已保存的复核结论', 'Saved Review Result')}")
        st.write(f"- {tr(lang, '最终科室', 'Final department')}: {department_label(review['final_department'], lang)}")
        st.write(f"- {tr(lang, '备注', 'Notes')}: {review['review_notes']}")

    col1, col2 = st.columns(2)
    if col1.button(tr(lang, "返回结果页", "Back to Result"), use_container_width=True):
        st.session_state["stage"] = "result"
        st.rerun()
    if col2.button(tr(lang, "查看看板", "View Dashboard"), use_container_width=True):
        st.session_state["stage"] = "dashboard"
        st.rerun()


def render_dashboard(sample_cases, rules_data, lang: str):
    st.title(tr(lang, "后台规则与评估看板", "Rules and Evaluation Dashboard"))
    st.caption(
        tr(
            lang,
            "这一页用于支撑量化收益、技术可信度与商业价值叙事。",
            "This page supports the quantified benefits, technical credibility, and business value story.",
        )
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(tr(lang, "人工采集时间", "Manual Intake Time"), "8 min")
    col2.metric(tr(lang, "原型采集时间", "Prototype Intake Time"), "3 min", "-62.5%")
    col3.metric(tr(lang, "信息完整率", "Completeness"), "90%", "+50%")
    col4.metric(tr(lang, "日处理能力", "Daily Capacity"), "90", "+80%")

    st.markdown(f"### {tr(lang, '示例案例一致性', 'Sample Case Consistency')}")
    case_rows = []
    for sample in sample_cases:
        patient = deepcopy(sample["patient"])
        patient["chief_complaint"] = localized_value(patient["chief_complaint"], lang)
        patient["duration"] = localized_value(patient["duration"], lang)
        patient["history"] = localized_value(patient["history"], lang)
        patient["medications"] = localized_value(patient["medications"], lang)
        patient["allergies"] = localized_value(patient["allergies"], lang)
        result = evaluate_case(patient, sample.get("follow_up_answers", {}), lang)
        case_rows.append(
            {
                tr(lang, "案例", "Case"): localized_value(sample["name"], lang),
                tr(lang, "预期风险", "Expected Risk"): risk_label(sample["expected_risk_level"], lang),
                tr(lang, "系统输出", "System Output"): risk_label(result["risk_level"], lang),
                tr(lang, "是否一致", "Match"): tr(lang, "是", "Yes") if result["risk_level"] == sample["expected_risk_level"] else tr(lang, "否", "No"),
            }
        )
    st.table(case_rows)

    st.markdown(f"### {tr(lang, '红旗规则表', 'Red-Flag Rules')}")
    rule_rows = [
        {
            tr(lang, "类别", "Category"): localized_value(rule["category"], lang),
            tr(lang, "规则", "Rule"): localized_value(rule["label"], lang),
            tr(lang, "动作", "Action"): localized_value(rule["action"], lang),
        }
        for rule in rules_data.get("general_rules", [])
    ]
    st.table(rule_rows)

    assessments = st.session_state.get("completed_assessments", [])
    st.markdown(f"### {tr(lang, '当前会话已完成的案例', 'Completed Cases in This Session')}")
    if assessments:
        risk_counts = Counter(item["result"]["risk_level"] for item in assessments)
        st.write({risk_label(key, lang): value for key, value in risk_counts.items()})
        session_rows = [
            {
                tr(lang, "主诉", "Chief Complaint"): item["patient"]["chief_complaint"],
                tr(lang, "风险等级", "Risk Level"): risk_label(item["result"]["risk_level"], lang),
                tr(lang, "建议科室", "Department"): department_label(item["result"]["department"], lang),
            }
            for item in assessments
        ]
        st.table(session_rows)
    else:
        st.info(tr(lang, "当前会话还没有完成案例。", "No completed cases in this session yet."))

    st.markdown(f"### {tr(lang, '后续扩展', 'Future Extensions')}")
    st.write(
        "\n".join(
            [
                f"- {tr(lang, '连接数据库与真实身份认证', 'Connect database and production authentication')}",
                f"- {tr(lang, '加入更多症状类别和专科规则', 'Add more symptom categories and specialty rules')}",
                f"- {tr(lang, '引入临床专家审核规则库', 'Introduce clinician-reviewed rule library')}",
                f"- {tr(lang, '在合规前提下进行小规模试点', 'Run small pilot testing under compliance requirements')}",
            ]
        )
    )

    if st.button(tr(lang, "返回首页", "Back Home"), use_container_width=True):
        st.session_state["stage"] = "home"
        st.rerun()


def main():
    st.set_page_config(page_title="MedGuide AI", page_icon="🩺", layout="wide")
    apply_theme_css()
    init_state()

    sample_cases = load_json(SAMPLE_CASES_PATH, [])
    rules_data = load_json(RULES_PATH, {"general_rules": []})
    lang = st.session_state["language"]

    if not st.session_state.get("authenticated"):
        render_login(lang)
        return

    render_sidebar(sample_cases, rules_data, lang)
    lang = st.session_state["language"]
    stage = st.session_state["stage"]

    if stage == "home":
        render_home(sample_cases, lang)
    elif stage == "intake":
        render_intake(lang)
    elif stage == "followup":
        render_followup(lang)
    elif stage == "result":
        render_result(lang)
    elif stage == "review":
        render_review(lang)
    elif stage == "dashboard":
        render_dashboard(sample_cases, rules_data, lang)
    else:
        st.session_state["stage"] = "home"
        st.rerun()


if __name__ == "__main__":
    main()
