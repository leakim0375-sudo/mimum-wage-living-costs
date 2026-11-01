import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="최저임금과 생활 물가", layout="wide")

# =========================================================
# 1부. 데이터 불러오기
# =========================================================
@st.cache_data
def load_data():
    cpi = pd.read_csv("data/cpi_2014.csv")        # 물가지수 (2014년=100)
    wage = pd.read_csv("data/min_wage.csv")       # 최저임금, 최저임금지수 (2014년=100)
    real = pd.read_csv("data/real_wage.csv")      # 실질 최저임금 (2014년 물가 기준, 원)
    return cpi, wage, real


cpi, wage, real = load_data()
CATEGORIES = [c for c in cpi.columns if c not in ("연도", "총지수")]  # 12개 생활 분야

# 그래프 색상
WAGE_COLOR = "#1F4E79"    # 최저임금: 진한 파랑
PRICE_COLOR = "#7FB3D5"   # 물가: 연한 파랑
REAL_COLOR = "#2A9D8F"    # 실질 최저임금: 청록색 (위 두 선과 다른 값임을 구분)
UP_COLOR = "#4A6FA5"      # 막대: 오른 분야
DOWN_COLOR = "#B03A2E"    # 막대: 내린 분야


def growth(start_value, end_value):
    """상승률(%) = (끝 값 ÷ 시작 값 − 1) × 100"""
    return (end_value / start_value - 1) * 100


def value_in(df, year, column):
    return df.loc[df["연도"] == year, column].iloc[0]


# =========================================================
# 2부. 사이드바 만들기
# =========================================================
st.sidebar.header("조건 선택")
start, end = st.sidebar.slider("연도 범위", 2014, 2025, (2014, 2025))
chosen = st.sidebar.multiselect("생활 분야 (그래프 ②)", CATEGORIES, default=CATEGORIES)

if start == end:
    st.warning("시작 연도와 끝 연도를 다르게 골라 주세요.")
    st.stop()

cpi_r = cpi[cpi["연도"].between(start, end)]
wage_r = wage[wage["연도"].between(start, end)]
real_r = real[real["연도"].between(start, end)]

# =========================================================
# 3부. 화면과 차트 그리기
# =========================================================

# ---------- 1. 개요 ----------
st.title("최저임금은 우리 생활비보다 빨리 올랐을까?")
st.write(
    "매년 최저임금이 올랐다는 뉴스가 나오지만 생활비가 더 많이 올랐다는 말도 자주 듣습니다. "
    "시급이 오른 만큼 실제로 살 수 있는 것도 늘었는지 2014~2025년 공공데이터로 확인했습니다."
)
c1, c2, c3 = st.columns(3)
c1.info("**소비자물가지수**\n\n사람들이 사는 물건과 서비스 가격의 평균적인 수준을 나타낸 숫자")
c2.info("**2014년 = 100**\n\n단위가 다른 최저임금(원)과 물가지수를 같은 출발선에서 비교하려고 둘 다 2014년 값을 100으로 맞춤")
c3.info("**실질 최저임금**\n\n그 해 최저시급이 2014년 물가로 치면 몇 원어치인지 나타낸 값")
st.caption(f"현재 선택한 기간: {start}년 ~ {end}년")

# ---------- 2-①. 최저임금 vs 물가 ----------
wage_g = growth(value_in(wage, start, "시간급"), value_in(wage, end, "시간급"))
cpi_g = growth(value_in(cpi, start, "총지수"), value_in(cpi, end, "총지수"))
if abs(wage_g - cpi_g) < 1:
    title1 = "최저임금과 물가가 거의 같은 속도로 올랐다"
elif wage_g > cpi_g and cpi_g > 0:
    title1 = f"최저임금은 물가보다 약 {wage_g / cpi_g:.1f}배 빨리 올랐다"
elif wage_g > cpi_g:
    title1 = "최저임금이 물가보다 더 많이 올랐다"
else:
    title1 = "물가가 최저임금보다 더 많이 올랐다"
st.header(f"① {title1}")
st.caption("분석 질문: 최저임금과 물가는 각각 몇 % 올랐나?")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=wage_r["연도"], y=wage_r["최저임금지수"],
                          mode="lines+markers", name="최저임금지수",
                          line=dict(color=WAGE_COLOR)))
fig1.add_trace(go.Scatter(x=cpi_r["연도"], y=cpi_r["총지수"],
                          mode="lines+markers", name="물가 총지수",
                          line=dict(color=PRICE_COLOR)))
if start < 2018 <= end:
    fig1.add_annotation(x=2018, y=value_in(wage, 2018, "최저임금지수"),
                        text="2018년 16.4% 인상", showarrow=True, arrowhead=2, ay=-40)
