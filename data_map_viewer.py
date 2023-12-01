import streamlit as st
import pandas as pd
import geopandas
import folium
from folium import plugins
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Data Map Viewer",
    page_icon="🗺️",
    layout="wide",
)


@st.cache_data
def load_data(data):
    df = pd.read_csv(data)
    lowercase = lambda x: str(x).lower()
    df.rename(lowercase, axis="columns", inplace=True)
    st.session_state.rows = df.shape[0]

    columns = df.columns.tolist()

    for i in range(len(columns)):
        col = columns[i]

        # Rename latitude/longitude columns
        if "lon" in col:
            df.rename(columns={col: "longitude"}, inplace=True)

        if "lat" in col:
            df.rename(columns={col: "latitude"}, inplace=True)

    # Drop rows with missing values in the latitude or longitude columns
    if "latitude" in df.columns:
        df.dropna(subset=["latitude"], inplace=True)

    if "longitude" in df.columns:
        df.dropna(subset=["longitude"], inplace=True)

    return df


@st.cache_data
def load_geometries(df):
    geometry = geopandas.points_from_xy(df.longitude, df.latitude)
    geo_df = geopandas.GeoDataFrame(df[["latitude", "longitude"]], geometry=geometry)

    return geo_df


df = None

if "rows" not in st.session_state:
    st.session_state.rows = 0

# Initialize submit button state
if "clicked" not in st.session_state:
    st.session_state.clicked = False


def click_submit():
    st.session_state.clicked = True


def url_input():
    st.session_state.clicked = False


st.title("🗺️ Data Map Viewer")

st.write("Import Data")
tab1, tab2 = st.tabs(["By File", "By URL"])

with tab1:
    uploaded_file = st.file_uploader("Choose a .csv file", type="csv")

with tab2:
    if uploaded_file is None:
        data_url = st.text_input("Data File URL", on_change=url_input)
        st.button("Submit", on_click=click_submit, type="primary")
    else:
        data_url = st.text_input("Data File URL", on_change=url_input, disabled=True)
        st.button("Submit", on_click=click_submit, type="primary", disabled=True)
        st.info("To enter a URL, remove the uploaded file", icon="ℹ️")

if uploaded_file is not None:
    df = load_data(uploaded_file)
elif st.session_state.clicked and len(data_url) > 0:
    df = load_data(data_url)

# Display the maps when the data is loaded
if df is not None:
    na_values = st.session_state.rows - df.shape[0]
    nrows = st.slider("Observations", 0, df.shape[0], min(df.shape[0], 10000))

    column_gap = "medium"

    top_left, top_right = st.columns([1, 1], gap=column_gap)

    with top_left:
        # Map with scatterplot
        st.map(df.head(nrows), use_container_width=True)
    with top_right:
        st.subheader("🔭 Dataset Preview")
        st.dataframe(df.head(nrows), height=405)
        if na_values > 0:
            st.write(
                "{} rows with NA values in the Latitude/Longitude column were removed.".format(
                    na_values
                )
            )

    bottom_left, bottom_right = st.columns([1, 1], gap=column_gap)

    map_height = 500
    zoom_level = 2

    location = df[["latitude", "longitude"]].median()
    geo_df = load_geometries(df.head(nrows))
    points = [[point.xy[1][0], point.xy[0][0]] for point in geo_df.geometry]

    with bottom_left:
        # Heatmap
        map = folium.Map(
            location=[location.latitude, location.longitude],
            tiles="Cartodb dark_matter",
            zoom_start=zoom_level,
            control_scale=True,
        )

        plugins.HeatMap(points).add_to(map)
        st_folium(
            map, use_container_width=True, height=map_height, center="center", key="1"
        )

    with bottom_right:
        # Clustered point map

        m = folium.Map(
            location=[location.latitude, location.longitude],
            tiles="cartodbpositron",
            zoom_start=zoom_level,
            control_scale=True,
        )

        marker_cluster = plugins.MarkerCluster(points)

        marker_cluster.add_to(m)

        st_folium(
            m, use_container_width=True, height=map_height, center="center", key="2"
        )
