import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pickle
import pandas as pd
import plotly.express as px
import numpy as np

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

# 챔피언별 역할군 승률 데이터 로드
with open("dashboard_data/champion_winrate_by_role.pkl", "rb") as f:
    champion_winrate_by_role = pickle.load(f)

# 옵션 설정
tag_options = [{'label': tag, 'value': tag} for tag in tag_avg_dataframes.keys()]
champion_options = [{'label': name, 'value': name} for name in champion_dataframes.keys()]
position_options = [{'label': position, 'value': position} for position in champion_win_pick_rate.keys()]
sort_options = [
    {'label': '명수 순', 'value': 'default'},
    {'label': '오름차순', 'value': 'ascending'},
    {'label': '내림차순', 'value': 'descending'}
]

# 레이아웃 구성
app.layout = html.Div([
    html.H1("챔피언 성능 및 통계 대시보드", style={'textAlign': 'center', 'color': '#4CAF50'}),
    dcc.Tabs(id="tabs", value='tab-1', children=[
        # 탭 1: 챔피언 성능 대시보드
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
        
        # 탭 2: 챔피언 승률 및 픽률
        dcc.Tab(label='챔피언 승률 및 픽률', value='tab-2', children=[
            html.Div([
                html.Div([
                    html.Label("포지션 선택"),
                    dcc.Dropdown(id='position-dropdown', options=position_options, value=position_options[0]['value']),
                ], style={'width': '25%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),
                
                html.Div(id='win-pick-rate-table', style={'width': '75%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ]),

        # 탭 3: 챔피언별 역할군 승률
        dcc.Tab(label='챔피언별 상대 역할군에 따른 승률', value='tab-3', children=[
            html.Div([
                html.Div([
                    html.Label("챔피언 선택"),
                    dcc.Dropdown(id='champion-role-dropdown', options=champion_options, value=champion_options[0]['value']),
                    html.Label("정렬 방식"),
                    dcc.Dropdown(id='sort-dropdown', options=sort_options, value='default', clearable=False)
                ], style={'width': '25%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),

                html.Div(id='role-winrate-table', style={'width': '75%', 'padding': '20px'})
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
    stat_name = stat_name if stat_name else '챔피언에게 가한 피해량'
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
    ], style={'width': '100%', 'margin': '20px 0', 'textAlign': 'center', 'border': '1px solid black', 'borderCollapse': 'collapse'})

# 정렬 기준 관리 함수
def sort_winrate(df, sort_order):
    if sort_order == 'default':  # 명수 순서대로 정렬 (1명, 2명, 3명, 4명, 5명)
        return df.sort_index()
    elif sort_order == 'ascending':  # 오름차순 정렬
        return df.sort_values(by='승률', ascending=True)
    elif sort_order == 'descending':  # 내림차순 정렬
        return df.sort_values(by='승률', ascending=False)

# 콜백: 챔피언별 역할군 승률 테이블 업데이트
@app.callback(
    Output('role-winrate-table', 'children'),
    [Input('champion-role-dropdown', 'value'), Input('sort-dropdown', 'value')]
)
def update_role_winrate_table(selected_champion, sort_order):
    tables = []
    
    if selected_champion in champion_winrate_by_role:
        tables.append(html.H3(selected_champion, style={'textAlign': 'center'}))
        
        for role, df in champion_winrate_by_role[selected_champion].items():
            df = df.copy()
            # '데이터 없음'을 NaN으로 변환하여 처리
            df['승률'] = df['승률'].apply(lambda x: round(x * 100, 2) if pd.notna(x) else np.nan)
            df = sort_winrate(df, sort_order)  # 정렬 적용
            sorted_counts = df.index.tolist()

            table = html.Table([
                html.Thead(html.Tr([
                    html.Th("역할군", style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center', 'width': '100px'}),
                    *[html.Th(f"{count}명", style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center', 'width': '100px'}) for count in sorted_counts]
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(role, style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center', 'width': '100px'}),
                        *[html.Td(
                            f"{df['승률'].iloc[i]}%" if pd.notna(df['승률'].iloc[i]) else "데이터 없음",
                            style={
                                'border': '1px solid black',
                                'padding': '5px',
                                'textAlign': 'center',
                                'width': '100px',
                                'backgroundColor': 'white'
                            }
                        ) for i in range(len(df))]
                    ])
                ])
            ], style={'width': '100%', 'margin': '20px 0', 'borderCollapse': 'collapse'})
            
            tables.append(html.Div([table]))
    
    return tables if tables else "선택된 챔피언에 대한 데이터가 없습니다."

# 앱 실행
if __name__ == '__main__':
    app.run_server(debug=True)
