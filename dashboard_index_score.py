#!/usr/bin/env python
# coding: utf-8


# In[ ]:

# Step 1: Setup and Imports
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Financial Resilience Dashboard - Canada", page_icon="🍁", layout="wide")


# In[ ]:


# Step 2: Data and GeoJSON Loading

@st.cache_data
def load_data():
    dataset = pd.read_excel("Interative dashboard.xlsx", sheet_name="Index_score")
    segments_data = pd.read_excel("Interative dashboard.xlsx", sheet_name="Index_segment")
    return dataset, segments_data

@st.cache_data
def load_geojson():
    with open("canada_provinces.geojson", "r") as f:
        geojson = json.load(f)
    return geojson

dataset, segments_data = load_data()
geojson = load_geojson()


# In[ ]:


# Step 3: Sidebar - Year and Province(s) Selection

st.sidebar.header("🔍 Filter Options")
year_options = sorted(dataset['Survey round'].dropna().unique().tolist())
province_options = ['All provinces'] + sorted(dataset['Province'].dropna().unique())

selected_year = st.sidebar.selectbox("Select Survey Round:", year_options)
selected_provinces = st.sidebar.multiselect(
    "Select Province(s) or Territory(ies):",
    province_options,
    default=['All provinces']
)

# Add a divider
st.sidebar.markdown("---")

# Add information box
st.sidebar.markdown("""
<div style='border-radius:8px; padding: 18px 15px 10px 15px; background-color: #E8F4FB; border: 1px solid #BFE1FC; margin-bottom: 20px;'>
<b>Color Legend:</b><br>
<span style='color:#C00000; font-size:22px; vertical-align:middle'>●</span> <b>Extremely Vulnerable</b> (0–30)<br>
<span style='color:#ED175B; font-size:22px; vertical-align:middle'>●</span> <b>Financially Vulnerable</b> (30.0–50)<br>
<span style='color:#1E196A; font-size:22px; vertical-align:middle'>●</span> <b>Approaching Resilience</b> (50.0–70)<br>
<span style='color:#00AEEF; font-size:22px; vertical-align:middle'>●</span> <b>Financially Resilient</b> (70.0–100)
</div>
""", unsafe_allow_html=True)



# In[ ]:


# Step 4: Filtering Data

filtered = dataset[dataset['Survey round'] == selected_year]
# Remove national rows for map
filtered = filtered[filtered['Province'].notnull()]
filtered['Mean Financial Resilience Score'] = filtered['Mean Financial Resilience Score'].round(1)

# Province selection logic
if "All provinces" in selected_provinces or not selected_provinces:
    # Show all provinces
    display_provinces = [f['properties']['name'] for f in geojson['features']]
    provinces_geojson = geojson
    view_mode = 'all'
elif len(selected_provinces) == 1:
    display_provinces = [selected_provinces[0]]
    provinces_geojson = {
        "type": "FeatureCollection",
        "features": [f for f in geojson['features'] if f['properties']['name'] == selected_provinces[0]]
    }
    view_mode = 'single'
else:
    display_provinces = selected_provinces
    provinces_geojson = {
        "type": "FeatureCollection",
        "features": [f for f in geojson['features'] if f['properties']['name'] in selected_provinces]
    }
    view_mode = 'multi'

filtered_map = filtered[filtered['Province'].isin(display_provinces)]


# In[ ]:


# Step 5: Mapping and Color Logic

def score_code(val):
    if pd.isna(val) or val == -1:
        return -1
    elif val < 30:
        return 0
    elif val < 50:
        return 1
    elif val < 70:
        return 2
    else:
        return 3

category_labels = {
    -1: "No Data",
     0: "Extremely Vulnerable",
     1: "Financially Vulnerable",
     2: "Approaching Resilience",
     3: "Financially Resilient"
}
category_colors = {
    -1: "#A6A6A6",  # Gray
     0: "#C00000",  # 0-30: Dark Red
     1: "#ED175B",  # 30-50: Reddish Pink
     2: "#1E196A",  # 50-70: Deep Indigo
     3: "#00AEEF"   # 70-100: Sky Blue
}

z_codes, hover_labels = [], []
for prov in display_provinces:
    row = filtered_map[filtered_map['Province'] == prov]
    if not row.empty:
        val = row['Mean Financial Resilience Score'].values[0]
        code = score_code(val)
        label = f"{prov}<br>Score: {val if not (pd.isna(val) or val==-1) else 'No Data'}<br>{category_labels[code]}"
    else:
        code = -1
        label = f"{prov}<br>No Data"
    z_codes.append(code)
    hover_labels.append(label)

discrete_colorscale = [
    [0.0/4, category_colors[-1]],   # gray ("No Data")
    [1.0/4, category_colors[0]],
    [2.0/4, category_colors[1]],
    [3.0/4, category_colors[2]],
    [4.0/4, category_colors[3]],
]


# In[1]:


# Step 6: Map and Zoom Logic
col1, col2 = st.columns([6, 2])

