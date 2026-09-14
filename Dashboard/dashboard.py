import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import json
from branca.colormap import LinearColormap

# Configuração da página
st.set_page_config(
    page_title="Dashboard Climatológico - Precipitação e Temperatura",
    page_icon="🌦️",
    layout="wide"
)

# Título do dashboard
st.title("🌦️ Dashboard Climatológico - Precipitação e Temperatura por Estado")
st.markdown("---")

# Função para carregar dados do CSV
@st.cache_data
def load_csv_data():
    """Carrega os dados do CSV"""
    try:
        df = pd.read_csv("dados_precipitacao_temperatura_estados.csv")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return None

# Função para carregar GeoJSON do IBGE
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_geojson():
    """Carrega o GeoJSON do IBGE"""
    url = "https://geoservicos.ibge.gov.br/geoserverIBGE/CGMAT/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=CGMAT%3Apbqg22_02_Estado_NomUF&outputFormat=application%2Fjson&maxFeatures=600000"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        geojson_data = response.json()
        return geojson_data
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON do IBGE: {e}")
        return None

# Função para normalizar strings (remover acentos e converter para minúsculas)
def normalize_string(s):
    """Normaliza string removendo acentos e convertendo para minúsculas"""
    import unicodedata
    if not s:
        return ''
    # Remove acentos
    nfkd = unicodedata.normalize('NFKD', str(s))
    ascii_str = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    return ascii_str.lower().strip()

# Função para fazer merge dos dados
def merge_data_with_geojson(df, geojson_data):
    """Faz o merge dos dados do CSV com o GeoJSON"""
    # Criar um dicionário de mapeamento de sigla para nome
    sigla_para_nome = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
        'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
        'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    
    # Adicionar coluna de nome do estado ao DataFrame
    df['nm_uf'] = df['SIGLA_UF'].map(sigla_para_nome)
    
    # Criar um dicionário de dados por estado (normalizado para busca)
    dados_dict = {}
    dados_dict_normalized = {}
    for idx, row in df.iterrows():
        nome_uf = row['nm_uf']
        dados_dict[nome_uf] = {
            'SIGLA_UF': row['SIGLA_UF'],
            'Precipitacao_Anual_mm': row['Precipitacao_Anual_mm'],
            'Temperatura_Media_C': row['Temperatura_Media_C']
        }
        # Também criar versão normalizada para busca flexível
        dados_dict_normalized[normalize_string(nome_uf)] = dados_dict[nome_uf]
    
    # Coletar estados do GeoJSON que não foram encontrados (para debug)
    estados_nao_encontrados = set()
    
    # Adicionar dados às features do GeoJSON
    for feature in geojson_data.get('features', []):
        nm_uf_geojson = feature['properties'].get('nm_uf', '')
        nm_uf_normalized = normalize_string(nm_uf_geojson)
        
        # Tentar match exato primeiro
        if nm_uf_geojson in dados_dict:
            feature['properties'].update(dados_dict[nm_uf_geojson])
        # Tentar match normalizado
        elif nm_uf_normalized in dados_dict_normalized:
            feature['properties'].update(dados_dict_normalized[nm_uf_normalized])
        else:
            # Se não encontrar, adicionar valores vazios
            feature['properties']['Precipitacao_Anual_mm'] = None
            feature['properties']['Temperatura_Media_C'] = None
            if nm_uf_geojson:
                estados_nao_encontrados.add(nm_uf_geojson)
    
    # Mostrar aviso se algum estado não foi encontrado
    if estados_nao_encontrados:
        st.warning(f"Estados no GeoJSON não encontrados no CSV: {', '.join(sorted(estados_nao_encontrados))}")
    
    return geojson_data

# Função para criar mapa de precipitação
def create_precipitation_map(geojson_data):
    """Cria mapa Folium com dados de precipitação"""
    # Calcular valores mínimo e máximo para o colormap
    valores = [f['properties'].get('Precipitacao_Anual_mm') 
               for f in geojson_data['features'] 
               if f['properties'].get('Precipitacao_Anual_mm') is not None]
    
    if not valores:
        st.warning("Nenhum dado de precipitação encontrado")
        return None
    
    vmin, vmax = min(valores), max(valores)
    
    # Criar colormap
    colormap = LinearColormap(
        colors=['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', 
                '#41ab5d', '#238b45', '#006d2c', '#00441b'],
        vmin=vmin,
        vmax=vmax
    )
    
    # Criar mapa
    m = folium.Map(
        location=[-14.2350, -51.9253],  # Centro do Brasil
        zoom_start=4,
        tiles='OpenStreetMap'
    )
    
    # Adicionar camada de estados com dados de precipitação
    folium.GeoJson(
        geojson_data,
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties'].get('Precipitacao_Anual_mm', 0)),
            'fillOpacity': 0.7,
            'color': 'black',
            'weight': 1.5,
            'dashArray': '5, 5'
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['nm_uf', 'SIGLA_UF', 'Precipitacao_Anual_mm'],
            aliases=['Estado:', 'UF:', 'Precipitação Anual (mm):'],
            localize=True
        ),
        popup=folium.GeoJsonPopup(
            fields=['nm_uf', 'SIGLA_UF', 'Precipitacao_Anual_mm', 'Temperatura_Media_C'],
            aliases=['Estado:', 'UF:', 'Precipitação Anual (mm):', 'Temperatura Média (°C):'],
            localize=True
        )
    ).add_to(m)
    
    # Adicionar legenda
    colormap.add_to(m)
    colormap.caption = 'Precipitação Anual (mm)'
    
    return m

