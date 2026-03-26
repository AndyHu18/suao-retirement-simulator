"""
養生造鎮決策模擬器
Suao Retirement Community Monte Carlo Simulator

Main Streamlit application entry point.
"""

import streamlit as st
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env file for API keys
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, 'r', encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip().rstrip('\r\n')
            if '=' in _line and not _line.startswith('#') and _line:
                _k, _v = _line.split('=', 1)
                os.environ[_k.strip()] = _v.strip()

from engine.monte_carlo import run_monte_carlo, extract_metrics, run_stress_tests
from ui.sidebar import render_sidebar
from ui.dashboard import render_dashboard
from ui.ai_analysis import render_ai_analysis
from ui.methodology import render_methodology

st.set_page_config(
    page_title="養生造鎮決策模擬器",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏘️ 養生造鎮決策模擬器")
st.caption("宜蘭蘇澳 · 8,000 戶 · 25 年蒙地卡羅模擬 · v2.0")


def _params_hash(params):
    """Create a hashable key from params for caching."""
    # Exclude internal keys
    items = []
    for k, v in sorted(params.items()):
        if k.startswith('_'):
            continue
        if isinstance(v, list):
            items.append((k, tuple(v)))
        elif isinstance(v, dict):
            items.append((k, tuple(sorted(v.items()))))
        else:
            items.append((k, v))
    return hash(tuple(items))


# --- Sidebar controls ---
params = render_sidebar()
mc_runs = params.pop('_mc_runs', 1000)

# --- Run simulation ---
params_key = _params_hash(params)

# Cache results in session state
if ('mc_result' not in st.session_state
        or st.session_state.get('params_key') != params_key):
    # Save previous metrics for before/after comparison
    if 'current_metrics' in st.session_state:
        st.session_state.prev_metrics = st.session_state.current_metrics

    with st.spinner(f"正在執行 {mc_runs} 次蒙地卡羅模擬..."):
        mc_result = run_monte_carlo(params, n_runs=mc_runs, seed=42)
        metrics = extract_metrics(mc_result)
        mc_result['_metrics'] = metrics

        # Run stress tests (lighter: 200 runs each)
        stress_results = run_stress_tests(params, n_runs=200)

    st.session_state.mc_result = mc_result
    st.session_state.stress_results = stress_results
    st.session_state.current_metrics = metrics
    st.session_state.params_key = params_key
    st.session_state.current_params = dict(params)

mc_result = st.session_state.mc_result
stress_results = st.session_state.stress_results
metrics = st.session_state.current_metrics

# --- Render dashboard ---
render_dashboard(mc_result, params, stress_results)

# --- Tabs: AI Analysis + Methodology ---
tab_ai, tab_method = st.tabs(["🤖 AI 分析報告", "📐 方法論"])

with tab_ai:
    render_ai_analysis(params, metrics, mc_result)

with tab_method:
    render_methodology()
