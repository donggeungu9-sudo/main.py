import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8")
    except Exception:
        df = pd.read_csv(url, encoding="cp949")
    
    # 열 이름 공백 제거
    df.columns = df.columns.str.strip()
    
    # 날짜 및 기온 컬럼 자동 감지
    date_col = [c for c in df.columns if "날짜" in c][0]
    temp_col = [c for c in df.columns if "평균" in c][0]
    
    # 데이터 전처리
    df[date_col] = pd.to_datetime(df[date_col])
    df['연도'] = df[date_col].dt.year
    df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
    
    df = df.dropna(subset=[temp_col])
    
    # 연도별 평균 기온 계산
    yearly_df = df.groupby('연도')[temp_col].mean().reset_index()
    yearly_df.rename(columns={temp_col: '연평균기온'}, inplace=True)
    
    return yearly_df

try:
    data = load_data()
    
    # 헤더 섹션
    st.title("🌡️ 서울 100년 연평균 기온 변화 시각화")
    st.markdown("지난 100여 년간 서울의 연평균 기온 변화 추이를 한눈에 살펴볼 수 있는 대시보드입니다.")
    st.divider()

    # 사이드바 필터
    st.sidebar.header("⚙️ 데이터 옵션")
    min_year = int(data['연도'].min())
    max_year = int(data['연도'].max())
    
    selected_range = st.sidebar.slider(
        "조회 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    window_size = st.sidebar.slider(
        "이동평균(Moving Average) 구간 (년)",
        min_value=1,
        max_value=20,
        value=5,
        help="단기 변동성을 완화하여 장기적인 온난화 추세를 확인하는 데 도움을 줍니다."
    )
    
    # 필터링 및 이동평균 계산
    filtered_df = data[(data['연도'] >= selected_range[0]) & (data['연도'] <= selected_range[1])].copy()
    filtered_df['이동평균'] = filtered_df['연평균기온'].rolling(window=window_size, min_periods=1).mean()

    # 주요 지표 (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    
    start_temp = filtered_df.iloc[0]['연평균기온']
    end_temp = filtered_df.iloc[-1]['연평균기온']
    temp_change = end_temp - start_temp
    
    max_row = filtered_df.loc[filtered_df['연평균기온'].idxmax()]
    min_row = filtered_df.loc[filtered_df['연평균기온'].idxmin()]
    avg_temp = filtered_df['연평균기온'].mean()

    col1.metric("조회 기간 평균", f"{avg_temp:.1f} ℃")
    col2.metric("최고 연평균 기온", f"{max_row['연평균기온']:.1f} ℃", f"{int(max_row['연도'])}년")
    col3.metric("최저 연평균 기온", f"{min_row['연평균기온']:.1f} ℃", f"{int(min_row['연도'])}년")
    col4.metric(f"기간 내 변화량 ({selected_range[0]}→{selected_range[1]})", f"{end_temp:.1f} ℃", f"{temp_change:+.1f} ℃")

    st.markdown("---")

    # Interactive Plotly 그래프
    fig = go.Figure()

    # 연평균 기온 선 그래프
    fig.add_trace(go.Scatter(
        x=filtered_df['연도'],
        y=filtered_df['연평균기온'],
        mode='lines+markers',
        name='연평균 기온',
        line=dict(color='#E63946', width=2),
        marker=dict(size=5),
        hovertemplate='<b>%{x}년</b>: %{y:.2f}℃<extra></extra>'
    ))

    # 이동평균 추세선
    if window_size > 1:
        fig.add_trace(go.Scatter(
            x=filtered_df['연도'],
            y=filtered_df['이동평균'],
            mode='lines',
            name=f'{window_size}년 이동평균 추세선',
            line=dict(color='#1D3557', width=3, dash='dash'),
            hovertemplate=f'<b>%{{x}}년 ({window_size}년 이동평균)</b>: %{{y:.2f}}℃<extra></extra>'
        ))

    fig.update_layout(
        title=dict(
            text=f"<b>서울 연도별 평균 기온 추이 ({selected_range[0]}년 ~ {selected_range[1]}년)</b>",
            font=dict(size=18)
        ),
        xaxis=dict(title="연도", dtick=10, gridcolor='#EAEAEA'),
        yaxis=dict(title="평균 기온 (℃)", gridcolor='#EAEAEA'),
        hovermode="x unified",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # 데이터 상세 보기
    with st.expander("📊 데이터 상세보기"):
        st.dataframe(
            filtered_df[['연도', '연평균기온', '이동평균']].style.format({'연평균기온': '{:.2f}℃', '이동평균': '{:.2f}℃'}),
            use_container_width=True
        )

except Exception as e:
    st.error(f"데이터를 불러오거나 처리하는 중 오류가 발생했습니다: {e}")