# Função para criar mapa de temperatura
def create_temperature_map(geojson_data):
    """Cria mapa Folium com dados de temperatura"""
    # Calcular valores mínimo e máximo para o colormap
    valores = [f['properties'].get('Temperatura_Media_C') 
               for f in geojson_data['features'] 
               if f['properties'].get('Temperatura_Media_C') is not None]
    
    if not valores:
        st.warning("Nenhum dado de temperatura encontrado")
        return None
    
    vmin, vmax = min(valores), max(valores)
    
    # Criar colormap (quente para frio)
    colormap = LinearColormap(
        colors=['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8',
                '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'],
        vmin=vmin,
        vmax=vmax
    )
    
    # Criar mapa
    m = folium.Map(
        location=[-14.2350, -51.9253],  # Centro do Brasil
        zoom_start=4,
        tiles='OpenStreetMap'
    )
    
    # Adicionar camada de estados com dados de temperatura
    folium.GeoJson(
        geojson_data,
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties'].get('Temperatura_Media_C', 0)),
            'fillOpacity': 0.7,
            'color': 'black',
            'weight': 1.5,
            'dashArray': '5, 5'
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['nm_uf', 'SIGLA_UF', 'Temperatura_Media_C'],
            aliases=['Estado:', 'UF:', 'Temperatura Média (°C):'],
            localize=True
        ),
        popup=folium.GeoJsonPopup(
            fields=['nm_uf', 'SIGLA_UF', 'Precipitacao_Anual_mm', 'Temperatura_Media_C'],
            aliases=['Estado:', 'UF:', 'Precipitação Anual (mm):', 'Temperatura Média (°C):'],
            localize=True
        )
    ).add_to(m)
    
    # Adicionar legenda
    colormap.add_to(m)
    colormap.caption = 'Temperatura Média (°C)'
    
    return m

# Carregar dados
with st.spinner("Carregando dados..."):
    df = load_csv_data()
    geojson_data = load_geojson()

if df is not None and geojson_data is not None:
    # Fazer merge dos dados
    geojson_merged = merge_data_with_geojson(df, geojson_data)
    
    # Sidebar com estatísticas
    st.sidebar.header("📊 Estatísticas")
    
    st.sidebar.metric(
        "Precipitação Média",
        f"{df['Precipitacao_Anual_mm'].mean():.1f} mm"
    )
    st.sidebar.metric(
        "Temperatura Média",
        f"{df['Temperatura_Media_C'].mean():.1f} °C"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("📈 Valores Extremos")
    
    # Estado com maior precipitação
    max_prec = df.loc[df['Precipitacao_Anual_mm'].idxmax()]
    st.sidebar.write(f"**Maior Precipitação:** {max_prec['SIGLA_UF']} - {max_prec['Precipitacao_Anual_mm']} mm")
    
    # Estado com menor precipitação
    min_prec = df.loc[df['Precipitacao_Anual_mm'].idxmin()]
    st.sidebar.write(f"**Menor Precipitação:** {min_prec['SIGLA_UF']} - {min_prec['Precipitacao_Anual_mm']} mm")
    
    # Estado com maior temperatura
    max_temp = df.loc[df['Temperatura_Media_C'].idxmax()]
    st.sidebar.write(f"**Maior Temperatura:** {max_temp['SIGLA_UF']} - {max_temp['Temperatura_Media_C']} °C")
    
    # Estado com menor temperatura
    min_temp = df.loc[df['Temperatura_Media_C'].idxmin()]
    st.sidebar.write(f"**Menor Temperatura:** {min_temp['SIGLA_UF']} - {min_temp['Temperatura_Media_C']} °C")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa - Precipitação", "🌡️ Mapa - Temperatura", "📊 Gráficos", "📋 Tabela de Dados"])
    
    with tab1:
        st.header("Mapa de Precipitação Acumulada por Estado")
        st.markdown("Visualização da precipitação anual em milímetros por estado brasileiro")
        
        map_prec = create_precipitation_map(geojson_merged)
        if map_prec:
            st_folium(map_prec, width=1200, height=600)
    
    with tab2:
        st.header("Mapa de Temperatura Média por Estado")
        st.markdown("Visualização da temperatura média em graus Celsius por estado brasileiro")
        
        map_temp = create_temperature_map(geojson_merged)
        if map_temp:
            st_folium(map_temp, width=1200, height=600)
    
    with tab3:
        st.header("Gráficos Comparativos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Precipitação Anual por Estado")
            df_sorted_prec = df.sort_values('Precipitacao_Anual_mm', ascending=True)
            st.bar_chart(df_sorted_prec.set_index('SIGLA_UF')['Precipitacao_Anual_mm'])
        
        with col2:
            st.subheader("Temperatura Média por Estado")
            df_sorted_temp = df.sort_values('Temperatura_Media_C', ascending=True)
            st.bar_chart(df_sorted_temp.set_index('SIGLA_UF')['Temperatura_Media_C'])
        
        st.subheader("Relação Precipitação vs Temperatura")
        st.scatter_chart(
            df,
            x='Temperatura_Media_C',
            y='Precipitacao_Anual_mm',
            size='Precipitacao_Anual_mm',
            color='SIGLA_UF'
        )
    
    with tab4:
        st.header("Tabela Completa de Dados")
        st.dataframe(
            df.sort_values('SIGLA_UF'),
            use_container_width=True,
            hide_index=True
        )
        
        # Opção de download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="dados_precipitacao_temperatura_estados.csv",
            mime="text/csv"
        )

else:
    st.error("Não foi possível carregar os dados. Verifique se o arquivo CSV está presente e se há conexão com a internet para carregar o GeoJSON do IBGE.")

