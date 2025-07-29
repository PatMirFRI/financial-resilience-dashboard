#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Step 1: Imports & Page Setup (with sidebar width fix)
import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Financial Resilience Segments Dashboard", 
    page_icon="🍁", 
    layout="wide"
)

# CSS to increase sidebar width and improve appearance
st.markdown("""
<style>
    /* Increase sidebar width */
    section[data-testid="stSidebar"] {
        width: 375px !important;
    }
    
    /* Adjust main content area */
    .main > div {
        padding-left: 400px !important;
    }
    
    /* Improve sidebar content styling */
    section[data-testid="stSidebar"] .stMarkdown {
        font-size: 0.95rem;
    }
    
    section[data-testid="stSidebar"] .stMultiSelect label {
        font-weight: 600;
        color: #262730;
        margin-bottom: 0.5rem;
    }
    
    /* Style the dividers */
    section[data-testid="stSidebar"] hr {
        margin: 1.5rem 0;
    }
    
    /* Info box styling */
    .sidebar-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00AEEF;
        font-size: 0.85rem;
        line-height: 1.5;
    }
    
    /* Color legend styling */
    .color-legend-item {
        display: flex;
        align-items: center;
        margin: 8px 0;
        font-size: 0.9rem;
    }
    
    .color-box {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        margin-right: 10px;
        border: 1px solid rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# In[2]:


# Step 2: Data Loading
@st.cache_data
def load_data():
    segments_data = pd.read_excel("Interative dashboard.xlsx", sheet_name="Index_segment")
    # Clean empty provinces - treat them as 'Canada (Overall)'
    segments_data['Province'] = segments_data['Province'].fillna('Canada (Overall)')
    segments_data['Province'] = segments_data['Province'].apply(
        lambda x: 'Canada (Overall)' if pd.isna(x) or str(x).strip() == '' else str(x)
    )
    return segments_data

segments_data = load_data()


# In[ ]:


# Step 3: Color config and Category Helper
SEGMENT_CATEGORIES = [
    "Extremely Vulnerable", 
    "Financially Vulnerable", 
    "Approaching Resilience", 
    "Financially Resilient"
]
SEGMENT_COLORS = {
    "Extremely Vulnerable": "#C00000",
    "Financially Vulnerable": "#ED175B",
    "Approaching Resilience": "#1E196A",
    "Financially Resilient": "#00AEEF"
}


# In[ ]:


# Step 4: Sidebar Filters - Enhanced Version

# Reset button at the top
if st.sidebar.button("🔄 Reset All Filters", type="primary", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Quick Presets Section
st.sidebar.markdown("### ⚡ Quick Presets")
col1, col2 = st.sidebar.columns(2)

# We need to define these variables first before using them in presets
# Get data options
try:
    year_options = sorted(segments_data['Survey round'].dropna().unique().tolist())
    province_options = ['Canada (Overall)'] + sorted(
        [prov for prov in segments_data['Province'].dropna().unique() if prov != 'Canada (Overall)']
    )
except:
    year_options = []
    province_options = ['Canada (Overall)']

with col1:
    latest_round = year_options[-1] if year_options else "June 2025"
    button_label = f"Latest Round ({latest_round})"
    if st.button("button_label", key="preset1", use_container_width=True):
        if year_options:
            st.session_state.year_filter = [year_options[-1]]
            st.session_state.province_filter = ['Canada (Overall)']
            st.session_state.segment_multiselect = ["All Segments"]
            st.rerun()

with col2:
    if st.button("All Time", key="preset2", use_container_width=True):
        st.session_state.year_filter = year_options
        st.session_state.province_filter = ['Canada (Overall)']
        st.session_state.segment_multiselect = ["All Segments"]
        st.rerun()

st.sidebar.markdown("---")

# Filter Section
# Year filter
with st.sidebar.container():
    st.markdown("**📅 Survey Round(s)**")
    try:
        selected_years = st.multiselect(
            "Select one or more survey rounds:",
            year_options,
            default=st.session_state.get('year_filter', [year_options[-1]] if year_options else []),
            key="year_filter",
            help="Choose which survey rounds to include in the analysis"
        )
        
        if selected_years:
            st.caption(f"Selected: {len(selected_years)} round(s)")
    except KeyError:
        st.error("Survey round data not found")
        selected_years = []

st.sidebar.markdown("")

# Province filter
with st.sidebar.container():
    st.markdown("**📍 Location(s)**")
    
    # Quick selection buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("All Provinces", key="all_prov", use_container_width=True):
            st.session_state.province_filter = province_options
            st.rerun()
    with col2:
        if st.button("Clear All", key="clear_prov", use_container_width=True):
            st.session_state.province_filter = []
            st.rerun()
    
    # Multiselect
    selected_provinces = st.multiselect(
        "Select provinces or Canada overall:",
        province_options,
        default=st.session_state.get('province_filter', ['Canada (Overall)']),
        key="province_filter",
        help="Choose geographic areas to analyze"
    )
    
    if selected_provinces:
        st.caption(f"Selected: {len(selected_provinces)} location(s)")

st.sidebar.markdown("")

# Segment filter
with st.sidebar.container():
    st.markdown("**📊 Financial Resilience Segment(s)**")
    
    segment_options = ["All Segments"] + SEGMENT_CATEGORIES
    
    # Quick selection buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("All Segments", key="all_seg", use_container_width=True):
            st.session_state.segment_multiselect = ["All Segments"]
            st.rerun()
    with col2:
        if st.button("Clear All", key="clear_seg", use_container_width=True):
            st.session_state.segment_multiselect = []
            st.rerun()
    
    # Multiselect
    selected_segments = st.multiselect(
        "Select segments to display:",
        segment_options,
        default=st.session_state.get('segment_multiselect', ["All Segments"]),
        key="segment_multiselect",
        help="Choose which financial resilience segments to include"
    )
    
    # Handle "All Segments" logic
    if "All Segments" in selected_segments:
        selected_segments = SEGMENT_CATEGORIES
    elif not selected_segments:
        selected_segments = SEGMENT_CATEGORIES
    
    st.caption(f"Selected: {len(selected_segments)} segment(s)")

st.sidebar.markdown("---")
chart_type = st.sidebar.radio(
    "Chart Type:",
    options=["Pie chart", "Bar chart", "Trended line chart"],
    horizontal=True
)


# Color legend
with st.sidebar.expander("🎨 Segment Color Legend", expanded=True):
    st.markdown("""
    <div style='border-radius:8px; padding: 18px 15px 10px 15px; background-color: #E8F4FB; border: 1px solid #BFE1FC; margin-bottom: 20px;'>
    <b>Color Legend:</b><br>
    <span style='color:#C00000; font-size:22px; vertical-align:middle'>●</span> <b>Extremely Vulnerable</b> (0–30)<br>
    <span style='color:#ED175B; font-size:22px; vertical-align:middle'>●</span> <b>Financially Vulnerable</b> (30.0–50)<br>
    <span style='color:#1E196A; font-size:22px; vertical-align:middle'>●</span> <b>Approaching Resilience</b> (50.0–70)<br>
    <span style='color:#00AEEF; font-size:22px; vertical-align:middle'>●</span> <b>Financially Resilient</b> (70.0–100)
    </div>
    """, unsafe_allow_html=True)


# Download section (only show if data is filtered)
# Note: This assumes 'filtered' DataFrame exists from Step 5
if 'filtered' in locals() and not filtered.empty:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Export Data")
    
    csv = filtered.to_csv(index=False)
    
    st.sidebar.download_button(
        label="⬇️ Download Filtered Data (CSV)",
        data=csv,
        file_name=f"FRI_data_{'-'.join(str(y) for y in selected_years)}.csv",
        mime="text/csv",
        help="Download the filtered dataset as CSV file",
        use_container_width=True
    )
    
    st.sidebar.caption(f"Export contains {len(filtered):,} records")


# Information section
with st.sidebar.expander("ℹ️ Dashboard Information", expanded=False):
    st.markdown("""
    <div class='sidebar-info'>
        <b>About this Dashboard</b><br>
        • Data updates quarterly<br>
        • Gray areas in pie charts represent unselected segments<br>
        • All data from Financial Resilience Institute surveys
    </div>
    """, unsafe_allow_html=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #888; font-size: 0.75rem; padding: 10px 0;'>
    © 2025 Financial Resilience Institute<br>
    All Rights Reserved
</div>
""", unsafe_allow_html=True)


