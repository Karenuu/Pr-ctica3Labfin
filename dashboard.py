import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(page_title="Panel Financiero", layout="wide", page_icon="💰")

# Add custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    data_path = 'Data/'
    try:
        factsale = pd.read_csv(f'{data_path}FactSale.csv')
        dimcustomer = pd.read_csv(f'{data_path}DimCostumer.csv')
        dimcity = pd.read_csv(f'{data_path}DimCity.csv')
        dimdate = pd.read_csv(f'{data_path}DimDate.csv')
        dimemployee = pd.read_csv(f'{data_path}DimEmployee.csv')
        dimstockitem = pd.read_csv(f'{data_path}DimStockItem.csv')

        # Merge all dataframes
        merged_df = factsale.merge(dimcustomer, on='Customer Key', how='left', suffixes=('', '_customer')) \
                        .merge(dimcity, on='City Key', how='left', suffixes=('', '_city')) \
                        .merge(dimemployee, left_on='Salesperson Key', right_on='Employee Key', how='left', suffixes=('', '_employee')) \
                        .merge(dimstockitem, on='Stock Item Key', how='left', suffixes=('', '_stock')) \
                        .merge(dimdate, left_on='Invoice Date Key', right_on='Date', how='left')
        
        return merged_df
    except FileNotFoundError as e:
        st.error("Error: One or more data files not found. Please check the file paths.")
        raise e

# State abbreviations mapping
state_abbreviations = {
    'Alaska': 'AK', 'California': 'CA', 'Hawaii': 'HI', 'Nevada': 'NV',
    'Oregon': 'OR', 'Washington': 'WA'
}

def filter_data(df, selected_state, selected_year):
    filtered_df = df.copy()
    
    if selected_state != 'All':
        filtered_df = filtered_df[filtered_df['State Province'] == selected_state]
    if selected_year != 'All':
        filtered_df = filtered_df[filtered_df['Calendar Year'] == int(selected_year)]
    
    return filtered_df

def main():
    # Title
    st.title("🎯 Panel Financiero")
    
    # Load data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return

    # Sidebar filters
    st.sidebar.header("Filtros")
    
    # Get unique states and years
    states = ['Todos'] + sorted([x for x in df['State Province'].unique() if pd.notna(x)])
    years = ['Todos'] + sorted([int(x) for x in df['Calendar Year'].unique() if pd.notna(x)])
    
    # Create filters
    selected_state = st.sidebar.selectbox('Seleccionar Estado:', states)
    selected_year = st.sidebar.selectbox('Seleccionar Año:', years)
    
    # Filter data based on selection
    filtered_df = filter_data(df, selected_state if selected_state != 'Todos' else 'All', 
                            selected_year if selected_year != 'Todos' else 'All')
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Display metrics
    with col1:
        unique_colors = len(filtered_df['Color'].dropna().unique())
        st.metric("Colores Únicos", unique_colors)
    
    with col2:
        avg_unit_price = round(filtered_df['Unit Price'].mean(), 2)
        st.metric("Precio Unitario Promedio", f"${avg_unit_price:,.2f}")
    
    with col3:
        unique_sizes = len(filtered_df['Size'].dropna().unique())
        st.metric("Tallas Únicas", unique_sizes)
    
    with col4:
        total_revenue = filtered_df['Unit Price'].sum()
        st.metric("Ingresos Totales", f"${total_revenue:,.2f}")
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Total Revenue by State Map
        state_revenue = filtered_df.groupby('State Province')['Unit Price'].sum().reset_index()
        state_revenue['State Abbrev'] = state_revenue['State Province'].map(state_abbreviations)
        
        fig_map = px.choropleth(
            state_revenue,
            locations='State Abbrev',
            locationmode='USA-states',
            color='Unit Price',
            scope='usa',
            color_continuous_scale='Viridis',
            title='Ingresos Totales por Estado',
            labels={'Unit Price': 'Ingresos ($)'}
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
        # Sales by Size Pie Chart
        size_sales = filtered_df.groupby(filtered_df['Size'].fillna('Sin Talla'))['Unit Price'].sum()
        fig_size = px.pie(
            values=size_sales.values,
            names=size_sales.index,
            title='Distribución de Ventas por Talla'
        )
        st.plotly_chart(fig_size, use_container_width=True)
    
    with col2:
        # Median Tax by State
        state_tax = filtered_df.groupby('State Province')['Tax Amount'].median().reset_index()
        fig_tax = px.bar(
            state_tax,
            y='State Province',
            x='Tax Amount',
            title='Impuesto Mediano por Estado',
            labels={'Tax Amount': 'Impuesto ($)', 'State Province': 'Estado'},
            orientation='h'
        )
        st.plotly_chart(fig_tax, use_container_width=True)
          # Brand Sales Distribution as a Ring Chart
        brand_sales = filtered_df.groupby(filtered_df['Brand'].fillna('Sin Marca'))['Unit Price'].sum()
        fig_brand = go.Figure(data=[go.Pie(
            values=brand_sales.values,
            labels=brand_sales.index,
            hole=0.4,  # This makes it a ring/donut chart
            title='Distribución de Ventas por Marca'
        )])
        fig_brand.update_layout(
            title_text='Distribución de Ventas por Marca', 
            title_x=0.5,
            showlegend=True
        )
        st.plotly_chart(fig_brand, use_container_width=True)

if __name__ == "__main__":
    main()
