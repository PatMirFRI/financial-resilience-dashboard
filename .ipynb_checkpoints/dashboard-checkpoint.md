# Interactive Financial Resilience Dashboard for Canada

This notebook creates a complete interactive dashboard for visualizing financial resilience data across Canadian provinces. The dashboard includes province/year filters, custom color coding, and professional formatting.

## Setup and Import Libraries

```python
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
import streamlit as st

# Set page config
st.set_page_config(
    page_title="Financial Resilience Dashboard - Canada",
    page_icon="🍁",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stButton>button {
        background-color: #00AEEF;
        color: white;
    }
    .stButton>button:hover {
        background-color: #0090C7;
    }
</style>
""", unsafe_allow_html=True)

# Dashboard Title
st.title("🍁 Financial Resilience Dashboard - Canada")
st.markdown("---")
```

## Load Data

```python
# Load the dataset
@st.cache_data
def load_data():
    dataset = pd.read_excel("Interative-dashboard.xlsx", sheet_name="Index_score")
    segments_data = pd.read_excel("Interative-dashboard.xlsx", sheet_name="Index_segment")
    return dataset, segments_data

dataset, segments_data = load_data()

# Load GeoJSON
@st.cache_data
def load_geojson():
    with open("canada_provinces.geojson", "r") as f:
        geojson = json.load(f)
    return geojson

geojson = load_geojson()
```

## Create Sidebar Filters

```python
# Sidebar for filters
st.sidebar.header("🔍 Filter Options")

# Get unique provinces and years
province_options = ['All provinces'] + sorted(dataset['Province'].dropna().unique().tolist())
year_options = sorted(dataset['Survey round'].dropna().unique().tolist())

# Province selector
selected_province = st.sidebar.selectbox(
    "Select Province or Territory:",
    province_options,
    help="Choose a specific province or 'All provinces' for national view"
)

# Year selector
selected_year = st.sidebar.selectbox(
    "Select Survey Round:",
    year_options,
    help="Choose the time period for the data"
)

# Add a divider
st.sidebar.markdown("---")

# Add information box
st.sidebar.info("""
**Color Legend:**
- 🔴 **Extremely Vulnerable** (0-29.9)
- 🟠 **Financially Vulnerable** (30-49.9)
- 🔵 **Approaching Resilience** (50-69.9)
- 🟦 **Financially Resilient** (70-100)
""")
```

## Filter and Prepare Data

```python
# Filter the data
filtered = dataset.copy()

# Apply year filter first
filtered = filtered[filtered['Survey round'] == selected_year]

# If specific province selected, filter for it
if selected_province != 'All provinces':
    filtered = filtered[filtered['Province'] == selected_province]
    # Also get national data for comparison
    national_data = dataset[(dataset['Survey round'] == selected_year) & (dataset['Province'].isnull())]
else:
    # For all provinces view, exclude national data from map
    filtered = filtered[filtered['Province'].notnull()]
    national_data = dataset[(dataset['Survey round'] == selected_year) & (dataset['Province'].isnull())]

# Round scores to 1 decimal place
filtered['Mean Financial Resilience Score'] = filtered['Mean Financial Resilience Score'].round(1)
```

## Create the Map

```python
# Define custom discrete color scale
def get_color_for_score(score):
    if score < 30:
        return "#C00000"  # Dark Red
    elif score < 50:
        return "#ED175B"  # Reddish Pink
    elif score < 70:
        return "#1E196A"  # Deep Indigo
    else:
        return "#00AEEF"  # Sky Blue

# Create discrete color scale for Plotly
colorscale = [
    [0.0, "#C00000"],     # 0-30: Dark Red
    [0.3, "#C00000"],
    [0.3, "#ED175B"],     # 30-50: Reddish Pink
    [0.5, "#ED175B"],
    [0.5, "#1E196A"],     # 50-70: Deep Indigo
    [0.7, "#1E196A"],
    [0.7, "#00AEEF"],     # 70-100: Sky Blue
    [1.0, "#00AEEF"]
]

# Main content area - create columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    # Create the choropleth map
    if not filtered.empty:
        fig = px.choropleth(
            filtered,
            geojson=geojson,
            locations="Province",
            featureidkey="properties.name",
            color="Mean Financial Resilience Score",
            hover_name="Province",
            hover_data={"Mean Financial Resilience Score": ":.1f"},
            color_continuous_scale=colorscale,
            range_color=[0, 100],
            projection="natural earth",
            title=f"Financial Resilience Index by Province — {selected_year}"
        )
        
        # Update layout
        fig.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=False,
                projection_type='natural earth',
                bgcolor="rgba(0,0,0,0)",
                center=dict(lat=60, lon=-96),
                projection_scale=3
            ),
            coloraxis_colorbar=dict(
                title="Score",
                tickvals=[15, 40, 60, 85],
                ticktext=[
                    "Extremely<br>Vulnerable",
                    "Financially<br>Vulnerable",
                    "Approaching<br>Resilience",
                    "Financially<br>Resilient"
                ],
                tickmode='array',
                x=1.02
            ),
            height=600,
            margin=dict(l=0, r=0, t=50, b=50),
            title=dict(
                font=dict(size=20, family="Arial, sans-serif"),
                x=0.5,
                xanchor='center'
            ),
            annotations=[
                dict(
                    text="© 2025 Financial Resilience Society dba Financial Resilience Institute. All Rights Reserved.",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.98,
                    y=0.02,
                    xanchor="right",
                    yanchor="bottom",
                    font=dict(
                        size=10,
                        color="#888888",
                        family="Arial, sans-serif"
                    )
                )
            ]
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        
        # Display the map
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")
```