# In[ ]:


# Step 5: Main Filtered DataFrame

if not segments_data.empty and selected_years:
    # Filter by years and segments
    filtered = segments_data[
        (segments_data['Survey round'].isin(selected_years)) &
        (segments_data['Index segments'].isin(selected_segments))
    ].copy()

    # Province (including Canada) filtering
    if selected_provinces:
        if "Canada (Overall)" in selected_provinces:
            if len(selected_provinces) == 1:
                # Only Canada (Overall) - filter for Canada (Overall)
                filtered = filtered[filtered['Province'] == "Canada (Overall)"]
            else:
                # Canada (Overall) + other(s): include both
                filtered = filtered[
                    (filtered['Province'] == "Canada (Overall)") |
                    (filtered['Province'].isin([prov for prov in selected_provinces if prov != "Canada (Overall)"]))
                ]
        else:
            # Specific provinces only
            filtered = filtered[filtered['Province'].isin(selected_provinces)]
else:
    filtered = pd.DataFrame()


# In[ ]:


# Step 6: Visualization Choices and Main Title



# Main page title and subtitle
st.title("🍁 Financial Resilience Segments Dashboard")

if selected_years and selected_provinces:
    subtitle = (
        f"**Survey Rounds:** {', '.join(str(y) for y in selected_years)} | "
        f"**Locations:** {', '.join(selected_provinces)} | "
        f"**Segments:** {', '.join(selected_segments)}"
    )
    st.markdown(subtitle)
    st.markdown("---")


