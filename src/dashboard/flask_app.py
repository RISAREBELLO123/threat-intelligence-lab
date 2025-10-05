from flask import Flask, render_template, jsonify
import json
import pandas as pd
import plotly
import plotly.express as px
from pathlib import Path
from datetime import datetime
import glob

app = Flask(__name__)

def load_scored_data(date_str=None):
    """Load latest scored data"""
    if not date_str:
        # Find latest scored file
        scored_files = list(Path("data/scored").glob("*.jsonl"))
        if not scored_files:
            return None
        latest = max(scored_files, key=lambda x: x.stat().st_mtime)
        date_str = latest.stem
    
    file_path = Path(f"data/scored/{date_str}.jsonl")
    if not file_path.exists():
        return None
    
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    return pd.DataFrame(data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    df = load_scored_data()
    if df is None or df.empty:
        return jsonify({"error": "No data available"})
    
    # Basic statistics
    stats = {
        "total_indicators": len(df),
        "band_distribution": df['band'].value_counts().to_dict(),
        "type_distribution": df['indicator_type'].value_counts().to_dict(),
        "avg_score": df['score'].mean(),
        "high_risk_count": len(df[df['band'].isin(['P1', 'P2'])])
    }
    
    return jsonify(stats)

@app.route('/api/band_chart')
def band_chart():
    df = load_scored_data()
    if df is None or df.empty:
        return jsonify({"error": "No data available"})
    
    band_counts = df['band'].value_counts().reset_index()
    band_counts.columns = ['band', 'count']
    
    fig = px.bar(band_counts, x='band', y='count', 
                 title='Indicators by Priority Band',
                 color='band',
                 color_discrete_map={'P1': 'red', 'P2': 'orange', 'P3': 'yellow', 'P4': 'green'})
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/type_chart')
def type_chart():
    df = load_scored_data()
    if df is None or df.empty:
        return jsonify({"error": "No data available"})
    
    type_counts = df['indicator_type'].value_counts().reset_index()
    type_counts.columns = ['type', 'count']
    
    fig = px.pie(type_counts, values='count', names='type', 
                 title='Indicator Types Distribution')
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/api/top_indicators')
def top_indicators():
    df = load_scored_data()
    if df is None or df.empty:
        return jsonify({"error": "No data available"})
    
    top_p1 = df[df['band'] == 'P1'][['indicator', 'indicator_type', 'score', 'source']].head(10)
    return jsonify(top_p1.to_dict('records'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