fig1.update_layout(xaxis_title="연도", yaxis_title="지수 (2014년 = 100)",
                   xaxis=dict(dtick=1), hovermode="x unified")
st.plotly_chart(fig1, width="stretch")

st.write(f"{start}~{end}년 최저임금은 **{wage_g:.1f}%**, 물가(총지수)는 **{cpi_g:.1f}%** 올랐습니다.")

# ---------- 2-②. 분야별 물가 상승률 ----------
if not chosen:
    st.header("② 분야별 물가 상승률")
    st.caption("분석 질문: 어느 분야의 물가가 가장 많이 올랐나?")
    st.warning("사이드바에서 생활 분야를 하나 이상 골라 주세요.")
else:
    rates = pd.Series({c: growth(value_in(cpi, start, c), value_in(cpi, end, c)) for c in chosen})
    rates = rates.sort_values()  # 가로 막대는 아래에서 위로 그려지므로 작은 값부터
    st.header(f"② '{rates.index[-1]}' 물가가 {rates.iloc[-1]:.1f}%로 가장 많이 올랐다")
    st.caption("분석 질문: 어느 분야의 물가가 가장 많이 올랐나?")
    colors = [UP_COLOR if v >= 0 else DOWN_COLOR for v in rates]
    fig2 = go.Figure(go.Bar(x=rates.values, y=rates.index, orientation="h",
                            marker_color=colors,
                            text=[f"{v:.1f}%" for v in rates.values], textposition="outside"))
    if "주류 및 담배" in chosen and start < 2015 <= end:
        fig2.add_annotation(x=rates["주류 및 담배"], y="주류 및 담배",
                            text="2015년 담뱃값 인상", showarrow=True, arrowhead=2, ax=0, ay=45,
                            xanchor="left")
    fig2.update_layout(xaxis_title="물가 상승률 (%)", xaxis=dict(ticksuffix="%", zeroline=True),
                       height=450, margin=dict(r=80))
    st.plotly_chart(fig2, width="stretch")
    st.write(f"{start}~{end}년 가장 많이 오른 분야는 **{rates.index[-1]}({rates.iloc[-1]:.1f}%)**, "
             f"가장 적게 오른 분야는 **{rates.index[0]}({rates.iloc[0]:.1f}%)**입니다.")

# ---------- 2-③. 실질 최저임금 ----------
r_start = value_in(real, start, "실질최저임금")
r_end = value_in(real, end, "실질최저임금")
real_g = growth(r_start, r_end)
title3 = f"실질 최저임금은 {real_g:.1f}% {'늘었' if real_g >= 0 else '줄었'}"
if start < 2020 < end and abs(growth(value_in(real, 2020, "실질최저임금"), r_end)) < 1:
    title3 += "지만 2020년 이후 거의 멈췄다"
else:
    title3 += "다"
st.header(f"③ {title3}")
st.caption("분석 질문: 실질 최저임금은 얼마나 늘었나?")
fig3 = go.Figure(go.Scatter(x=real_r["연도"], y=real_r["실질최저임금"],
                            mode="lines+markers", name="실질 최저임금",
                            line=dict(color=REAL_COLOR, width=3)))
fig3.update_layout(xaxis_title="연도", yaxis_title="실질 최저임금 (원, 2014년 물가 기준)",
                   xaxis=dict(dtick=1), yaxis=dict(tickformat=","))
st.plotly_chart(fig3, width="stretch")

st.write(f"실질 최저임금은 {start}년 **{r_start:,}원**에서 {end}년 **{r_end:,}원**이 되었습니다.")

# ---------- 3. 결론 ----------
st.header("결론")
wage_all = growth(value_in(wage, 2014, "시간급"), value_in(wage, 2025, "시간급"))
cpi_all = growth(value_in(cpi, 2014, "총지수"), value_in(cpi, 2025, "총지수"))
wage_late = growth(value_in(wage, 2020, "시간급"), value_in(wage, 2025, "시간급"))
cpi_late = growth(value_in(cpi, 2020, "총지수"), value_in(cpi, 2025, "총지수"))
st.info(f"**종합 결론:** 2014~2025년 전체로 보면 최저임금({wage_all:.1f}%)이 물가({cpi_all:.1f}%)보다 "
        f"약 {wage_all / cpi_all:.1f}배 빨리 올랐습니다. 하지만 2020년 이후에는 최저임금 {wage_late:.1f}%, "
        f"물가 {cpi_late:.1f}%로 거의 같은 속도로 올라, 시급의 실제 가치는 더 늘지 않았습니다.")