# In[ ]:


# Step 7: Visualization Rendering

# Helper function for consistent footer annotation with adjustable spacing
def add_footer_annotation(fig, y_position=-0.10):
    """
    Add copyright footer to any Plotly figure with proper spacing
    y_position: Negative values place footer below the chart area
    """
    fig.add_annotation(
        text="© 2025 Financial Resilience Institute. All Rights Reserved.",
        showarrow=False,
        xref="paper", yref="paper",
        x=0.98, y=y_position,
        xanchor="right", yanchor="bottom",
        font=dict(size=10, color="#888888", family="Avenir, sans-serif")
    )
    return fig

if filtered.empty:
    st.warning("⚠️ No data available for your filter selection. Please adjust your filters.")
else:
    show_names = sorted(filtered['Index segments'].unique(), key=lambda s: SEGMENT_CATEGORIES.index(s))
    
    # ═══════════════════════════════ PIE CHART ═══════════════════════════════
    if chart_type == "Pie chart":
        # Helper function to get actual proportions for pie charts
        @st.cache_data(show_spinner=False)
        def get_pie_data(df, year, prov):
            """Get all segments data for a specific year and province"""
            all_rows = df[(df["Survey round"] == year) & (df["Province"] == prov)]
            return (
                all_rows.groupby("Index segments", as_index=False)["Proportion"]
                .sum()
                .sort_values("Index segments", key=lambda s: s.map({seg: i for i, seg in enumerate(SEGMENT_CATEGORIES)}))
            )
        
        # Multiple pie charts (subplots)
        if len(selected_years) > 1 or len(selected_provinces) > 1:
            # Determine combinations to show
            if len(selected_years) > 1 and len(selected_provinces) > 1:
                combinations = [(y, p) for y in selected_years[:3] for p in selected_provinces[:2]][:6]
            elif len(selected_years) > 1:
                combinations = [(y, selected_provinces[0]) for y in selected_years[:6]]
            else:
                combinations = [(selected_years[0], p) for p in selected_provinces[:6]]
            
            # Create subplot grid
            n_charts = len(combinations)
            cols = min(3, n_charts)
            rows = (n_charts + cols - 1) // cols
            
            fig = make_subplots(
                rows=rows,
                cols=cols,
                specs=[[{"type": "pie"} for _ in range(cols)] for _ in range(rows)],
                subplot_titles=[f"{y} – {p}" for y, p in combinations],
                vertical_spacing=0.14,
                horizontal_spacing=0.08
            )
            
            # Add each pie chart
            for idx, (year, prov) in enumerate(combinations):
                row_idx = idx // cols + 1
                col_idx = idx % cols + 1
                
                # Get ALL segments data (not just selected ones)
                all_segments_data = get_pie_data(segments_data, year, prov)
                
                # Separate selected vs unselected
                selected_data = all_segments_data[all_segments_data["Index segments"].isin(selected_segments)]
                total_all = all_segments_data["Proportion"].sum()
                total_selected = selected_data["Proportion"].sum()
                unselected = total_all - total_selected
                
                # Build pie data
                labels = selected_data["Index segments"].tolist()
                values = selected_data["Proportion"].tolist()
                colors = [SEGMENT_COLORS[seg] for seg in labels]
                
                # Add gray slice for unselected segments if any
                if unselected > 0.001:
                    labels.append("Not Selected")
                    values.append(unselected)
                    colors.append("#E8E8E8")
                
                # Add pie trace
                fig.add_trace(
                    go.Pie(
                        labels=labels,
                        values=values,
                        marker=dict(
                            colors=colors,
                            line=dict(color="white", width=2)
                        ),
                        textinfo="label+percent",
                        hovertemplate="<b>%{label}</b><br>Proportion: %{value:.1%}<br>%{percent} of total",
                        sort=False,
                        pull=[0.03 if label == "Not Selected" else 0 for label in labels],
                        showlegend=(idx == 0)  # Only show legend for first pie
                    ),
                    row=row_idx,
                    col=col_idx
                )
            
            # Update layout
            fig.update_layout(
                height=380 * rows + 100,
                title="Financial Resilience Segment Distribution – Actual Proportions",
                margin=dict(t=80, b=140),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5
                )
            )
            
            # Add footer
            add_footer_annotation(fig, y_position=-0.20)
            st.plotly_chart(fig, use_container_width=True)
            
            # Info message if not all segments selected
            if len(selected_segments) < len(SEGMENT_CATEGORIES):
                st.info(f"📊 Showing {len(selected_segments)} of {len(SEGMENT_CATEGORIES)} segments. Gray areas represent unselected segments.")
        
        # Single pie chart
        else:
            year = selected_years[0]
            prov = selected_provinces[0]
            
            # Get ALL segments data for actual proportions
            all_segments_data = get_pie_data(segments_data, year, prov)
            
            if all_segments_data.empty:
                st.warning("No data available for selected filters")
            else:
                # Separate selected vs unselected
                selected_data = all_segments_data[all_segments_data["Index segments"].isin(selected_segments)]
                total_all = all_segments_data["Proportion"].sum()
                total_selected = selected_data["Proportion"].sum()
                unselected = total_all - total_selected
                
                # Build pie data
                labels = selected_data["Index segments"].tolist()
                values = selected_data["Proportion"].tolist()
                colors = [SEGMENT_COLORS[seg] for seg in labels]
                
                # Add gray slice for unselected segments if any
                if unselected > 0.001:
                    labels.append("Not Selected")
                    values.append(unselected)
                    colors.append("#E8E8E8")
                
                # Create pie chart
                fig = go.Figure(go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.35,
                    marker=dict(
                        colors=colors,
                        line=dict(color="white", width=2)
                    ),
                    textinfo="label+percent",
                    hovertemplate="<b>%{label}</b><br>Proportion: %{value:.1%}<br>%{percent} of total",
                    pull=[0.04 if label == "Not Selected" else 0 for label in labels],
                    sort=False
                ))
                
                # Update layout with center annotation
                fig.update_layout(
                    title=f"Segment Distribution – {year} – {prov}",
                    height=560,
                    margin=dict(t=80, b=120),
                    annotations=[
                        dict(
                            text=f"{total_selected:.1%}<br>Selected",
                            x=0.5, y=0.5,
                            font_size=22,
                            showarrow=False
                        ),
                        dict(
                            text="© 2025 Financial Resilience Institute. All Rights Reserved.",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.98, y=-0.14,
                            xanchor="right", yanchor="bottom",
                            font=dict(size=10, color="#888888", family="Avenir, sans-serif")
                        )
                    ]
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display metrics
                if len(selected_segments) < len(SEGMENT_CATEGORIES):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.info(f"📊 Showing {len(selected_segments)} of {len(SEGMENT_CATEGORIES)} segments. "
                               f"Gray area represents unselected segments.")
                    with col2:
                        st.metric("Selected", f"{total_selected:.1%}")
                    with col3:
                        st.metric("Unselected", f"{unselected:.1%}")
                else:
                    st.success("✅ All segments selected – showing complete distribution")
                    
                # Show largest segment
                if labels and "Not Selected" not in labels:
                    largest_idx = values.index(max(values))
                    st.metric("Largest Segment", f"{labels[largest_idx]}: {values[largest_idx]:.1%}")

    # ═══════════════════════════════ BAR CHART ═══════════════════════════════
    elif chart_type == "Bar chart":
        bar_data = filtered.copy()
        num_provinces = len(selected_provinces)
        num_years = len(selected_years)
        
        # CASE 1: Multiple Provinces AND Multiple Years
        if num_provinces > 1 and num_years > 1:
            st.info(f"📊 Showing {num_years} years across {min(num_provinces, 4)} provinces")
            
            # Limit to 4 provinces for readability
            display_provinces = selected_provinces[:4]
            
            # Create subplots
            fig = make_subplots(
                rows=1,
                cols=len(display_provinces),
                subplot_titles=display_provinces,
                shared_yaxes=True,
                horizontal_spacing=0.05
            )
            
            # Add bars for each province
            for idx, province in enumerate(display_provinces):
                prov_data = bar_data[bar_data['Province'] == province]
                
                for year_idx, year in enumerate(selected_years):
                    year_data = prov_data[prov_data['Survey round'] == year]
                    if not year_data.empty:
                        year_summary = year_data.groupby('Index segments')['Proportion'].mean().reset_index()
                        
                        for seg_idx, segment in enumerate(SEGMENT_CATEGORIES):
                            seg_data = year_summary[year_summary['Index segments'] == segment]
                            if not seg_data.empty:
                                fig.add_trace(
                                    go.Bar(
                                        name=f"{year}" if idx == 0 and seg_idx == 0 else None,
                                        x=[segment],
                                        y=seg_data['Proportion'].values,
                                        marker_color=px.colors.qualitative.Set2[year_idx % len(px.colors.qualitative.Set2)],
                                        text=[f"{seg_data['Proportion'].values[0]:.1%}"],
                                        textposition='outside',
                                        showlegend=(idx == 0 and seg_idx == 0),
                                        legendgroup=str(year)
                                    ),
                                    row=1,
                                    col=idx + 1
                                )
            
            # Update layout
            fig.update_layout(
                title="Financial Resilience Distribution by Province and Year",
                height=650,
                barmode='group',
                legend_title="Survey Round",
                margin=dict(b=180, t=80)
            )
            
            fig.update_xaxes(tickangle=-45)
            fig.update_yaxes(tickformat=".0%", title="Proportion", row=1, col=1)
            
            max_val = bar_data['Proportion'].max()
            fig.update_yaxes(range=[0, max_val * 1.2])
            
            add_footer_annotation(fig, y_position=-0.12)
            st.plotly_chart(fig, use_container_width=True)
            
            if num_provinces > 4:
                st.warning(f"Showing first 4 of {num_provinces} provinces. Consider using the trend chart for all provinces.")
        
        # CASE 2: Multiple Provinces, Single Year
        elif num_provinces > 1 and num_years == 1:
            year = selected_years[0]
            
            # Option for horizontal bars
            use_horizontal = st.checkbox("Use horizontal bars", value=(num_provinces > 6))
            
            if use_horizontal:
                # Horizontal bars
                fig = px.bar(
                    bar_data,
                    y="Index segments",
                    x="Proportion",
                    color="Province",
                    orientation='h',
                    category_orders={"Index segments": list(reversed(SEGMENT_CATEGORIES))},
                    text="Proportion",
                    title=f"Financial Resilience Distribution by Province – {year}",
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                
                fig.update_traces(
                    texttemplate='%{text:.1%}',
                    textposition='outside'
                )
                
                fig.update_layout(
                    xaxis_tickformat=".0%",
                    yaxis_title="Segment",
                    xaxis_title="Proportion",
                    height=max(500, 80 * len(SEGMENT_CATEGORIES) + 100),
                    legend_title="Province",
                    margin=dict(l=200, b=120, r=80, t=80)
                )
                
                max_val = bar_data['Proportion'].max()
                fig.update_xaxes(range=[0, max_val * 1.15])
                
                add_footer_annotation(fig, y_position=-0.14)
                
            else:
                # Vertical bars
                fig = px.bar(
                    bar_data,
                    x="Index segments",
                    y="Proportion",
                    color="Province",
                    barmode="group",
                    category_orders={"Index segments": SEGMENT_CATEGORIES},
                    text="Proportion",
                    title=f"Financial Resilience Distribution by Province – {year}",
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                
                fig.update_traces(
                    texttemplate='%{text:.1%}',
                    textposition='outside',
                    textfont_size=10
                )
                
                fig.update_layout(
                    yaxis_tickformat=".0%",
                    xaxis_title="Segment",
                    yaxis_title="Proportion",
                    height=650,
                    legend_title="Province",
                    xaxis_tickangle=0,
                    margin=dict(b=130, t=80),
                    bargap=0.15,
                    bargroupgap=0.05
                )
                
                max_val = bar_data['Proportion'].max()
                fig.update_yaxes(range=[0, max_val * 1.2])
                
                add_footer_annotation(fig, y_position=-0.10)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary table
            st.subheader("Summary by Province")
            summary_df = bar_data.pivot_table(
                index='Index segments',
                columns='Province',
                values='Proportion',
                aggfunc='mean'
            ).round(3)
            st.dataframe(summary_df.style.format("{:.1%}"))
        
        # CASE 3: Single Province, Multiple Years
        elif num_provinces == 1 and num_years > 1:
            province = selected_provinces[0]
            
            fig = px.bar(
                bar_data,
                x="Index segments",
                y="Proportion",
                color="Survey round",
                barmode="group",
                category_orders={"Index segments": SEGMENT_CATEGORIES},
                text="Proportion",
                title=f"Financial Resilience Trends – {province}",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            
            fig.update_traces(
                texttemplate='%{text:.1%}',
                textposition='outside',
                textfont_size=10
            )
            
            fig.update_layout(
                yaxis_tickformat=".0%",
                xaxis_title="Segment",
                yaxis_title="Proportion",
                height=650,
                legend_title="Survey Round",
                xaxis_tickangle=0,
                margin=dict(b=120, t=80),
                bargap=0.15,
                bargroupgap=0.1
            )
            
            max_val = bar_data['Proportion'].max()
            fig.update_yaxes(range=[0, max_val * 1.2])
            
            add_footer_annotation(fig, y_position=-0.10)
            st.plotly_chart(fig, use_container_width=True)
        
        # CASE 4: Single Province, Single Year
        else:
            year = selected_years[0]
            province = selected_provinces[0]
            
            fig = px.bar(
                bar_data,
                x="Index segments",
                y="Proportion",
                color="Index segments",
                color_discrete_map=SEGMENT_COLORS,
                category_orders={"Index segments": SEGMENT_CATEGORIES},
                text="Proportion",
                title=f"Financial Resilience Distribution – {province} – {year}"
            )
            
            fig.update_traces(
                texttemplate='%{text:.1%}',
                textposition='outside',
                textfont_size=14
            )
            
            fig.update_layout(
                yaxis_tickformat=".0%",
                xaxis_title="",
                yaxis_title="Proportion",
                height=550,
                showlegend=False,
                xaxis_tickangle=0,
                margin=dict(b=120, t=80)
            )
            
            max_val = bar_data['Proportion'].max()
            fig.update_yaxes(range=[0, max_val * 1.15])
            
            add_footer_annotation(fig, y_position=-0.10)
            st.plotly_chart(fig, use_container_width=True)

    # ═══════════════════════════════ LINE CHART ═══════════════════════════════
    elif chart_type == "Trended line chart":
        trend_data = filtered.copy()
        
        if len(selected_years) < 2:
            st.info("📈 Please select at least two survey rounds to see trends over time")
        elif trend_data.empty:
            st.warning("⚠️ No data available for this trend chart selection")
        else:
            multiple_prov = len(selected_provinces) > 1
            
            fig = px.line(
                trend_data,
                x="Survey round",
                y="Proportion",
                color="Index segments",
                line_dash="Province" if multiple_prov else None,
                markers=True,
                color_discrete_map=SEGMENT_COLORS,
                category_orders={
                    "Index segments": SEGMENT_CATEGORIES,
                    "Province": sorted(filtered['Province'].unique())
                },
                title="Financial Resilience Segments Trend Over Time"
            )
            
            fig.update_layout(
                yaxis_tickformat=".0%",
                xaxis_title="Survey Round",
                yaxis_title="Proportion",
                legend_title="Segment" + (" / Province" if multiple_prov else ""),
                height=550,
                hovermode='x unified',
                margin=dict(b=100, t=80)
            )
            
            fig.update_traces(
                mode='lines+markers',
                marker=dict(size=9),
                line=dict(width=3)
            )
            
            # Custom hover template
            fig.update_traces(
                hovertemplate="<b>Segment:</b> %{legendgroup}<br>" +
                              "<b>Province:</b> %{customdata[0]}<br>" +
                              "<b>Survey Round:</b> %{x}<br>" +
                              "<b>Proportion:</b> %{y:.1%}<extra></extra>",
                customdata=trend_data[['Province']].values
            )
            
            add_footer_annotation(fig, y_position=-0.10)
            st.plotly_chart(fig, use_container_width=True)


# In[ ]:


# Add this at the end of your Step 7, after all visualizations (and before the footer if present)
# The download button will provide the current filtered data in CSV format
csv_data = filtered.to_csv(index=False)
st.sidebar.download_button(
    label="📥 Download Filtered Data (CSV)",
    data=csv_data,
    file_name=f"resilience_data_{'-'.join(str(y) for y in selected_years)}.csv",
    mime="text/csv"
)


# In[ ]:


# Step 8: Summary Metrics and Download

if not filtered.empty:
    st.markdown("---")
    st.subheader("📊 Summary Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Total Records", f"{len(filtered):,}")

    with col2:
        st.metric("📅 Survey Rounds", len(filtered['Survey round'].unique()))

    with col3:
        st.metric("📍 Locations", len(filtered['Province'].unique()))

    with col4:
        avg_proportion = filtered.groupby('Index segments')['Proportion'].mean()
        if not avg_proportion.empty:
            dominant_segment = avg_proportion.idxmax()
            st.metric("🏆 Largest Segment", dominant_segment)


