import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

st.set_page_config(
    page_title="금융 커리어 핏 | 금융권 직무 추천",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Theme ----------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
  .stApp { background: #f6f8fc; }
  section[data-testid="stSidebar"] { background: #101b33; }
  section[data-testid="stSidebar"] * { color: #f3f6fc !important; }
  /* Keep profile text-entry controls white with clearly readable dark text. */
  section[data-testid="stSidebar"] input,
  section[data-testid="stSidebar"] textarea,
  section[data-testid="stSidebar"] div[data-baseweb="input"] input {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    background-color: #ffffff !important;
  }
  section[data-testid="stSidebar"] input::placeholder,
  section[data-testid="stSidebar"] textarea::placeholder {
    color: #667085 !important;
    -webkit-text-fill-color: #667085 !important;
    opacity: 1;
  }
  .hero { padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(125deg,#101b33 0%,#1e3a63 66%,#287c8e 100%); color: white; margin-bottom: 1.2rem; }
  .hero h1 { font-size: 2.05rem; font-weight: 800; margin: 0 0 .4rem 0; color: white; }
  .hero p { margin: .2rem 0; color: #e8eef8; font-size: 1rem; }
  .subtle { color: #61708a; font-size: .9rem; }
  .result-card { padding: 1.1rem 1.2rem; border: 1px solid #e1e7f0; border-radius: 14px; background: white; }
  .rank { color: #287c8e; font-weight: 800; letter-spacing: .04em; font-size: .84rem; }
  .small-pill { display: inline-block; padding: .18rem .52rem; border-radius: 999px; background: #edf5f7; color: #205c68; font-size: .82rem; margin: .15rem .18rem .15rem 0; }
  div[data-testid="stMetric"] { background: #fff; border: 1px solid #e1e7f0; padding: 1rem; border-radius: 12px; }
  .footer-note { font-size: .82rem; color: #667085; }
</style>
""", unsafe_allow_html=True)

LIKERT = ["전혀 아니다", "아닌 편이다", "보통이다", "그런 편이다", "매우 그렇다"]
LIKERT_VALUE = {label: i + 1 for i, label in enumerate(LIKERT)}

TRAIT_LABELS = {
    "communication": "의사소통",
    "sales": "설득·영업",
    "analytical": "수리·분석",
    "markets": "시장·기업 탐구",
    "detail": "꼼꼼함·정확성",
    "risk": "위험 판단",
    "global": "글로벌·외국어",
    "digital": "디지털·데이터",
    "teamwork": "협업",
    "relationship": "장기 관계 형성",
    "problem": "문제 해결",
    "public": "공공성·제도 관심",
    "resilience": "압박 대응",
    "planning": "계획·실행",
    "service": "고객 관점·공감",
}

# The 15 answers are summarized into six readable profile dimensions.
# This summary is for the profile visualization; all existing role details and
# per-trait recommendation logic are intentionally preserved.
TRAIT_GROUPS = {
    "의사소통·고객공감": ["communication", "service"],
    "설득·관계형성": ["sales", "relationship"],
    "분석·디지털 문제해결": ["analytical", "digital", "problem"],
    "시장·글로벌 탐구": ["markets", "global"],
    "정확성·위험관리": ["detail", "risk", "public"],
    "실행·협업·압박대응": ["teamwork", "planning", "resilience"],
}

QUESTIONS = [
    ("communication", "처음 만난 사람의 이야기를 듣고 핵심을 파악해 설명하는 편이다.", "고객·동료와 대화하고 복잡한 내용을 쉽게 전달하는 상황"),
    ("sales", "상대의 필요를 파악해 특정 상품이나 아이디어를 설득력 있게 제안하는 일이 재미있다.", "영업, 협상, 제안서 발표 등 설득이 중요한 상황"),
    ("analytical", "숫자와 표를 비교해 패턴을 찾고 근거에 따라 결론을 내리는 일을 좋아한다.", "재무제표·실적·수치 데이터를 분석하는 상황"),
    ("markets", "기업 실적, 금리, 환율, 주식시장 등 금융시장 변화의 이유가 궁금하다.", "경제 뉴스와 시장 움직임을 지속적으로 살펴보는 상황"),
    ("detail", "작은 오류도 찾아내고 규정이나 절차를 정확히 지키는 편이다.", "계약·정산·서류·내부통제의 정확성이 중요한 상황"),
    ("risk", "결정을 내리기 전에 손실 가능성과 여러 시나리오를 꼼꼼히 검토한다.", "대출 심사, 리스크 관리, 보험 인수 등 판단이 중요한 상황"),
    ("global", "영어 등 외국어로 소통하거나 해외 문화·국제 비즈니스를 접하는 것이 좋다.", "외국계 금융사, 외환, 무역금융, 해외 고객 업무"),
    ("digital", "엑셀·SQL·코딩·데이터 시각화 같은 도구로 문제를 개선하는 데 흥미가 있다.", "금융 데이터 분석, 디지털 상품, 자동화 프로젝트"),
    ("teamwork", "역할이 다른 사람들과 목표를 맞추고 공동 결과물을 만드는 데 강점이 있다.", "부서 간 협업, 딜 수행, 프로젝트 업무"),
    ("relationship", "한 번 맺은 관계를 오래 유지하며 신뢰를 쌓는 것에 보람을 느낀다.", "기업 고객 관리, 자산관리, 장기 고객 관계"),
    ("problem", "정답이 정해지지 않은 문제도 여러 방법을 시험하면서 해결하는 편이다.", "신규 사업, 상품 기획, 조사·분석 과제"),
    ("public", "금융소비자 보호, 금융시장 안정, 정책과 제도가 사회에 미치는 영향에 관심이 많다.", "금융공공기관, 감독·정책·제도 연구 업무"),
    ("resilience", "마감이 촉박하거나 변수가 생겨도 우선순위를 정해 침착하게 대응한다.", "시장 변동, 빠른 의사결정, 촉박한 업무 일정"),
    ("planning", "목표를 세분화하고 일정과 진행 상황을 관리해 끝까지 완수하는 편이다.", "딜 관리, 프로젝트 운영, 시험·채용 준비"),
    ("service", "사람의 불편과 필요를 먼저 살펴 실질적으로 도움이 되는 해결책을 찾고 싶다.", "개인금융, 고객지원, 금융소비자 보호 업무"),
]

# A role score is a weighted average of the user's self-ratings on relevant work preferences.
# It is an exploratory matching score, not a validated psychometric or hiring predictor.
ROLES = [
    {
        "id": "personal_bank", "sector": "은행", "title": "개인금융·자산관리(PB/WM)",
        "summary": "개인 고객의 예금·대출·투자·자산관리 니즈를 파악하고 장기적인 금융 솔루션을 제안합니다.",
        "weights": {"communication":1.2,"sales":1.1,"detail":0.6,"relationship":1.3,"service":1.4,"planning":0.7,"risk":0.5,"teamwork":0.5},
        "tasks": ["고객 재무 목표와 상황 파악", "예금·대출·투자상품 상담 및 사후관리", "금융소비자 보호 및 적합성 원칙 준수"],
        "certs": ["AFPK: 개인 재무설계의 기초 학습에 활용", "투자자산운용사: 투자상품·운용 지식 보강", "은행FP: 은행 자산관리 업무 이해 보강", "컴퓨터활용능력/엑셀: 상담 자료와 실적 관리"],
        "prep": "고객 상담 경험과 신뢰 형성 사례를 STAR 방식으로 정리하고, 예금·대출·투자상품을 고객의 상황에 맞춰 설명하는 연습을 하세요.",
        "companies": [("KB국민은행", "개인·기업 고객 대상 종합 은행 서비스와 자산관리", "https://jobs.kbstar.com/"), ("IBK기업은행", "중소기업 금융을 중심으로 개인금융도 제공하는 은행", "https://ibk.incruit.com/apply/index.asp"), ("신한은행", "개인·기업·글로벌 금융 서비스를 제공하는 시중은행", "https://shinhan.recruiter.co.kr/")],
    },
    {
        "id": "corporate_bank", "sector": "은행", "title": "기업금융·기업 RM", 
        "summary": "기업의 자금 수요와 사업 구조를 이해하고 대출·현금관리·외환 등 금융 솔루션을 제안합니다.",
        "weights": {"communication":1.0,"sales":0.8,"analytical":1.3,"markets":0.8,"risk":1.2,"teamwork":0.9,"relationship":1.3,"problem":0.7,"planning":1.0},
        "tasks": ["기업의 사업모델·재무상태·현금흐름 파악", "대출·운전자금·무역금융 등 솔루션 제안", "심사부서·상품부서와 협업하고 고객 관계 관리"],
        "certs": ["신용분석사: 재무제표·신용분석 기초", "외환전문역: 외환·무역금융 관심 직무에 도움", "투자자산운용사: 금융상품 이해 확장", "엑셀·재무모델링: 현금흐름과 재무비율 분석"],
        "prep": "관심 산업 하나를 정해 기업 2곳의 사업보고서와 재무제표를 비교하고, ‘왜 이 기업에 어떤 금융이 필요한가’를 1페이지로 작성하세요.",
        "companies": [("IBK기업은행", "중소기업 금융에 강점을 가진 국책 특수은행", "https://ibk.incruit.com/apply/index.asp"), ("KB국민은행", "기업대출·자금관리·글로벌 서비스를 제공하는 시중은행", "https://jobs.kbstar.com/"), ("Standard Chartered Korea", "국경 간 거래와 기업·기관 고객을 지원하는 글로벌 은행", "https://jobs.standardchartered.com/?locale=ko_KR")],
    },
    {
        "id": "credit", "sector": "은행·캐피탈", "title": "여신심사·신용분석", 
        "summary": "대출 신청자나 기업의 상환능력, 담보, 현금흐름과 산업 위험을 분석해 신용 의사결정을 지원합니다.",
        "weights": {"analytical":1.5,"markets":0.8,"detail":1.2,"risk":1.5,"problem":0.8,"planning":0.9,"public":0.2},
        "tasks": ["재무제표·신용정보·현금흐름 분석", "상환 위험과 담보·보증 구조 검토", "여신한도와 사후관리 기준 검토"],
        "certs": ["신용분석사: 가장 직접적으로 연결되는 기초 자격 예시", "재경관리사: 회계·세무·재무 기반", "SQLD: 데이터 조회·분석 보강", "엑셀·재무모델링: 현금흐름 및 민감도 분석"],
        "prep": "상장기업 한 곳의 재무제표에서 부채비율·이자보상배율·영업현금흐름을 계산하고, 신용위험 요인을 5개 정리해 보세요.",
        "companies": [("IBK기업은행", "중소기업 여신과 기업 분석 경험을 쌓을 수 있는 은행", "https://ibk.incruit.com/apply/index.asp"), ("KB국민은행", "가계·기업 대출 및 리스크 관리 기능을 운영하는 은행", "https://jobs.kbstar.com/"), ("현대캐피탈", "자동차금융과 기업·소비자 금융을 제공하는 여신전문금융회사", "https://www.hyundaicapital.com/")],
    },
    {
        "id": "global_fx", "sector": "은행·외국계", "title": "외환·글로벌뱅킹·무역금융", 
        "summary": "환율·국제거래에 대한 이해를 바탕으로 외환, 수출입 결제, 무역금융 및 글로벌 고객 업무를 지원합니다.",
        "weights": {"communication":0.7,"analytical":1.0,"markets":1.2,"risk":0.8,"global":1.6,"teamwork":0.7,"relationship":0.7,"resilience":0.8,"planning":0.7},
        "tasks": ["환전·송금·수출입 결제 및 무역서류 업무", "환율과 국가별 시장 동향 파악", "해외 지점·고객·내부 부서와 협업"],
        "certs": ["외환전문역 I·II종: 외환 업무 지식", "국제무역사: 무역 실무 이해", "무역영어: 무역 서류·영문 표현 학습", "영어 인터뷰·비즈니스 이메일 포트폴리오"],
        "prep": "관심 통화의 환율을 주 1회 기록하고 변화 원인을 요약하세요. 수출입 거래의 결제 흐름과 신용장 기본 개념도 함께 익히세요.",
        "companies": [("Standard Chartered Korea", "글로벌 네트워크 기반의 기업금융·시장·무역금융 업무", "https://jobs.standardchartered.com/?locale=ko_KR"), ("KB국민은행", "외환·글로벌 기업금융 서비스를 운영하는 은행", "https://jobs.kbstar.com/"), ("한국산업은행", "산업·기업 금융과 정책금융을 수행하는 정책금융기관", "https://www.kdb.co.kr/")],
    },
    {
        "id": "foreign_cib", "sector": "외국계 은행", "title": "외국계 은행 CIB·기업고객 커버리지", 
        "summary": "국내외 기업·금융기관 고객 관계를 관리하고 대출, 자금시장, 무역금융 등 여러 상품을 연결합니다.",
        "weights": {"communication":1.2,"analytical":1.0,"markets":0.9,"global":1.5,"teamwork":1.1,"relationship":1.0,"resilience":0.8,"planning":0.8,"sales":0.6},
        "tasks": ["기업·금융기관 고객의 사업과 금융 수요 파악", "글로벌 상품 전문가와 고객 제안 조율", "영문 자료 작성 및 다국적 팀 협업"],
        "certs": ["영어 말하기·비즈니스 작문: 실제 업무 샘플을 만들어 연습", "신용분석사: 기업 재무 이해 보강", "투자자산운용사: 금융시장 상품 기초", "엑셀·파워포인트: 분석과 고객 제안 자료 작성"],
        "prep": "영문 이력서와 90초 자기소개를 준비하고, 기업 한 곳을 골라 ‘회사 개요-금융 니즈-제안 가능한 솔루션’을 영어로 설명해 보세요.",
        "companies": [("Standard Chartered Korea", "아시아·아프리카·유럽 등 글로벌 네트워크를 보유한 은행", "https://jobs.standardchartered.com/?locale=ko_KR"), ("HSBC", "국제 무역·기업금융·자산관리 등 글로벌 금융을 제공", "https://www.hsbc.com/careers"), ("Citi", "기관·기업 고객과 글로벌 시장을 연결하는 국제 금융그룹", "https://jobs.citi.com/")],
    },
    {
        "id": "research", "sector": "증권사", "title": "리서치·기업분석 애널리스트", 
        "summary": "기업과 산업 자료를 분석해 실적 전망, 가치평가, 투자 판단에 필요한 리서치를 제공합니다.",
        "weights": {"analytical":1.5,"markets":1.5,"detail":1.2,"risk":0.7,"digital":0.7,"problem":0.8,"planning":0.8,"communication":0.5},
        "tasks": ["산업·기업 실적 및 공시 분석", "실적 추정과 밸류에이션 모델 작성", "리서치 보고서 작성 및 핵심 의견 전달"],
        "certs": ["금융투자분석사: 리서치 직무와 밀접한 학습 예시", "투자자산운용사: 금융투자상품 기초", "CFA: 장기적 전문성 개발 선택지(필수 아님)", "회계·엑셀·파이썬: 재무모델과 데이터 분석"],
        "prep": "기업 1곳을 정해 최근 실적발표와 사업보고서를 읽고, 핵심 투자 포인트·위험·가치평가 가정을 2페이지 리포트로 작성하세요.",
        "companies": [("삼성증권", "주식·채권 중개, 자산관리, 기업금융 및 리서치 사업 운영", "https://www.samsungsecurities.co.kr/kor/recruit/new_employee.do"), ("한국투자증권", "브로커리지·자산관리·투자은행 등 종합 증권 서비스", "https://www.truefriend.com/"), ("미래에셋증권", "글로벌 투자·자산관리·기업금융 사업을 전개하는 증권사", "https://securities.miraeasset.com/")],
    },
    {
        "id": "ib", "sector": "증권사", "title": "투자은행(IB)·자본시장", 
        "summary": "기업의 자금조달, 회사채·주식 발행, 인수합병 및 거래 구조화 과정을 지원합니다.",
        "weights": {"analytical":1.2,"markets":1.2,"detail":0.8,"risk":0.8,"global":0.6,"teamwork":1.1,"relationship":0.7,"problem":1.0,"resilience":1.3,"planning":1.3,"communication":0.7},
        "tasks": ["기업 자금조달·거래 구조 분석", "밸류에이션·제안서·실사 자료 작성", "고객 및 법무·회계·내부 팀과 거래 일정 관리"],
        "certs": ["투자자산운용사: 금융투자상품 이해", "재경관리사: 회계·재무 기초", "CFA: 기업가치·재무 분석의 장기 학습 선택지", "엑셀·파워포인트·재무모델링 실습"],
        "prep": "거래 사례 하나를 선정해 거래 배경, 기업가치, 자금조달 방식, 리스크를 요약하세요. 재무모델이나 피치북 형태의 결과물을 포트폴리오로 만드세요.",
        "companies": [("삼성증권", "기업금융과 자본시장 서비스를 제공하는 종합 증권사", "https://www.samsungsecurities.co.kr/kor/recruit/new_employee.do"), ("미래에셋증권", "국내외 자본시장·투자은행 업무를 수행하는 증권사", "https://securities.miraeasset.com/"), ("한국투자증권", "기업금융·발행시장·투자 서비스 등을 제공", "https://www.truefriend.com/")],
    },
    {
        "id": "card_product", "sector": "카드사", "title": "카드 상품기획·마케팅 데이터 분석", 
        "summary": "결제 데이터와 고객 니즈를 분석해 카드 상품, 혜택, 캠페인 및 고객 경험을 개선합니다.",
        "weights": {"communication":0.6,"sales":0.7,"analytical":1.1,"markets":0.6,"detail":0.7,"digital":1.5,"teamwork":1.0,"relationship":0.5,"problem":1.2,"planning":1.0,"service":0.8},
        "tasks": ["고객·가맹점·결제 데이터 분석", "카드 상품·혜택·캠페인 기획", "성과지표 정의와 실험·결과 평가"],
        "certs": ["SQLD: 데이터 조회·모델 이해", "ADsP: 데이터 분석 기초", "GA4 또는 디지털 마케팅 교육: 캠페인 측정 이해", "엑셀·파이썬·시각화: 분석 포트폴리오"],
        "prep": "공개 데이터를 이용해 고객 세그먼트나 소비 패턴을 분석하고, 문제-인사이트-제안-성과지표를 담은 3~5장 포트폴리오를 만드세요.",
        "companies": [("현대카드", "카드 상품·결제 서비스와 데이터 기반 마케팅을 전개", "https://www.hyundaicard.com/"), ("KB국민카드", "신용·체크카드, 결제 및 데이터 기반 서비스를 제공", "https://card.kbcard.com/"), ("신한카드", "카드 결제와 금융·데이터 서비스를 운영", "https://www.shinhancard.com/")],
    },
    {
        "id": "insurance_risk", "sector": "보험사", "title": "보험 인수심사·리스크 관리", 
        "summary": "보험계약의 위험을 평가하고 인수 조건·보험료·손실 가능성을 검토합니다.",
        "weights": {"analytical":1.2,"detail":1.3,"risk":1.5,"digital":0.5,"problem":0.7,"planning":0.8,"public":0.3},
        "tasks": ["가입 대상과 위험 요인 평가", "보험 약관·인수 기준 적용", "손해율·리스크 지표 모니터링"],
        "certs": ["보험심사역: 보험 인수·리스크 관련 학습 예시", "보험계리사: 계리·수리 분야를 목표로 할 때 도전", "SQLD/ADsP: 손해율·계약 데이터 분석", "통계·확률·회계 기초 복습"],
        "prep": "보험상품 하나를 골라 보장 범위, 주요 위험, 손해율에 영향을 줄 요소를 요약하고 기본 통계·엑셀 분석을 연습하세요.",
        "companies": [("삼성생명", "생명보험과 자산관리 서비스를 제공하는 보험사", "https://www.samsunglife.com/"), ("삼성화재", "자동차·장기·일반보험 및 리스크 관리 서비스를 제공", "https://www.samsungfire.com/"), ("KB손해보험", "손해보험 상품과 보상 서비스를 제공", "https://www.kbinsure.co.kr/")],
    },
    {
        "id": "insurance_sales", "sector": "보험사", "title": "보험 컨설팅·재무설계", 
        "summary": "고객의 생애주기와 위험 보장 수요를 파악해 보험·재무 솔루션을 설명하고 관리합니다.",
        "weights": {"communication":1.2,"sales":1.1,"detail":0.6,"relationship":1.1,"service":1.3,"planning":0.8,"risk":0.5,"resilience":0.6},
        "tasks": ["고객의 보장 니즈·재무목표 파악", "상품 구조와 보장 범위 설명", "계약 유지·보험금 청구 등 사후관리 지원"],
        "certs": ["AFPK: 재무설계의 기초", "생명·손해보험 모집 관련 자격: 실제 판매 직무의 등록 요건 확인", "변액보험 관련 자격: 취급 상품·회사 기준에 따라 확인", "상담·설명·고객 보호 사례 정리"],
        "prep": "판매 실적뿐 아니라 고객에게 적합한 선택지를 비교해 설명한 경험, 민원이나 이해 충돌을 원칙에 따라 해결한 경험을 정리하세요.",
        "companies": [("삼성생명", "생명보험·연금·자산관리 서비스를 제공", "https://www.samsunglife.com/"), ("KB손해보험", "생활 위험에 대비하는 다양한 손해보험 서비스", "https://www.kbinsure.co.kr/"), ("메리츠화재", "손해보험 및 보상 서비스를 운영", "https://www.meritzfire.com/")],
    },
    {
        "id": "capital", "sector": "캐피탈", "title": "캐피탈 기업금융·리스·여신", 
        "summary": "자동차·설비 리스, 할부, 기업대출 등의 금융 구조를 설계하고 거래의 신용위험을 평가합니다.",
        "weights": {"communication":0.7,"sales":0.6,"analytical":1.1,"detail":0.8,"risk":1.2,"teamwork":0.8,"relationship":0.7,"problem":0.7,"planning":0.9},
        "tasks": ["리스·할부·기업금융 상품 검토", "고객·자산·상환능력 평가", "계약 조건 협의와 사후 리스크 관리"],
        "certs": ["신용분석사: 신용평가 기초", "재경관리사: 회계·재무 기반", "투자자산운용사: 금융시장 이해 확장", "엑셀·현금흐름 분석 실습"],
        "prep": "캐피탈사의 주요 상품을 비교하고, 자동차금융 또는 설비금융 사례를 골라 고객·담보·상환재원·위험을 정리하세요.",
        "companies": [("현대캐피탈", "자동차금융·리스·할부 등 소비자 및 기업 금융 제공", "https://www.hyundaicapital.com/"), ("IBK캐피탈", "기업금융·리스·할부·투자금융 등을 수행", "https://www.ibkc.co.kr/"), ("롯데캐피탈", "개인·기업 대출과 리스 등 여신금융 서비스 제공", "https://www.lottecap.com/")],
    },
    {
        "id": "asset_trust", "sector": "자산운용·신탁", "title": "자산운용·신탁·수탁 업무", 
        "summary": "펀드·신탁재산의 운용 지원, 자산·계약 관리, 수탁·사무관리와 관련된 통제 업무를 수행합니다.",
        "weights": {"analytical":1.0,"markets":1.1,"detail":1.4,"risk":1.0,"teamwork":0.6,"relationship":0.6,"planning":1.0,"public":0.3},
        "tasks": ["펀드·신탁 관련 데이터와 계약 관리", "운용·수탁·결제·보고 프로세스 지원", "규정 준수와 오류 예방"],
        "certs": ["투자자산운용사: 자산운용 직무 기초", "펀드투자권유자문인력 등: 담당 업무와 회사 요건 확인", "SQLD/엑셀: 데이터·정산 처리", "회계·금융상품·자본시장법 기초"],
        "prep": "펀드가치 산정, 결제, 권리 처리 등 자산운용·수탁 업무 흐름을 조사하고 정확성·통제·문제 해결 사례를 준비하세요.",
        "companies": [("KB자산운용", "주식·채권·대체투자 등 자산운용 사업을 수행", "https://www.kbam.co.kr/"), ("신한자산운용", "국내외 다양한 자산군의 투자상품을 운용", "https://www.shinhanam.com/"), ("한국예탁결제원", "증권 예탁·결제 등 자본시장 인프라를 담당", "https://www.ksd.or.kr/")],
    },
    {
        "id": "public_finance", "sector": "금융공공기관", "title": "금융공기업 정책·경제·시장 분석", 
        "summary": "금융시장 안정, 산업·중소기업 지원, 금융소비자 보호 등 공공 목적과 관련된 조사·정책·운영 업무입니다.",
        "weights": {"analytical":1.1,"markets":0.8,"detail":0.9,"risk":0.7,"teamwork":0.8,"problem":0.9,"public":1.6,"planning":1.2,"communication":0.4},
        "tasks": ["경제·금융·산업 자료 분석", "정책·사업 성과 및 리스크 검토", "보고서 작성과 유관기관 협업"],
        "certs": ["경제·경영·법·통계 전공지식: 기관별 필기과목 확인", "SQLD/ADsP: 데이터 직무 지원 시 활용", "한국사·컴퓨터 자격: 공고상 우대 여부 확인", "NCS 직업기초능력: 채용 공고와 출제 범위에 맞춰 대비"],
        "prep": "관심 기관의 설립 목적과 최근 연차보고서를 읽고 정책 이슈 1개를 골라 현황·원인·대안·부작용을 1~2페이지로 정리하세요.",
        "companies": [("한국거래소", "증권시장 운영과 공정·투명한 자본시장 인프라를 담당", "https://krx.saramin.co.kr/service/krx/3839/applicant/apply/index.asp"), ("금융감독원", "금융회사 감독과 금융소비자 보호 기능을 수행", "https://www.fss.or.kr/"), ("한국산업은행", "산업 발전과 기업 구조개선 등을 지원하는 정책금융기관", "https://www.kdb.co.kr/")],
    },
    {
        "id": "compliance", "sector": "은행·금융회사", "title": "준법감시·내부통제·AML", 
        "summary": "금융 관련 법규·내부 규정을 점검하고 자금세탁방지, 개인정보 보호, 이해상충 및 내부통제를 지원합니다.",
        "weights": {"analytical":0.7,"detail":1.6,"risk":1.3,"teamwork":0.6,"problem":0.7,"public":0.8,"planning":1.0,"resilience":0.6},
        "tasks": ["내부 규정·법령 변경사항 점검", "거래 모니터링·의심거래 검토 및 보고 지원", "통제 절차·교육·점검 결과 문서화"],
        "certs": ["AML·컴플라이언스 관련 교육: 기관·직무별 인정 범위 확인", "개인정보·정보보호 기초: 데이터 취급 업무에 유용", "신용분석사 또는 금융상품 기초: 금융 거래 이해", "문서 작성·엑셀: 점검 결과와 근거 관리"],
        "prep": "금융소비자보호·개인정보·자금세탁방지 이슈를 하나 골라 관련 규정과 회사가 마련할 통제 절차를 요약해 보세요.",
        "companies": [("Standard Chartered Korea", "국제 규정과 현지 법규를 준수하며 글로벌 금융을 운영", "https://jobs.standardchartered.com/?locale=ko_KR"), ("KB국민은행", "대형 금융기관으로 준법·리스크·내부통제 기능 운영", "https://jobs.kbstar.com/"), ("금융감독원", "금융회사 감독 및 금융소비자 보호를 수행", "https://www.fss.or.kr/")],
    },
    {
        "id": "fintech", "sector": "핀테크·은행 디지털", "title": "금융 데이터·핀테크 서비스 기획", 
        "summary": "데이터와 사용자 관점에서 금융 앱, 결제·대출·자산관리 서비스의 문제를 정의하고 개선합니다.",
        "weights": {"analytical":1.1,"digital":1.6,"teamwork":0.9,"problem":1.4,"planning":0.9,"service":0.8,"communication":0.5,"resilience":0.6},
        "tasks": ["고객 행동·서비스 지표 분석", "요구사항 정의와 서비스 개선 실험", "개발·디자인·리스크 부서와 협업"],
        "certs": ["SQLD: SQL 기반 데이터 활용", "ADsP: 분석 방법론 기초", "빅데이터분석기사: 응시자격을 확인한 뒤 선택", "파이썬·대시보드·서비스 기획 포트폴리오"],
        "prep": "금융 앱 하나를 선정해 사용자 흐름의 불편을 정의하고, 지표(전환율·이탈률 등)와 개선 가설을 포함한 서비스 개선안을 작성하세요.",
        "companies": [("카카오뱅크", "모바일 중심 은행 서비스와 금융 플랫폼을 운영", "https://www.kakaobank.com/Corp/Careers"), ("토스", "송금·결제·대출비교 등 금융 서비스를 제공하는 핀테크 플랫폼", "https://toss.im/career"), ("KB국민은행", "은행 업무의 디지털 전환과 데이터 기반 서비스를 추진", "https://jobs.kbstar.com/")],
    },
    {
        "id": "bank_ops", "sector": "은행", "title": "은행텔러·영업점 운영·금융사무", 
        "summary": "영업점이나 금융 운영 조직에서 거래 처리, 고객 안내, 서류 확인, 정산 및 업무 통제를 수행합니다.",
        "weights": {"communication":0.6,"detail":1.5,"teamwork":0.7,"relationship":0.5,"planning":0.9,"service":1.2,"resilience":0.8,"risk":0.7},
        "tasks": ["예금·송금 등 고객 거래 및 기본 안내", "본인확인·서류·거래 내역의 정확한 처리", "고객 문의와 민원 전달 및 내부 절차 준수"],
        "certs": ["컴퓨터활용능력/엑셀: 사무·정산 역량", "은행FP: 은행 상품과 고객 상담 기초", "금융 관련 기초 교육: 상품·금융소비자보호", "고객 응대·정확성 사례 정리"],
        "prep": "정확한 업무 처리, 고객 응대, 민원 대응 경험을 정리하고 희망 은행의 일반직·지원직·전문직 공고별 고용형태와 자격요건을 구분해 확인하세요.",
        "companies": [("KB국민은행", "개인·기업 금융과 영업점·디지털 채널 운영", "https://jobs.kbstar.com/"), ("IBK기업은행", "중소기업·개인 고객 대상 금융과 영업점 업무 운영", "https://ibk.incruit.com/apply/index.asp"), ("신한은행", "개인·기업 고객 금융 및 영업점 업무 운영", "https://shinhan.recruiter.co.kr/")],
    },
    {
        "id": "card_risk", "sector": "카드사", "title": "카드 신용리스크·이상거래 분석", 
        "summary": "결제·신용 데이터를 바탕으로 연체 위험이나 이상거래를 탐지하고 손실을 줄이는 정책을 지원합니다.",
        "weights": {"analytical":1.3,"detail":1.0,"risk":1.4,"digital":1.2,"problem":1.0,"planning":0.6,"public":0.3},
        "tasks": ["연체·승인·이상거래 데이터 분석", "위험 지표와 탐지 규칙 검토", "모델·정책 성과 및 오탐·미탐 모니터링"],
        "certs": ["SQLD: 데이터 질의 기초", "ADsP: 분석 기초", "통계·파이썬: 분류·이상탐지 실습", "금융소비자보호·개인정보 기초"],
        "prep": "공개된 사기탐지 또는 신용 데이터로 기본 탐색분석을 해보고, 정확도 외에도 오탐·미탐 비용을 함께 설명하는 프로젝트를 만드세요.",
        "companies": [("현대카드", "카드 결제와 데이터 기반 위험·마케팅 서비스를 운영", "https://www.hyundaicard.com/"), ("KB국민카드", "카드 결제·신용 및 고객 데이터 관련 기능을 운영", "https://card.kbcard.com/"), ("신한카드", "결제·신용·데이터 기반 금융 서비스를 제공", "https://www.shinhancard.com/")],
    },
]

HIRING_PROCESS = [
    ("공고·직무 확인", "직무기술서, 지원 자격, 근무지, 고용형태, 접수 마감일을 확인합니다."),
    ("지원서·자기소개서", "직무 요건과 연결되는 경험을 문제-행동-결과로 작성합니다. 블라인드 채용은 학교명 등 금지 정보를 공고대로 처리합니다."),
    ("필기·온라인 평가", "기관에 따라 NCS, 전공시험, 인적성, 수리·언어·상황판단 또는 온라인 역량평가가 포함될 수 있습니다."),
    ("면접·과제", "직무면접, 인성·가치면접, PT·토론·케이스·코딩/분석과제 중 일부가 진행될 수 있습니다."),
    ("검진·서류 확인·최종", "신원·자격·경력 확인과 건강검진 등은 회사와 채용 유형별 안내를 따릅니다."),
]


def score_roles(answer_values):
    """Score each role through the six core dimensions.

    Each core dimension combines the existing detailed response weights. The
    grouped weighted average is algebraically equivalent to the original
    per-trait weighted average, so the UI change does not alter role rankings.
    """
    scores = []
    for role in ROLES:
        weights = role["weights"]
        grouped_axes = []
        for _, keys in TRAIT_GROUPS.items():
            axis_weights = {key: weights[key] for key in keys if key in weights}
            if not axis_weights:
                continue
            axis_weight_sum = sum(axis_weights.values())
            axis_score = sum(answer_values[key] * weight for key, weight in axis_weights.items()) / axis_weight_sum
            grouped_axes.append((axis_score, axis_weight_sum))
        total_axis_weight = sum(weight for _, weight in grouped_axes)
        weighted_avg = sum(score * weight for score, weight in grouped_axes) / total_axis_weight
        # Convert the 1–5 weighted self-rating to a 0–100 display scale.
        score = round((weighted_avg - 1) / 4 * 100)
        scores.append({"role": role, "score": score, "raw": weighted_avg})
    return sorted(scores, key=lambda x: x["score"], reverse=True)


def top_reasons(role, trait_values, limit=3):
    ranked = sorted(role["weights"].items(), key=lambda kv: trait_values[kv[0]] * kv[1], reverse=True)
    return [(TRAIT_LABELS[k], trait_values[k], role["weights"][k]) for k, _ in ranked[:limit]]


def major_guidance(major):
    m = major.strip().lower()
    if any(x in m for x in ["경영", "경제", "회계", "금융", "세무"]):
        return "전공 지식을 금융 직무로 연결하기 좋습니다. 회계·재무제표 분석, 산업 리서치, 기업 분석 결과물을 지원 직무와 연결해 보세요."
    if any(x in m for x in ["통계", "수학", "데이터", "컴퓨터", "소프트웨어", "it", "공학", "산업공학"]):
        return "수리·데이터 기반 강점을 금융 문제에 적용해 보세요. SQL·파이썬으로 결제·신용·시장 데이터를 분석한 프로젝트가 유용합니다."
    if any(x in m for x in ["영어", "중국", "일본", "언어", "국제", "무역", "외교"]):
        return "언어·국제 감각을 글로벌뱅킹, 외환, 무역금융 및 외국계 은행 업무 사례로 구체화해 보세요. 금융시장 기초와 영문 자료 분석을 함께 준비하세요."
    if any(x in m for x in ["법", "행정", "정치", "사회", "정책"]):
        return "규정 해석·정책 이해를 준법감시, 금융소비자 보호, 금융공공기관 정책·조사 업무와 연결해 보세요. 금융 제도와 데이터 기초를 보완하면 좋습니다."
    if any(x in m for x in ["심리", "상담", "교육", "사회복지", "서비스"]):
        return "상담·고객 이해 역량을 개인금융, 자산관리, 금융소비자 보호와 연결해 보세요. 상품 구조와 금융규제에 대한 기본 지식도 함께 쌓으세요."
    return "전공 자체보다 직무와 연결되는 경험·결과물이 중요합니다. 전공 과제나 아르바이트에서 분석, 정확성, 협업, 고객 문제 해결 중 한 가지 사례를 골라 금융 직무 관점으로 재구성하세요."


def timeline(age):
    if age < 20:
        return [
            ("이번 달", "금융 직무 2개를 비교하고 경제·금융 뉴스 요약을 주 1회 작성"),
            ("1~3개월", "엑셀·회계·경제 기초를 학습하고 학교 프로젝트/동아리 경험 확보"),
            ("3~6개월", "관심 분야에 맞는 입문 자격·교육을 탐색하고 금융권 현직자 인터뷰 진행"),
            ("6~12개월", "직무 체험·공모전·봉사·데이터 미니 프로젝트 중 하나를 결과물로 완성"),
        ]
    if age <= 24:
        return [
            ("1~2주", "1·2순위 직무의 최근 채용공고 5개를 비교해 공통 역량과 전형을 표로 정리"),
            ("1~2개월", "직무 핵심 자격·전공 공부를 시작하고 금융 동아리·공모전·케이스 활동 지원"),
            ("2~4개월", "직무별 결과물 1개 완성: 기업분석 보고서, SQL 분석, 금융 이슈 리포트 등"),
            ("4~6개월", "인턴·산학 프로젝트·체험형 청년인턴 및 신입 공채에 지원하며 면접 연습"),
        ]
    if age <= 29:
        return [
            ("1~2주", "직무 적합 경험을 재정리하고 지원 가능한 신입·인턴·계약·경력 공고를 구분"),
            ("1~2개월", "직무 핵심 지식과 필기/영어/데이터 역량 중 가장 큰 약점을 집중 보완"),
            ("2~3개월", "실무형 포트폴리오 또는 케이스 답변을 만들고 이력서·자기소개서를 맞춤화"),
            ("3~6개월", "주간 지원 목표를 설정하고 모의면접·현직자 피드백으로 답변을 개선"),
        ]
    return [
        ("1~2주", "기존 경력에서 금융 직무에 전이 가능한 역량과 업계 이해가 필요한 부분을 구분"),
        ("1~2개월", "경력채용·전문직·디지털/리스크 등 직무 특화 공고를 중심으로 요구 경력과 자격 확인"),
        ("2~3개월", "성과를 수치로 표현한 경력기술서와 금융 직무에 적용 가능한 사례·포트폴리오 정리"),
        ("3~6개월", "직무 적합 네트워킹과 면접을 진행하고, 필요시 자격·교육으로 전문성 보강"),
    ]


def get_role_by_id(role_id):
    return next(r for r in ROLES if r["id"] == role_id)

# ---------- Sidebar profile ----------
with st.sidebar:
    st.markdown("## 💼 나의 프로필")
    nickname = st.text_input("별명", placeholder="예: 금융꿈나무", max_chars=30)
    age = st.number_input("나이", min_value=14, max_value=80, value=23, step=1)
    major = st.text_input("전공 / 학과", placeholder="예: 경영학과, 컴퓨터공학과")
    st.divider()
    st.markdown("### 이용 안내")
    st.caption("15개 문항에 답하면 선호 성향과 업무 특성의 가중치 매칭으로 금융권 직무 1·2순위를 추천합니다.")
    st.caption("나이·전공은 점수에 반영하지 않습니다. 준비 로드맵을 개인화하는 참고 정보로만 사용합니다.")
    st.caption("응답은 별도의 데이터베이스에 저장하지 않습니다. Streamlit 배포 환경 자체의 로그·운영 설정은 별도 확인하세요.")

st.markdown("""
<div class="hero">
  <h1>금융 커리어 핏</h1>
  <p>나의 일하는 방식과 관심사를 바탕으로 금융권에서 어울릴 수 있는 직무를 탐색하세요.</p>
  <p>15개 성향 질문 · 직무 매칭 · 1·2순위 분석 · 준비 로드맵 · 공식 기업 링크</p>
</div>
""", unsafe_allow_html=True)

intro1, intro2, intro3 = st.columns(3)
intro1.metric("질문 수", "15개")
intro2.metric("분석 직무", f"{len(ROLES)}개")
intro3.metric("추천 결과", "1·2순위")
st.info("이 도구는 자기탐색용 참고 도구이며 MBTI 검사나 검증된 심리검사가 아닙니다. 결과는 실제 채용 합격 가능성·직무 성과를 예측하지 않으며, 직무 선택을 확정하기보다 탐색할 방향을 좁히는 데 사용하세요.")

st.markdown("## 1. 성향 질문에 답하기")
st.write("각 문항에서 평소 자신의 모습과 가장 가까운 답을 선택하세요. 정답은 없으며, 이상적인 모습보다 실제 행동에 가깝게 답하는 편이 좋습니다.")

with st.form("assessment_form"):
    responses = {}
    for idx, (trait, question, hint) in enumerate(QUESTIONS, start=1):
        st.markdown(f"**Q{idx}. {question}**")
        st.caption(hint)
        responses[trait] = st.radio(
            label=f"Q{idx} 응답",
            options=LIKERT,
            index=None,
            horizontal=True,
            key=f"q_{idx}",
            label_visibility="collapsed",
        )
        if idx < len(QUESTIONS):
            st.markdown(" ")
    submitted = st.form_submit_button("성향 분석하고 직무 추천받기", type="primary", use_container_width=True)

if submitted:
    missing = [i for i, (trait, _, _) in enumerate(QUESTIONS, start=1) if st.session_state.get(f"q_{i}") is None]
    if missing:
        st.warning(f"아직 답하지 않은 문항이 {len(missing)}개 있습니다. Q{', Q'.join(map(str, missing))}에 응답한 후 다시 제출하세요.")
    else:
        trait_values = {trait: LIKERT_VALUE[responses[trait]] for trait, _, _ in QUESTIONS}
        st.session_state["assessment"] = {
            "traits": trait_values,
            "scores": score_roles(trait_values),
            "nickname": nickname.strip() or "금융 탐색자",
            "age": int(age),
            "major": major.strip() or "미입력",
        }

if "assessment" in st.session_state:
    assessment = st.session_state["assessment"]
    trait_values = assessment["traits"]
    scores = assessment["scores"]
    top_two = scores[:2]
    best_role = top_two[0]["role"]
    second_role = top_two[1]["role"]

    st.markdown("---")
    st.markdown(f"## 2. {assessment['nickname']}님의 추천 결과")
    st.write(f"전공: **{assessment['major']}** · 나이: **{assessment['age']}세** · 분석 문항: **15/15**")
    st.caption("추천 점수는 각 업무에 연결된 성향 응답의 가중 평균을 0~100 척도로 변환한 값입니다. 점수 차이가 작다면 두 직무를 함께 탐색하는 것이 좋습니다.")

    c1, c2 = st.columns(2, gap="large")
    for col, rank_num, item in [(c1, 1, top_two[0]), (c2, 2, top_two[1])]:
        role, score = item["role"], item["score"]
        with col:
            with st.container(border=True):
                st.markdown(f'<div class="rank">{rank_num}순위 · {role["sector"]}</div>', unsafe_allow_html=True)
                st.subheader(role["title"])
                st.metric("성향 매칭 점수", f"{score}/100")
                st.progress(score / 100)
                st.write(role["summary"])
                reasons = top_reasons(role, trait_values, limit=3)
                st.markdown("**응답에서 연결된 강점**")
                for label, value, weight in reasons:
                    st.markdown(f'<span class="small-pill">{label} {value}/5</span>', unsafe_allow_html=True)
                st.markdown("**주요 업무**")
                for task in role["tasks"]:
                    st.markdown(f"- {task}")

    st.markdown("### 직무 매칭 점수 비교")
    chart_df = pd.DataFrame([{"직무": f'{x["role"]["sector"]} · {x["role"]["title"]}', "매칭 점수": x["score"]} for x in scores[:10]])
    fig = px.bar(chart_df.sort_values("매칭 점수", ascending=True), x="매칭 점수", y="직무", orientation="h", range_x=[0, 100], text="매칭 점수")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(height=520, margin=dict(l=8, r=35, t=15, b=10), xaxis_title="성향 매칭 점수(0~100)", yaxis_title="", plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 성향 프로필 · 6가지 핵심 성향")
    profile_scores = {
        label: round(sum(trait_values[key] for key in keys) / len(keys), 2)
        for label, keys in TRAIT_GROUPS.items()
    }
    trait_df = pd.DataFrame([{"성향": label, "응답 점수": value} for label, value in profile_scores.items()])
    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(r=trait_df["응답 점수"].tolist() + [trait_df["응답 점수"].iloc[0]], theta=trait_df["성향"].tolist() + [trait_df["성향"].iloc[0]], fill="toself", name="나의 응답", line=dict(color="#287c8e", width=3), fillcolor="rgba(40,124,142,0.16)"))
    radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[1, 5], tickvals=[1,2,3,4,5]), bgcolor="white"), showlegend=False, height=440, margin=dict(l=40, r=40, t=25, b=25), paper_bgcolor="white")
    st.plotly_chart(radar, use_container_width=True)
    st.dataframe(trait_df.sort_values("응답 점수", ascending=False).reset_index(drop=True), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("## 3. 1·2순위 직무 상세 분석")
    tabs = st.tabs(["🥇 1순위 상세", "🥈 2순위 상세"])
    for tab, rank_item, rank_label in zip(tabs, top_two, ["1순위", "2순위"]):
        role = rank_item["role"]
        with tab:
            st.subheader(f"{role['sector']} | {role['title']}")
            st.write(role["summary"])
            left, right = st.columns([1.15, 1])
            with left:
                st.markdown("**추천 근거**")
                matched = sorted(role["weights"].items(), key=lambda kv: trait_values[kv[0]] * kv[1], reverse=True)
                for trait, weight in matched[:5]:
                    val = trait_values[trait]
                    st.write(f"**{TRAIT_LABELS[trait]}** · 응답 {val}/5 · 직무 연관 가중치 {weight:.1f}")
                    st.progress(val / 5)
                st.markdown("**실무에서 하는 일**")
                for task in role["tasks"]:
                    st.markdown(f"- {task}")
            with right:
                st.markdown("**추천 준비 항목 (자격·역량 예시)**")
                for cert in role["certs"]:
                    st.markdown(f"- {cert}")
                st.markdown("**지금 해볼 과제**")
                st.write(role["prep"])
            st.markdown("**관련 기업·공식 사이트**")
            company_cols = st.columns(len(role["companies"]))
            for company_col, (company, desc, url) in zip(company_cols, role["companies"]):
                with company_col:
                    st.markdown(f"**{company}**")
                    st.caption(desc)
                    st.link_button(f"{company} 사이트 열기", url, use_container_width=True)

    st.markdown("---")
    st.markdown("## 4. 개인 맞춤 진로 설계")
    st.markdown("### 전공을 활용하는 방법")
    st.write(major_guidance(assessment["major"]))
    st.markdown("### 12주 실행 로드맵")
    st.caption("아래는 시작 계획 예시입니다. 실제 지원 시점과 채용 일정, 학업·경력 상황에 맞춰 조정하세요.")
    for when, action in timeline(assessment["age"]):
        with st.expander(f"{when} · {action}", expanded=True):
            st.write(action)
    st.markdown("### 채용 전형에서 자주 확인할 단계")
    for step, detail in HIRING_PROCESS:
        st.markdown(f"**{step}**  \n{detail}")
    st.warning("회사·직무·채용 유형에 따라 서류, 필기, 인적성, 과제, 면접 순서와 포함 여부가 달라집니다. 실제 지원 전에는 해당 연도 공식 채용공고를 우선 확인하세요.")

    st.markdown("### 추천 직무별 우선 실행 목록")
    action_rows = []
    for rank, item in enumerate(top_two, start=1):
        role = item["role"]
        action_rows.append({"우선순위": f"{rank}순위", "업종·직무": f"{role['sector']} / {role['title']}", "이번 주 할 일": role["prep"], "핵심 준비 예시": " · ".join(role["certs"][:2])})
    st.dataframe(pd.DataFrame(action_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("## 5. 더 알아보기")
    st.write("공식 기업·채용 사이트에서 직무 소개와 현재 공고를 확인하세요. 채용 사이트가 개편되면 회사 공식 홈페이지에서 채용 메뉴를 다시 찾아야 할 수 있습니다.")
    links = [
        ("금융위원회", "금융정책·금융권 공동채용 관련 소식", "https://www.fsc.go.kr/"),
        ("KB국민은행 채용", "은행 직무와 채용공고", "https://jobs.kbstar.com/"),
        ("IBK기업은행 채용", "채용공고·전형 안내", "https://ibk.incruit.com/apply/index.asp"),
        ("Standard Chartered 채용", "외국계 은행·글로벌 직무와 공고", "https://jobs.standardchartered.com/?locale=ko_KR"),
        ("삼성증권 신입채용 안내", "증권사 신입 채용 단계 참고", "https://www.samsungsecurities.co.kr/kor/recruit/new_employee.do"),
        ("한국거래소 채용", "금융공공기관·시장 인프라 직무", "https://krx.saramin.co.kr/service/krx/3839/applicant/apply/index.asp"),
        ("금융감독원", "금융감독·소비자보호 기관 정보", "https://www.fss.or.kr/"),
    ]
    lcols = st.columns(2)
    for i, (name, desc, url) in enumerate(links):
        with lcols[i % 2]:
            st.markdown(f"**{name}** — {desc}")
            st.link_button(f"{name} 열기", url, use_container_width=True, key=f"more_{i}")

    st.markdown("---")
    st.markdown("### 결과 저장")
    result_export = pd.DataFrame([{"순위": i + 1, "업종": item["role"]["sector"], "추천 직무": item["role"]["title"], "매칭 점수": item["score"], "업무 설명": item["role"]["summary"]} for i, item in enumerate(top_two)])
    st.download_button("추천 결과 CSV 다운로드", data=result_export.to_csv(index=False).encode("utf-8-sig"), file_name="finance_career_recommendations.csv", mime="text/csv", use_container_width=True)

st.markdown("<p class='footer-note'>금융 커리어 핏 · 진로 탐색을 위한 교육용 프로토타입 · 공식 채용 공고와 각 자격 운영기관의 최신 안내를 반드시 재확인하세요.</p>", unsafe_allow_html=True)
