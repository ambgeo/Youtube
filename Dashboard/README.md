# Dashboard Climatológico - Precipitação e Temperatura

Dashboard interativo desenvolvido com Streamlit e Folium para visualização de dados de precipitação acumulada e temperatura média por estado brasileiro.

## 📋 Funcionalidades

- **Mapa Interativo de Precipitação**: Visualização geográfica da precipitação anual por estado com cores graduadas
- **Mapa Interativo de Temperatura**: Visualização geográfica da temperatura média por estado
- **Gráficos Comparativos**: Gráficos de barras e scatter plot para análise dos dados
- **Tabela de Dados**: Visualização completa dos dados com opção de download
- **Estatísticas**: Valores médios e extremos exibidos na barra lateral

## 🚀 Instalação

1. Clone ou baixe este repositório

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 📦 Dependências

- streamlit >= 1.28.0
- folium >= 0.14.0
- streamlit-folium >= 0.15.0
- pandas >= 2.0.0
- requests >= 2.31.0
- branca >= 0.6.0

## 🎯 Uso

Execute o dashboard com o seguinte comando:

```bash
streamlit run dashboard.py
```

O dashboard será aberto automaticamente no seu navegador padrão. Se não abrir, acesse `http://localhost:8501`

## 📊 Estrutura dos Dados

O arquivo CSV deve conter as seguintes colunas:
- `SIGLA_UF`: Sigla do estado (AC, AL, AP, etc.)
- `Precipitacao_Anual_mm`: Precipitação anual em milímetros
- `Temperatura_Media_C`: Temperatura média em graus Celsius

## 🗺️ Dados Geoespaciais

O dashboard utiliza dados GeoJSON do IBGE através do serviço WFS:
- **Fonte**: Instituto Brasileiro de Geografia e Estatística (IBGE)
- **URL do serviço**: GeoServer IBGE - Estados com nomes
- Os dados são carregados automaticamente e em cache por 1 hora

## 📝 Notas

- O dashboard faz o merge dos dados do CSV com o GeoJSON do IBGE usando o campo `nm_uf` (nome do estado)
- A busca é case-insensitive e normaliza acentos para maior robustez
- Os mapas são interativos e permitem zoom, pan e visualização de tooltips ao passar o mouse

## 🔧 Solução de Problemas

Se algum estado não aparecer no mapa:
- Verifique se a sigla do estado no CSV está correta
- Certifique-se de que o nome do estado corresponde ao utilizado pelo IBGE
- O dashboard mostrará um aviso caso algum estado do GeoJSON não seja encontrado no CSV