## Display Statistics and Additional Information

```python
with col2:
    st.markdown("### 📊 Key Statistics")
    
    # Display national score if available
    if not national_data.empty and selected_province == 'All provinces':
        national_score = national_data['Mean Financial Resilience Score'].iloc[0]
        st.metric(
            label="🇨🇦 Canada-wide Score",
            value=f"{national_score:.1f}",
            delta=None
        )
        st.markdown("---")
    
    # Provincial statistics
    if not filtered.empty:
        if selected_province == 'All provinces':
            # Show top and bottom provinces
            st.markdown("**Top 3 Provinces:**")
            top_provinces = filtered.nlargest(3, 'Mean Financial Resilience Score')[['Province', 'Mean Financial Resilience Score']]
            for _, row in top_provinces.iterrows():
                score = row['Mean Financial Resilience Score']
                color = get_color_for_score(score)
                st.markdown(f"<span style='color: {color}'>●</span> {row['Province']}: **{score:.1f}**", unsafe_allow_html=True)
            
            st.markdown("**Bottom 3 Provinces:**")
            bottom_provinces = filtered.nsmallest(3, 'Mean Financial Resilience Score')[['Province', 'Mean Financial Resilience Score']]
            for _, row in bottom_provinces.iterrows():
                score = row['Mean Financial Resilience Score']
                color = get_color_for_score(score)
                st.markdown(f"<span style='color: {color}'>●</span> {row['Province']}: **{score:.1f}**", unsafe_allow_html=True)
            
            # Average score
            avg_score = filtered['Mean Financial Resilience Score'].mean()
            st.markdown("---")
            st.metric(
                label="Average Provincial Score",
                value=f"{avg_score:.1f}"
            )
        else:
            # Show selected province score
            province_score = filtered['Mean Financial Resilience Score'].iloc[0]
            st.metric(
                label=f"{selected_province} Score",
                value=f"{province_score:.1f}"
            )
            
            # Show comparison to national if available
            if not national_data.empty:
                national_score = national_data['Mean Financial Resilience Score'].iloc[0]
                diff = province_score - national_score
                st.metric(
                    label="vs. National Average",
                    value=f"{national_score:.1f}",
                    delta=f"{diff:+.1f}"
                )
```

## Create Data Table

```python
# Data table section
st.markdown("---")
st.markdown("### 📋 Detailed Data View")

# Prepare data for display
display_data = filtered[['Province', 'Mean Financial Resilience Score']].copy()
display_data.columns = ['Province/Territory', 'Resilience Score']

# Add color coding
display_data['Category'] = display_data['Resilience Score'].apply(
    lambda x: 'Extremely Vulnerable' if x < 30 
    else 'Financially Vulnerable' if x < 50 
    else 'Approaching Resilience' if x < 70 
    else 'Financially Resilient'
)

# Sort by score
display_data = display_data.sort_values('Resilience Score', ascending=False)

# Display options
col3, col4 = st.columns(2)
with col3:
    show_segments = st.checkbox("Show population segments", value=False)
with col4:
    # Download button for filtered data
    csv = display_data.to_csv(index=False)
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name=f"financial_resilience_{selected_year.replace(' ', '_')}.csv",
        mime="text/csv"
    )

# Display the data table
st.dataframe(
    display_data.style.format({'Resilience Score': '{:.1f}'}),
    use_container_width=True,
    height=400
)
```

## Show Segment Distribution (Optional)

```python
if show_segments and selected_province != 'All provinces':
    st.markdown("---")
    st.markdown("### 📊 Population Distribution by Resilience Category")
    
    # Filter segments data
    segments_filtered = segments_data[
        (segments_data['Province'] == selected_province) & 
        (segments_data['Survey round'] == selected_year)
    ]
    
    if not segments_filtered.empty:
        # Create pie chart
        fig_pie = px.pie(
            segments_filtered,
            values='Proportion',
            names='Index segments',
            color='Index segments',
            color_discrete_map={
                'Extremely Vulnerable': '#C00000',
                'Financially Vulnerable': '#ED175B',
                'Approaching Resilience': '#1E196A',
                'Financially Resilient': '#00AEEF'
            },
            title=f"Population Distribution - {selected_province} ({selected_year})"
        )
        
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(
            height=400,
            showlegend=False,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
```

## Footer

```python
# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px;'>
    © 2025 Financial Resilience Society dba Financial Resilience Institute. All Rights Reserved.<br>
    Dashboard created for transparency and data-driven impact.
    </div>
    """,
    unsafe_allow_html=True
)
```

## Running the Dashboard

Save this code as `dashboard.py` and run it using:

```bash
streamlit run dashboard.py
```

Make sure you have:
1. The Excel file `Interative-dashboard.xlsx` in the same directory
2. The GeoJSON file `canada_provinces.geojson` in the same directory
3. All required packages installed: `pandas`, `plotly`, `streamlit`, `openpyxl`

The dashboard will open in your browser and provide an interactive experience for exploring financial resilience data across Canada.