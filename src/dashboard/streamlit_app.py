import streamlit as st
import pandas as pd
import plotly.express as px
import json
from pathlib import Path
import glob

def load_latest_scored():
    """Load the most recent scored data"""
    scored_files = list(Path("data/scored").glob("*.jsonl"))
    if not scored_files:
        return None, "No data"
    
    latest_file = max(scored_files, key=lambda x: x.stat().st_mtime)
    
    data = []
    with open(latest_file, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    return pd.DataFrame(data), latest_file.stem

def main():
    # Completely different page config
    st.set_page_config(
        page_title="Cyber Threat Matrix",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom dark theme CSS
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
    }
    .stApp {
        background: transparent;
    }
    .metric-container {
        background: rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 15px;
        border-left: 4px solid #00d4ff;
        margin: 10px 0;
    }
    .section-header {
        background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 1.4em;
    }
    .data-card {
        background: rgba(255,255,255,0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with different layout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 style='color: #00d4ff; margin-bottom: 0;'>🛡️ CYBER THREAT MATRIX</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #cccccc; font-size: 1.1em;'>Real-time Security Intelligence Platform</p>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: right; color: #888;'>Security Operations</div>", unsafe_allow_html=True)
    
    # Load data
    with st.spinner('🔄 Initializing threat assessment...'):
        df, date_str = load_latest_scored()
    
    if df is None or df.empty:
        st.error("🚫 Threat database unavailable. Execute scoring protocol.")
        st.info("Command: `make score` to process threat data")
        return
    
    # Status bar instead of sidebar
    st.markdown(f"""
    <div style='background: rgba(0,212,255,0.2); padding: 10px; border-radius: 8px; text-align: center; margin: 10px 0;'>
        <strong>Data Source Active:</strong> {date_str} | Last Updated: Real-time
    </div>
    """, unsafe_allow_html=True)
    
    # COMPLETELY DIFFERENT METRICS LAYOUT - Vertical cards instead of horizontal
    st.markdown("<div class='section-header'>THREAT LANDSCAPE OVERVIEW</div>", unsafe_allow_html=True)
    
    # Vertical metrics layout
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.markdown(f"""
        <div class='metric-container'>
            <div style='font-size: 0.9em; color: #00d4ff;'>TOTAL SIGNATURES</div>
            <div style='font-size: 2em; font-weight: bold;'>{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m2:
        p1_p2_count = len(df[df['band'].isin(['P1', 'P2'])])
        st.markdown(f"""
        <div class='metric-container'>
            <div style='font-size: 0.9em; color: #ff4444;'>CRITICAL THREATS</div>
            <div style='font-size: 2em; font-weight: bold;'>{p1_p2_count}</div>
            <div style='font-size: 0.8em;'>Severity Level 1 & 2</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m3:
        avg_score = df['score'].mean()
        st.markdown(f"""
        <div class='metric-container'>
            <div style='font-size: 0.9em; color: #ffaa00;'>RISK INDEX</div>
            <div style='font-size: 2em; font-weight: bold;'>{avg_score:.1f}</div>
            <div style='font-size: 0.8em;'>Average Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m4:
        source_count = df['source'].nunique()
        st.markdown(f"""
        <div class='metric-container'>
            <div style='font-size: 0.9em; color: #00ff88;'>INTEL FEEDS</div>
            <div style='font-size: 2em; font-weight: bold;'>{source_count}</div>
            <div style='font-size: 0.8em;'>Active Sources</div>
        </div>
        """, unsafe_allow_html=True)
    
    # DIFFERENT CHART LAYOUT - Single column with tabs
    st.markdown("<div class='section-header'>THREAT ANALYTICS</div>", unsafe_allow_html=True)
    
    # Use tabs instead of columns
    tab1, tab2, tab3 = st.tabs(["📋 Threat Classification", "🔍 Signature Analysis", "📈 Risk Distribution"])
    
    with tab1:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.write("**Threat Priority Matrix**")
        band_counts = df['band'].value_counts().reset_index()
        band_counts.columns = ['Threat Level', 'Count']
        # Use pie chart instead of bar chart
        fig = px.pie(band_counts, values='Count', names='Threat Level', 
                    color='Threat Level',
                    color_discrete_map={'P1': '#ff4444', 'P2': '#ffaa00', 
                                      'P3': '#ffff00', 'P4': '#00ff88'})
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.write("**Indicator Type Distribution**")
        type_counts = df['indicator_type'].value_counts().reset_index()
        type_counts.columns = ['Signature Type', 'Count']
        # Use treemap instead of pie chart
        fig = px.treemap(type_counts, path=['Signature Type'], values='Count',
                        color='Count', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<div class='data-card'>", unsafe_allow_html=True)
        st.write("**Threat Score Distribution**")
        # Use box plot instead of histogram
        fig = px.box(df, y='score', title="Threat Score Spread Analysis")
        fig.update_layout(yaxis_title="Risk Score")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # DIFFERENT TABLE LAYOUT - Cards for critical threats
    st.markdown("<div class='section-header'>🚨 CRITICAL THREAT ALERTS</div>", unsafe_allow_html=True)
    
    top_p1 = df[df['band'] == 'P1'][['indicator', 'indicator_type', 'score', 'source']].head(10)
    if not top_p1.empty:
        for idx, row in top_p1.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{row['indicator']}**")
                    st.caption(f"Type: {row['indicator_type']}")
                with col2:
                    st.markdown(f"Source: `{row['source']}`")
                with col3:
                    st.markdown(f"<div style='color: #ff4444; font-weight: bold;'>Score: {row['score']}</div>", unsafe_allow_html=True)
                st.divider()
    else:
        st.info("🟢 No critical threat alerts detected")
    
    # Different data explorer
    st.markdown("<div class='section-header'>DATABASE EXPLORER</div>", unsafe_allow_html=True)
    
    expander = st.expander("📁 Access Raw Threat Database", expanded=False)
    with expander:
        st.dataframe(df[['indicator', 'indicator_type', 'score', 'band', 'source']].head(50), 
                    use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #666; font-size: 0.8em;'>Cyber Threat Matrix v2.0 | Security Operations Center</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()