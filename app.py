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
st.header("① 최저임금과 물가는 각각 몇 % 올랐나?")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=wage_r["연도"], y=wage_r["최저임금지수"],
                          mode="lines+markers", name="최저임금지수"))
fig1.add_trace(go.Scatter(x=cpi_r["연도"], y=cpi_r["총지수"],
                          mode="lines+markers", name="물가 총지수"))
if start < 2018 <= end:
    fig1.add_annotation(x=2018, y=value_in(wage, 2018, "최저임금지수"),
                        text="2018년 16.4% 인상", showarrow=True, arrowhead=2, ay=-40)
fig1.update_layout(xaxis_title="연도", yaxis_title="지수 (2014년 = 100)",
                   xaxis=dict(dtick=1), hovermode="x unified")
st.plotly_chart(fig1, width="stretch")

wage_g = growth(value_in(wage, start, "최저임금지수"), value_in(wage, end, "최저임금지수"))
cpi_g = growth(value_in(cpi, start, "총지수"), value_in(cpi, end, "총지수"))
more = "최저임금이" if wage_g > cpi_g else "물가가"
st.success(f"**답:** {start}~{end}년 최저임금은 {wage_g:.1f}%, 물가는 {cpi_g:.1f}% 올라 "
           f"{more} 더 많이 올랐습니다.")

# ---------- 2-②. 분야별 물가 상승률 ----------
st.header("② 어느 분야의 물가가 가장 많이 올랐나?")
if not chosen:
    st.warning("사이드바에서 생활 분야를 하나 이상 골라 주세요.")
else:
    rates = pd.Series({c: growth(value_in(cpi, start, c), value_in(cpi, end, c)) for c in chosen})
    rates = rates.sort_values()  # 가로 막대는 아래에서 위로 그려지므로 작은 값부터
    colors = ["#1f77b4" if v >= 0 else "#d62728" for v in rates]
    fig2 = go.Figure(go.Bar(x=rates.values, y=rates.index, orientation="h",
                            marker_color=colors,
                            text=[f"{v:.1f}%" for v in rates.values], textposition="outside"))
    if "주류 및 담배" in chosen and start < 2015 <= end:
        fig2.add_annotation(x=rates["주류 및 담배"], y="주류 및 담배",
                            text="2015년 담뱃값 인상", showarrow=True, arrowhead=2, ax=60, ay=25)
    fig2.update_layout(xaxis_title="물가 상승률 (%)", xaxis=dict(ticksuffix="%", zeroline=True),
                       height=450, margin=dict(r=80))
    st.plotly_chart(fig2, width="stretch")
    st.success(f"**답:** {start}~{end}년 가장 많이 오른 분야는 {rates.index[-1]}({rates.iloc[-1]:.1f}%), "
               f"가장 적게 오른 분야는 {rates.index[0]}({rates.iloc[0]:.1f}%)입니다.")

# ---------- 2-③. 실질 최저임금 ----------
st.header("③ 실질 최저임금은 얼마나 늘었나?")
fig3 = go.Figure(go.Scatter(x=real_r["연도"], y=real_r["실질최저임금"],
                            mode="lines+markers", name="실질 최저임금"))
fig3.update_layout(xaxis_title="연도", yaxis_title="실질 최저임금 (원, 2014년 물가 기준)",
                   xaxis=dict(dtick=1), yaxis=dict(tickformat=","))
st.plotly_chart(fig3, width="stretch")

r_start = value_in(real, start, "실질최저임금")
r_end = value_in(real, end, "실질최저임금")
st.success(f"**답:** 실질 최저임금은 {start}년 {r_start:,}원에서 {end}년 {r_end:,}원으로 "
           f"{growth(r_start, r_end):.1f}% 늘었습니다.")

# ---------- 3. 결론 확인 ----------
st.header("결론 확인")
early = growth(value_in(real, 2014, "실질최저임금"), value_in(real, 2019, "실질최저임금"))
late = growth(value_in(real, 2020, "실질최저임금"), value_in(real, 2025, "실질최저임금"))
all_rates = pd.Series({c: growth(value_in(cpi, start, c), value_in(cpi, end, c)) for c in CATEGORIES})
k1, k2 = st.columns(2)
k1.metric("실질 최저임금 증가율 2014→2019", f"{early:.1f}%")
k2.metric("실질 최저임금 증가율 2020→2025", f"{late:.1f}%")
st.write(f"- **기간 선택:** 어느 기간을 보느냐에 따라 결론이 달라집니다. 앞 기간에는 크게 늘었지만 뒤 기간에는 거의 그대로입니다.")
st.write(f"- **반대 사례:** 모든 물가가 오른 것은 아닙니다. {start}~{end}년 가장 적게 오른 분야인 '{all_rates.idxmin()}'의 상승률은 {all_rates.min():.1f}%입니다.")
st.write("- **상관과 인과:** 이 데이터만으로 물가가 오른 원인을 단정할 수는 없습니다.")

# ---------- 4. 해결책 ----------
st.header("해결책: 실제 가치로 확인해 보자")
st.write("시급이나 용돈이 올랐다는 숫자만 보지 말고, 물가를 반영한 실제 가치로 확인해 보세요.")
a1, a2 = st.columns(2)
calc_year = a1.number_input("연도", min_value=2014, max_value=2025, value=2025, step=1)
amount = a2.number_input("금액 (원)", min_value=0, value=10030, step=1000)
real_value = amount / value_in(cpi, calc_year, "총지수") * 100
st.metric(f"{calc_year}년 {amount:,}원의 실제 가치 (2014년 물가 기준)", f"{real_value:,.0f}원")
st.caption("전체 물가 평균으로 계산하므로, 식료품·외식처럼 더 많이 오른 품목에만 쓰면 실제 가치는 더 낮을 수 있습니다.")

# ---------- 5. 데이터 출처 ----------
st.divider()
st.caption("데이터 출처: 국가데이터처 「소비자물가조사」 지출목적별 소비자물가지수(KOSIS), "
           "최저임금위원회 연도별 최저임금")
