import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pickle
import pandas as pd

# Dash 앱 초기화
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# 데이터 로드
with open("dashboard_data/champion_stats.pkl", "rb") as f:
    champion_dataframes = pickle.load(f)

with open("dashboard_data/tag_avg_stats.pkl", "rb") as f:
    tag_avg_dataframes = pickle.load(f)

with open("dashboard_data/champion_win_pick_rate.pkl", "rb") as f:
    champion_win_pick_rate = pickle.load(f)

# 옵션 생성
tag_options = [{'label': tag, 'value': tag} for tag in tag_avg_dataframes.keys()]
champion_options = [{'label': name, 'value': name} for name in champion_dataframes.keys()]
position_options = [{'label': position, 'value': position} for position in champion_win_pick_rate.keys()]

# 레이아웃 구성
app.layout = html.Div([
    html.H1("챔피언 성능 및 통계 대시보드", style={'textAlign': 'center', 'color': '#4CAF50'}),
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='챔피언 성능 대시보드', value='tab-1', children=[
            html.Div([
                html.Div([
                    html.Label("역할군 선택"),
                    dcc.Dropdown(id='tag-dropdown', options=tag_options, value=[], multi=True),
                    html.Label("챔피언 선택"),
                    dcc.Dropdown(id='champion-dropdown', options=champion_options, value=[champion_options[0]['value']], multi=True),
                    html.Label("스탯 선택"),
                    dcc.Dropdown(id='stat-dropdown', value='챔피언에게 가한 피해량')
                ], style={'width': '25%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),
                
                html.Div([
                    dcc.Graph(id='stat-graph', style={'height': '80vh'})
                ], style={'width': '75%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ]),
        
        dcc.Tab(label='챔피언 승률 및 픽률', value='tab-2', children=[
            html.Div([
                html.Div([
                    html.Label("포지션 선택"),
                    dcc.Dropdown(id='position-dropdown', options=position_options, value=position_options[0]['value']),
                ], style={'width': '25%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),
                
                html.Div(id='win-pick-rate-table', style={'width': '75%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ])
    ])
])

# 콜백: 스탯 선택 및 그래프 업데이트
@app.callback(
    [Output('stat-dropdown', 'options'), Output('stat-graph', 'figure')],
    [Input('tag-dropdown', 'value'), Input('champion-dropdown', 'value'), Input('stat-dropdown', 'value')]
)
def update_graph(selected_tags, selected_champions, stat_name):
    stat_name = stat_name if stat_name is not None else '챔피언에게 가한 피해량'
    if selected_tags:
        first_tag = selected_tags[0]
        stats = [{'label': col, 'value': col} for col in tag_avg_dataframes[first_tag].columns if col != '분']
    elif selected_champions:
        first_champion = selected_champions[0]
        stats = [{'label': col, 'value': col} for col in champion_dataframes[first_champion].columns if col != '분']
    else:
        stats = []

    all_data = []
    for tag in selected_tags:
        if tag in tag_avg_dataframes:
            tag_df = tag_avg_dataframes[tag].copy()
            tag_df['champion_name'] = f"{tag} (Avg)"
            all_data.append(tag_df)

    for champion_name in selected_champions:
        if champion_name in champion_dataframes:
            champion_df = champion_dataframes[champion_name].copy()
            champion_df['champion_name'] = champion_name
            all_data.append(champion_df)

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

# 콜백: 포지션 선택에 따른 챔피언 승률/픽률 테이블 업데이트
@app.callback(
    Output('win-pick-rate-table', 'children'),
    [Input('position-dropdown', 'value')]
)
def update_win_pick_rate_table(position):
    df = champion_win_pick_rate[position].copy()
    df = df[df['픽률'] > 0.005]  # 0.5% 이하의 픽률 제외
    df = df.sort_values(by='픽률', ascending=False).reset_index(drop=True)
    df['승률'] = (df['승률'] * 100).round(2).astype(str) + '%'
    df['픽률'] = (df['픽률'] * 100).round(2).astype(str) + '%'
    
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in df.columns])
        ),
        html.Tbody([
            html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(len(df))
        ])
    ], style={'width': '100%', 'margin': '20px 0', 'textAlign': 'center'})

# 앱 실행
if __name__ == '__main__':
    app.run_server(debug=True)
