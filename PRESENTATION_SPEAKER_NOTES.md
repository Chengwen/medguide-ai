# MedGuide AI English-First Bilingual Speaker Notes

Team members: Yiyi Shen, Qianfeng Song, Chengwen Sui, Yingchen Wang, and Luliang Zhao  
Presentation date: April 26, 2026  
Live demo: https://medguide-ai-demo.streamlit.app/

## Slide 1. Title / 标题页

English: Hello everyone. Our group project is MedGuide AI, an AI pre-consultation and risk triage assistant. It is not an AI doctor. It helps users organize symptoms before consultation, complete initial risk screening, and support human review.

中文：大家好，我们的小组项目是 MedGuide AI，医疗智能预问诊与风险分诊助手。它不是 AI 医生，而是一个帮助用户在就诊前整理症状、完成风险初筛并支持人工复核的工具。

## Slide 2. Problem / 问题背景

English: In the pre-consultation workflow, patients often provide incomplete symptom descriptions. Front-desk and triage staff need to ask repeated questions. Manual screening depends on experience, and missed red flags may create safety risks.

中文：门诊前流程中，患者主诉经常不完整，前台和导诊人员需要重复追问。人工初筛依赖经验，不同人员判断可能不一致。如果高风险症状被遗漏，还可能带来安全风险。

## Slide 3. Scope / 项目边界

English: We are not building an automatic diagnosis system. We focus on pre-consultation intake, dynamic follow-up, risk-level suggestions, red-flag reminders, and human review support. We do not provide diagnosis, treatment, medication advice, or replace clinicians.

中文：我们明确不做自动诊断。我们做的是预问诊、动态追问、风险等级提示、红旗症状提醒和人工复核支持。我们不提供诊断、治疗方案或用药建议，也不替代医生。

## Slide 4. Solution / 解决方案

English: Our solution is "rule-first safety + AI-style interaction + human oversight." After login, users complete basic intake, the system detects symptom categories and asks follow-up questions, then rule-based logic produces a risk level, with human review available.

中文：我们的方案是“规则优先 + AI 式交互 + 人工兜底”。用户登录后填写基础信息，系统识别症状类别并进行动态追问，然后通过规则判断风险等级，最后可以交由人工复核。

## Slide 5. Prototype / 原型页面

English: The current prototype includes login, intake, dynamic follow-up, triage result, AI Smart Summary, human review, and evaluation dashboard. It supports a bilingual Chinese-English interface, which makes the demo easier for mixed-language audiences.

中文：当前原型已经实现登录、基础信息采集、动态追问、分诊结果、AI 智能摘要、人工复核和评估看板。系统支持中英文双语界面，方便在展示中切换语言。

## Slide 6. Architecture / 技术架构

English: Technically, we use Python and Streamlit. Local JSON files store rules and sample cases. The AI summary module can connect to OpenRouter using the model `minimax/minimax-m2.5:free`; if no API key is configured, the system automatically uses a local fallback summary.

中文：技术上我们使用 Python 和 Streamlit。数据层使用本地 JSON 存储规则和样例病例。AI 摘要模块可以通过 OpenRouter 接入 `minimax/minimax-m2.5:free` 模型；如果没有 API key，系统会自动使用本地兜底摘要。

## Slide 7. Demo / 演示流程

English: The live demo should be kept within two to three minutes. We can sign in with the demo account, load a high-risk sample case, complete follow-up questions, show the triage result and AI summary, then open human review or the dashboard.

Live demo link: https://medguide-ai-demo.streamlit.app/

中文：现场 Demo 建议控制在两到三分钟。我们可以使用 demo 账号登录，载入高风险示例病例，完成追问后展示分诊结果和 AI 摘要，最后进入人工复核或看板。

## Slide 8. AI Usage / AI 用法

English: AI is used in two layers. The first layer is an AI-style workflow: symptom category detection, dynamic follow-up, rule-based triage, and structured output. The second layer is optional LLM integration: with an OpenRouter API key, the system uses `minimax/minimax-m2.5:free` to generate a triage-facing smart summary.

中文：项目中的 AI 分为两层。第一层是 AI 式流程，包括症状类别识别、动态追问、规则风险分诊和结构化输出。第二层是可选大模型：配置 OpenRouter API key 后，系统可以使用 `minimax/minimax-m2.5:free` 生成导诊人员使用的智能摘要。

