import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pickle
import pandas as pd

# Dash 앱 초기화
app = dash.Dash(__name__)

server = app.server

with open("dashboard_data/champion_stats.pkl", "rb") as f:
    champion_dataframes = pickle.load(f)

with open("dashboard_data/tag_avg_stats.pkl", "rb") as f:
    tag_avg_dataframes = pickle.load(f)

# 태그와 챔피언 옵션 생성
tag_options = [{'label': tag, 'value': tag} for tag in tag_avg_dataframes.keys()]
champion_options = [{'label': name, 'value': name} for name in champion_dataframes.keys()]

# 레이아웃 정의
app.layout = html.Div([
    html.H1("챔피언 성능 대시보드", style={'textAlign': 'center', 'color': '#4CAF50'}),
    
    html.Div([
        html.Label("역할군 선택"),
        dcc.Dropdown(
            id='tag-dropdown',
            options=tag_options,
            value=[],
            multi=True
        ),
        
        html.Label("챔피언 선택"),
        dcc.Dropdown(
            id='champion-dropdown',
            options=champion_options,
            value=[champion_options[0]['value']],
            multi=True
        ),
        
        html.Label("스탯 선택"),
        dcc.Dropdown(
            id='stat-dropdown',
            value='챔피언에게 가한 피해량'  # 기본값 설정
        )
    ], style={'width': '10%', 'display': 'inline-block', 'padding': '10px'}),
    
    html.Div([
        dcc.Graph(id='stat-graph')
    ], style={'width': '70%', 'display': 'inline-block'})
])

# 콜백 정의
@app.callback(
    [Output('stat-dropdown', 'options'), Output('stat-graph', 'figure')],
    [Input('tag-dropdown', 'value'), Input('champion-dropdown', 'value'), Input('stat-dropdown', 'value')]
)
def update_graph(selected_tags, selected_champions, stat_name):
    
    # 기본값 설정
    stat_name = stat_name if stat_name is not None else '챔피언에게 가한 피해량'

    # 스탯 옵션 업데이트: 선택된 태그나 챔피언에 따라 결정
    if selected_tags:
        first_tag = selected_tags[0]
        stats = [{'label': col, 'value': col} for col in tag_avg_dataframes[first_tag].columns if col != '분']
    elif selected_champions:
        first_champion = selected_champions[0]
        stats = [{'label': col, 'value': col} for col in champion_dataframes[first_champion].columns if col != '분']
    else:
        stats = []

    # 선택된 태그와 챔피언들의 데이터 결합하여 그래프 생성
    all_data = []

    # 선택된 태그별 평균 데이터 추가
    for tag in selected_tags:
        if tag in tag_avg_dataframes:
            tag_df = tag_avg_dataframes[tag].copy()
            tag_df['champion_name'] = f"{tag} (Avg)"
            all_data.append(tag_df)

    # 선택된 개별 챔피언 데이터 추가
    for champion_name in selected_champions:
        if champion_name in champion_dataframes:
            champion_df = champion_dataframes[champion_name].copy()
            champion_df['champion_name'] = champion_name
            all_data.append(champion_df)

    # 데이터 결합 후 그래프 생성
    if all_data:
        combined_df = pd.concat(all_data)
        fig = px.line(
            combined_df,
            x='분',
            y=stat_name,
            color='champion_name',
            title=f"성과 지표 - {stat_name}"
        )
        fig.update_layout(xaxis_title="분", yaxis_title=stat_name)
    else:
        fig = {}

    return stats, fig

# 앱 실행
if __name__ == '__main__':
    app.run_server(debug=True)