# 근거 그래프: 해마다 전년 대비 상승률 비교
st.subheader("근거: 해마다 무엇이 더 많이 올랐나?")
yearly = pd.DataFrame({
    "연도": wage["연도"],
    "최저임금 상승률": wage["시간급"].pct_change() * 100,
    "물가 상승률": cpi["총지수"].pct_change() * 100,
}).dropna()
yearly_r = yearly[yearly["연도"].between(start, end)]
fig4 = go.Figure()
fig4.add_trace(go.Bar(x=yearly_r["연도"], y=yearly_r["최저임금 상승률"], name="최저임금 상승률",
                      marker_color=WAGE_COLOR, texttemplate="%{y:.1f}", textposition="outside"))
fig4.add_trace(go.Bar(x=yearly_r["연도"], y=yearly_r["물가 상승률"], name="물가 상승률",
                      marker_color=PRICE_COLOR, texttemplate="%{y:.1f}", textposition="outside"))
fig4.update_layout(barmode="group", xaxis_title="연도", yaxis_title="전년 대비 상승률 (%)",
                   xaxis=dict(dtick=1), yaxis=dict(ticksuffix="%", rangemode="tozero"))
st.plotly_chart(fig4, width="stretch")
reverse = yearly[yearly["물가 상승률"] > yearly["최저임금 상승률"]]
reverse_years = ", ".join(f"{y}년" for y in reverse["연도"])
st.caption("막대 위 숫자는 전년 대비 상승률(%)입니다. 물가 상승률은 2014년=100으로 바꾼 지수(소수 첫째 자리)로 계산했습니다.")

# 결론 확인
st.subheader("결론 확인")
early = growth(value_in(real, 2014, "실질최저임금"), value_in(real, 2019, "실질최저임금"))
late = growth(value_in(real, 2020, "실질최저임금"), value_in(real, 2025, "실질최저임금"))
all_rates = pd.Series({c: growth(value_in(cpi, start, c), value_in(cpi, end, c)) for c in CATEGORIES})
top_year = yearly.loc[yearly["최저임금 상승률"].idxmax()]
low_year = yearly.loc[yearly["최저임금 상승률"].idxmin()]
k1, k2 = st.columns(2)
k1.metric("실질 최저임금 증가율 2014→2019", f"{early:.1f}%")
k2.metric("실질 최저임금 증가율 2020→2025", f"{late:.1f}%")
st.write("- **기간 선택:** 어느 기간을 보느냐에 따라 결론이 달라집니다. 앞 기간에는 크게 늘었지만 뒤 기간에는 거의 그대로입니다.")
st.write(f"- **반대 사례:** '최저임금이 물가보다 빨리 올랐다'는 결론과 달리 {reverse_years}에는 물가가 최저임금보다 더 많이 올랐습니다. "
         f"또 모든 물가가 오른 것도 아닙니다. {start}~{end}년 '{all_rates.idxmin()}'의 상승률은 {all_rates.min():.1f}%입니다.")
st.write(f"- **극값:** 최저임금이 가장 많이 오른 해는 {int(top_year['연도'])}년({top_year['최저임금 상승률']:.1f}%), "
         f"가장 적게 오른 해는 {int(low_year['연도'])}년({low_year['최저임금 상승률']:.1f}%)입니다.")
st.write("- **상관과 인과:** 이 데이터만으로 물가가 오르거나 실질 최저임금이 멈춘 원인을 단정할 수는 없습니다.")

# ---------- 4. 해결책 ----------
st.header("해결책: 실제 가치 계산기")
st.write("시급이 올랐다는 숫자만 보지 말고 물가를 반영한 실제 가치로 판단할 수 있도록 계산기를 제작했습니다. "
         "연도와 금액을 넣으면 2014년 물가로 환산한 값을 보여 줍니다.")
a1, a2 = st.columns(2)
calc_year = a1.number_input("연도", min_value=2014, max_value=2025, value=2025, step=1)
amount = a2.number_input("금액 (원)", min_value=0, value=10030, step=1000)
real_value = amount / value_in(cpi, calc_year, "총지수") * 100
food_value = amount / value_in(cpi, calc_year, "식료품 및 비주류음료") * 100
m1, m2 = st.columns(2)
m1.metric(f"{calc_year}년 {amount:,}원의 실제 가치 (전체 물가 기준)", f"{real_value:,.0f}원")
m2.metric("식료품 물가 기준으로 계산하면", f"{food_value:,.0f}원")
st.caption("2014년 물가로 환산한 값입니다. 식료품처럼 더 많이 오른 품목을 기준으로 하면 실제 가치는 더 낮아집니다.")

# ---------- 5. 데이터 출처 ----------
st.divider()
st.caption("데이터 출처: 국가데이터처 「소비자물가조사」 지출목적별 소비자물가지수(KOSIS), "
           "최저임금위원회 연도별 최저임금")