## Slide 9. Safety / 安全设计

English: In healthcare, safety comes first. We use a rule-first mechanism so red flags such as chest pain with breathing difficulty, blood in stool, or fast-spreading rash with fever trigger priority warnings. The result page also shows reasoning, disclaimer, and human review support.

中文：医疗场景中安全优先。我们使用规则优先机制，让胸痛加呼吸困难、便血、皮疹快速扩散伴发热等红旗症状优先触发风险提示。同时结果页还会显示判断依据、免责声明和人工复核支持。

## Slide 10. Benefits / 量化收益

English: These numbers are simulated course evaluation assumptions, not real hospital data. They show our quantifiable logic: intake time decreases from 8 minutes to 3 minutes, structured completeness improves from 60% to 90%, and daily capacity increases from 50 to 90 cases.

中文：这些数值是课程模拟评估假设，不是真实医院数据。它们体现的是量化思路：平均采集时间从 8 分钟降到 3 分钟，结构化完整率从 60% 提升到 90%，日处理能力从 50 个提升到 90 个。

## Slide 11. Strategy / 商业战略

English: Target customers include clinics, outpatient departments, online healthcare platforms, corporate health management services, and community healthcare centers. The business model can be B2B SaaS subscription or API integration. It is more flexible than fixed questionnaires and safer than pure LLM systems.

中文：目标客户包括诊所、门诊部门、互联网医疗平台、企业健康管理服务和社区医疗中心。商业模式可以是 B2B SaaS 订阅，也可以通过 API 接入。它比固定问卷更灵活，比纯大模型系统更安全可控。

## Slide 12. Reflection and Q&A / 反思与答疑

English: The current project uses simulated cases, has limited symptom coverage, and has not been clinically validated. Future work includes expanding specialty rules, adding database and access control, improving LLM-based summaries, and running clinician-reviewed pilot studies. Our conclusion is that the realistic value of AI in healthcare is not replacing doctors, but improving intake efficiency, risk visibility, and human decision support.

中文：当前项目使用模拟病例，覆盖症状有限，也没有真实临床验证。未来需要扩展专科规则、加入数据库和权限控制、增强基于大模型的摘要能力，并开展临床人员参与的小规模试点。我们的结论是：AI 在医疗中最现实的价值不是替代医生，而是提升预问诊效率、风险可见性和人工决策支持。

## Q&A Quick Answers / 答辩速答

### Why not automatic diagnosis? / 为什么不做自动诊断？

English: Medical diagnosis has high safety and legal risk. Pre-consultation and triage support are safer and more appropriate for a course prototype.

中文：医学诊断风险高、责任边界复杂。预问诊和分诊支持更安全，也更适合课程原型。

### Does login need a database? / 登录需要数据库吗？

English: Not for this prototype. Demo accounts are enough to show the user entry and access boundary. Real deployment would need a database, authentication, encryption, and audit logs.

中文：课程原型不需要。当前用演示账号展示入口和权限边界。真实部署时才需要数据库、身份认证、加密和审计日志。

### What if there is no OpenRouter API key? / 没有 OpenRouter API key 怎么办？

English: The system still works. It automatically uses a local fallback summary to keep the classroom demo stable.

中文：系统仍然可以运行，会自动使用本地兜底摘要，保证课堂展示稳定。

### Are the benefit numbers real hospital data? / 量化收益是真实医院数据吗？

English: No. They are simulated course evaluation assumptions used to demonstrate efficiency improvement and business-value thinking.

中文：不是。这些是课程模拟评估假设，用来展示效率提升和商业价值的量化思路。

### What can this project do next? / 这个项目未来还可以做什么？

English: The next step is to turn the prototype into a more deployable triage-support platform. That means expanding specialty coverage, adding secure accounts and database storage, improving LLM-based symptom understanding and summaries, and testing the workflow with clinicians in a controlled pilot.

中文：下一步可以把这个原型升级为更可部署的分诊支持平台，包括扩展更多专科场景、加入安全账号与数据库、增强基于大模型的症状理解和摘要能力，并在可控试点中与临床人员一起验证流程效果。