with col1:
    fig = go.Figure(go.Choropleth(
        geojson=provinces_geojson,
        locations=display_provinces,
        z=z_codes,
        featureidkey="properties.name",
        text=hover_labels,
        hoverinfo="text",
        showscale=False,
        colorscale=discrete_colorscale,
        zmin=-1,
        zmax=3,
        marker_line_color='white',
        marker_line_width=0.5
    ))

    # Smart zooming with conic conformal projection
    if view_mode == 'single' and provinces_geojson['features']:
        try:
            from shapely.geometry import shape
            selected_feat = provinces_geojson['features'][0]
            centroid = shape(selected_feat['geometry']).centroid
            fig.update_geos(
                fitbounds="locations", visible=False,
                center={"lat": centroid.y, "lon": centroid.x},
                projection_type="conic conformal",
                projection_scale=10
            )
        except Exception:
            fig.update_geos(
                fitbounds="locations", visible=False,
                projection_type="conic conformal",
                projection_scale=10
            )
    else:
        fig.update_geos(
            fitbounds="locations", visible=False,
            projection_type="conic conformal"
        )

    fig.update_layout(
        title=dict(
            text=f"Provincial Mean Financial Resilience Score — {selected_year}",
            font=dict(size=20, family="Avenir, sans-serif"),
            x=0.5, xanchor='center'
        ),
        height=600,          # Shorter vertical height
        width=2400,          # Much wider map; adjust as desired (900–1400 is typical)
        autosize=False,      # Explicit sizing
        margin=dict(l=0, r=0, t=30, b=10),
        annotations=[
            dict(
                text="© 2025 Financial Resilience Institute. All Rights Reserved.",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.98, y=0.02,
                xanchor="right", yanchor="bottom",
                font=dict(size=10, color="#888888", family="Avenir, sans-serif")
            )
        ]
    )
    st.plotly_chart(fig, use_container_width=True)


# In[ ]:


# Step 7: Statistics & Data Table

with col2:
    st.markdown("### 📊 Key Statistics")

    # Canada-wide comparison
    national_data = dataset[(dataset['Survey round'] == selected_year) & (dataset['Province'].isnull())]
    if not national_data.empty and ("All provinces" in selected_provinces or not selected_provinces):
        national_score = national_data['Mean Financial Resilience Score'].iloc[0]
        st.metric("🇨🇦 Canada-wide Score", f"{national_score:.1f}")

    st.markdown("---")
    if not filtered_map.empty:
        # Show top and bottom when many; else metrics for one
        if ("All provinces" in selected_provinces or not selected_provinces) or len(display_provinces) > 3:
            st.markdown("**Top 3 Provinces:**")
            top_provinces = filtered_map.nlargest(3, 'Mean Financial Resilience Score')[['Province', 'Mean Financial Resilience Score']]
            for _, row in top_provinces.iterrows():
                st.markdown(f"● {row['Province']}: **{row['Mean Financial Resilience Score']:.1f}**", unsafe_allow_html=True)
            st.markdown("**Bottom 3 Provinces:**")
            bottom_provinces = filtered_map.nsmallest(3, 'Mean Financial Resilience Score')[['Province', 'Mean Financial Resilience Score']]
            for _, row in bottom_provinces.iterrows():
                st.markdown(f"● {row['Province']}: **{row['Mean Financial Resilience Score']:.1f}**", unsafe_allow_html=True)
            avg_score = filtered_map['Mean Financial Resilience Score'].mean()
            st.metric("Average Provincial Score", f"{avg_score:.1f}")
        else:
            score = filtered_map['Mean Financial Resilience Score'].iloc[0]
            st.metric(f"{display_provinces[0]} Score", f"{score:.1f}")
            if not national_data.empty:
                national_score = national_data['Mean Financial Resilience Score'].iloc[0]
                diff = score - national_score
                st.metric("vs. National Average", f"{national_score:.1f}", delta=f"{diff:+.1f}")


# Now add the download button
    csv = filtered_map.to_csv(index=False)
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name=f"financial_resilience_{selected_year.replace(' ', '_')}.csv",
        mime="text/csv"
    )


# In[ ]:


# Step 8: Data Table and Download Option

#st.markdown("---")
# st.markdown("### 📋 Detailed Data View")
#
# table_data = filtered_map[['Province', 'Mean Financial Resilience Score']].copy()
# table_data.columns = ['Province/Territory', 'Resilience Score']
# def score_cat(x):
#     if pd.isna(x): return "No Data"
#     elif x < 30: return "Extremely Vulnerable"
#     elif x < 50: return "Financially Vulnerable"
#     elif x < 70: return "Approaching Resilience"
#     else: return "Financially Resilient"
# table_data['Category'] = table_data['Resilience Score'].apply(score_cat)
# table_data = table_data.sort_values('Resilience Score', ascending=False)
#
# col3, col4 = st.columns(2)
# with col3:
#     show_segments = st.checkbox("Show population segments", value=False)
# with col4:
#     csv = table_data.to_csv(index=False)
#    st.download_button(
#        label="📥 Download Data (CSV)",
#        data=csv,
#        file_name=f"financial_resilience_{selected_year.replace(' ', '_')}.csv",
#        mime="text/csv"
#    )

#st.dataframe(table_data.style.format({'Resilience Score': '{:.1f}'}), use_container_width=True, height=400)


# In[ ]:


show_segments = st.sidebar.checkbox("Show population segments pie chart", value=False)

# Step 9: Segment Distribution Pie Chart

if show_segments and (
    ("All provinces" not in selected_provinces or len(selected_provinces) == 1)
    and len(display_provinces) == 1
):
    province = display_provinces[0]
    st.markdown("---")
    st.markdown("### 📊 Population Distribution by Resilience Category")
    seg = segments_data[
        (segments_data['Province'] == province) & 
        (segments_data['Survey round'] == selected_year)
    ]
    if not seg.empty:
        import plotly.express as px
        fig_pie = px.pie(
            seg, values='Proportion', names='Index segments',
            color='Index segments',
            color_discrete_map={
                'Extremely Vulnerable': '#C00000',
                'Financially Vulnerable': '#ED175B',
                'Approaching Resilience': '#1E196A',
                'Financially Resilient': '#00AEEF'
            },
            title=f"Population Distribution - {province} ({selected_year})"
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)


# In[ ]:


# Step 10: Footer and Color Legend

st.markdown("---")

