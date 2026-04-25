import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick

st.set_page_config(page_title="Hospital Readmissions Analyzer", layout="wide")

st.title("🏥 Hospital Readmissions Reduction Program")
st.markdown("**Analyzing CMS penalty data across 2,800+ U.S. hospitals**")
st.markdown("---")

@st.cache_data
def load_data():
    df = pd.read_csv("FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv")
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(' ', '_').str.replace('/', '_'))
    df['number_of_readmissions'] = pd.to_numeric(
        df['number_of_readmissions'], errors='coerce')
    df = df.dropna(subset=['excess_readmission_ratio'])
    df['penalized'] = df['excess_readmission_ratio'] > 1.0
    return df

df = load_data()

# ── Sidebar filters ──────────────────────────────────────────
st.sidebar.header("Filters")

all_states = sorted(df['state'].unique())
selected_states = st.sidebar.multiselect(
    "Select states", all_states, default=all_states)

all_conditions = sorted(df['measure_name'].unique())
selected_conditions = st.sidebar.multiselect(
    "Select conditions", all_conditions, default=all_conditions)

filtered = df[
    df['state'].isin(selected_states) &
    df['measure_name'].isin(selected_conditions)
]

# ── Top metrics ───────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
n_hospitals = filtered['facility_id'].nunique()
n_penalized = filtered.groupby('facility_id')['penalized'].any().sum()
pct_penalized = n_penalized / n_hospitals * 100 if n_hospitals > 0 else 0
avg_ratio = filtered['excess_readmission_ratio'].mean()

col1.metric("Hospitals Analyzed", f"{n_hospitals:,}")
col2.metric("Hospitals Penalized", f"{n_penalized:,}")
col3.metric("% Penalized", f"{pct_penalized:.1f}%")
col4.metric("Avg Excess Ratio", f"{avg_ratio:.4f}")

st.markdown("---")

# ── Charts ────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Avg Excess Readmission Ratio by State")
    state_avg = (filtered.groupby('state')['excess_readmission_ratio']
                 .mean().sort_values(ascending=False).reset_index())
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#d62728' if x > 1.0 else '#1f77b4'
              for x in state_avg['excess_readmission_ratio']]
    ax.bar(state_avg['state'], state_avg['excess_readmission_ratio'],
           color=colors, width=0.7)
    ax.axhline(1.0, color='black', linewidth=1.2,
               linestyle='--', label='Baseline (1.0)')
    ax.set_ylabel('Avg Excess Readmission Ratio')
    ax.legend()
    plt.xticks(rotation=90, fontsize=7)
    plt.tight_layout()
    st.pyplot(fig)

with col_right:
    st.subheader("Readmission Rate by Condition")
    cond_avg = (filtered.groupby('measure_name')['excess_readmission_ratio']
                .mean().sort_values(ascending=False).reset_index())
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.barh(cond_avg['measure_name'],
             cond_avg['excess_readmission_ratio'], color='steelblue')
    ax2.axvline(1.0, color='red', linewidth=1.2,
                linestyle='--', label='Baseline (1.0)')
    ax2.set_xlabel('Avg Excess Readmission Ratio')
    ax2.legend()
    plt.tight_layout()
    st.pyplot(fig2)

st.markdown("---")

# ── Penalty rate by state ─────────────────────────────────────
st.subheader("% of Hospitals Penalized by State")
hospital_summary = (filtered.groupby(['facility_id', 'state'])['penalized']
                    .any().reset_index())
state_penalty = (hospital_summary.groupby('state')['penalized']
                 .mean().sort_values(ascending=False).reset_index())
state_penalty.columns = ['state', 'penalty_rate']

fig3, ax3 = plt.subplots(figsize=(16, 4))
ax3.bar(state_penalty['state'], state_penalty['penalty_rate'] * 100,
        color=['#d62728' if x > 0.5 else '#1f77b4'
               for x in state_penalty['penalty_rate']])
ax3.axhline(50, color='black', linestyle='--', linewidth=1)
ax3.set_ylabel('% Hospitals Penalized')
ax3.yaxis.set_major_formatter(mtick.PercentFormatter())
plt.xticks(rotation=90, fontsize=8)
plt.tight_layout()
st.pyplot(fig3)

st.markdown("---")

# ── Hospital search table ─────────────────────────────────────
st.subheader("Search Individual Hospitals")
search = st.text_input("Type a hospital name or city")
if search:
    results = filtered[filtered['facility_name'].str.contains(
        search, case=False, na=False)]
    st.dataframe(results[['facility_name', 'state', 'measure_name',
                           'excess_readmission_ratio', 'penalized']]
                 .sort_values('excess_readmission_ratio', ascending=False),
                 use_container_width=True)
else:
    st.info("Type a hospital name above to search")

st.markdown("---")
st.caption("Data source: CMS Hospital Readmissions Reduction Program | "
           "Built as a portfolio project")
