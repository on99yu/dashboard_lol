import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pickle
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

with open("dashboard_data/winrate_per_champion.pkl", "rb") as f:
    winrate_per_champion = pickle.load(f)

tag_options = [{'label': tag, 'value': tag} for tag in tag_avg_dataframes.keys()]
champion_options = [{'label': name, 'value': name} for name in champion_dataframes.keys()]
position_options = [{'label': position, 'value': position} for position in champion_win_pick_rate.keys()]
role_options = [{'label': role, 'value': role} for role in champion_winrate_by_role[champion_options[0]['value']].keys()]

# "챔피언 상대 승률" 탭 추가
app.layout = html.Div([
    html.H1("챔피언 성능 및 통계 대시보드", style={'textAlign': 'center', 'color': '#4CAF50'}),
    dcc.Tabs(id="tabs", value='tab-1', children=[
        # 기존 탭들 유지
        dcc.Tab(label='챔피언별 상대 역할군에 따른 승률', value='tab-1', children=[
            html.Div([
                html.Div([
                    html.Label("챔피언 선택"),
                    dcc.Dropdown(id='champion-role-dropdown', options=champion_options, value=champion_options[0]['value']),
                    html.Label("상대 역할군 선택"),
                    dcc.Dropdown(id='role-dropdown', options=role_options, value=role_options[0]['value']),
                ], style={'width': '20%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),

                html.Div([
                    dcc.Graph(id='combined-graph', style={'height': '80vh'})
                ], style={'width': '80%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ]),
    # 새로운 탭: 챔피언 상대 승률
        dcc.Tab(label='챔피언 상대 승률', value='tab-2', children=[
            html.Div([
                html.Div([
                    html.Label("챔피언 선택"),
                    dcc.Dropdown(id='champion-dropdown-compare', options=champion_options, value=champion_options[0]['value']),
                ], style={'width': '20%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),
                
                html.Div(id='champion-compare-table', style={'width': '80%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ]),
        dcc.Tab(label='챔피언 승률 및 픽률', value='tab-3', children=[
            html.Div([
                html.Div([
                    html.Label("포지션 선택"),
                    dcc.Dropdown(id='position-dropdown', options=position_options, value=position_options[0]['value']),
                ], style={'width': '20%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),
                
                html.Div(id='win-pick-rate-table', style={'width': '80%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ]),

        dcc.Tab(label='챔피언 성능 대시보드', value='tab-4', children=[
            html.Div([
                html.Div([
                    html.Label("역할군 선택"),
                    dcc.Dropdown(id='tag-dropdown', options=tag_options, value=[], multi=True),
                    html.Label("챔피언 선택"),
                    dcc.Dropdown(id='champion-dropdown', options=champion_options, value=[champion_options[0]['value']], multi=True),
                    html.Label("스탯 선택"),
                    dcc.Dropdown(id='stat-dropdown', value='챔피언에게 가한 피해량')
                ], style={'width': '20%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),
                
                html.Div([
                    dcc.Graph(id='stat-graph', style={'height': '80vh'})
                ], style={'width': '80%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ]),
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
    
    # 테이블 스타일 조정: 행간 간격, 여백 및 테두리 설정
    table = [html.H4(position, style={'textAlign': 'left', 'fontSize': '20px', 'marginBottom': '10px'})]
    table.append(html.Table([
        html.Thead(
            html.Tr([html.Th(col, style={'borderBottom': '1px solid black', 'padding': '8px'}) for col in df.columns if col != '포지션'])
        ),
        html.Tbody([
            html.Tr([
                html.Td(df.iloc[i][col], style={'padding': '5px', 'textAlign': 'center', 'borderBottom': '1px solid #ddd'}) for col in df.columns if col != '포지션'
            ]) for i in range(len(df))
        ])
    ], style={'width': '100%', 'margin': '20px 0', 'textAlign': 'center', 'border': '1px solid black', 'borderCollapse': 'collapse'}))
    
    return table

# 정렬 기준 관리 함수
def sort_winrate(df, sort_order):
    if sort_order == 'default':  # 명수 순서대로 정렬 (1명, 2명, 3명, 4명, 5명)
        return df.sort_index()
    elif sort_order == 'ascending':  # 오름차순 정렬
        return df.sort_values(by='승률', ascending=True)
    elif sort_order == 'descending':  # 내림차순 정렬
        return df.sort_values(by='승률', ascending=False)

# 콜백: 이중 Y축을 사용한 승률 및 표본수 그래프
@app.callback(
    Output('combined-graph', 'figure'),
    [Input('champion-role-dropdown', 'value'), Input('role-dropdown', 'value')]
)
def update_combined_graph(selected_champion, selected_role):
    if selected_champion in champion_winrate_by_role and selected_role in champion_winrate_by_role[selected_champion]:
        df = champion_winrate_by_role[selected_champion][selected_role].copy()
        overall_winrate = champion_win_pick_rate['ALL'].loc[champion_win_pick_rate['ALL']['챔피언'] == selected_champion, '승률'].values[0]
        df['승률'] = df['승률'] * 100
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df.index, y=df['표본 수'], name='표본 수', yaxis="y2", marker_color='#FFCC99', opacity=0.6, width=0.4))
        fig.add_trace(go.Scatter(x=df.index, y=df['승률'], mode='lines+markers', name='승률 (%)', yaxis="y1", line=dict(width=3, color='#6699CC')))
        annotations = [dict(x=x, y=y, text=f"{y:.1f}%", xanchor='center', yanchor='bottom', showarrow=False,font=dict(color='#6699CC')) for x, y in zip(df.index, df['승률'])]
        annotations.append(dict(xref="paper", yref="paper", x=0, y=1.15, text=f"<b>{selected_champion}</b>", showarrow=False,font=dict(size=20, color="black"),xanchor="left"))
        annotations.append(dict(xref="paper", yref="paper", x=0, y=1.05, text=f"{selected_role} 상대 승률", showarrow=False,font=dict(size=16, color="black"),xanchor="left"))
        annotations.append(dict(xref="paper", yref="paper", x=1, y=1.05, text=f"전체 승률: {overall_winrate*100:.2f}%", showarrow=False,font=dict(size=16, color='#6699CC'),xanchor="right"))
        fig.update_layout(
            title="",  # 제목을 빈 문자열로 설정
            xaxis_title="상대 역할군 명수",
            yaxis=dict(title="승률 (%)", side="left"),
            yaxis2=dict(title="표본 수", overlaying="y", side="right"),
            annotations=annotations
        )

        return fig
    else:
        return {}

# 콜백: 챔피언 상대 승률 테이블 업데이트
@app.callback(
    Output('champion-compare-table', 'children'),
    [Input('champion-dropdown-compare', 'value')]
)
def update_champion_compare_table(selected_champion):
    if selected_champion in winrate_per_champion:
        df = winrate_per_champion[selected_champion].copy()
        df['승률'] = (df['승률'] * 100).round(2).astype(str) + '%'  # 승률을 퍼센트로 변환 및 소수점 둘째 자리까지 표시
        table = html.Table([
            html.Thead(
                html.Tr([html.Th(col, style={'borderBottom': '1px solid black', 'padding': '8px'}) for col in df.columns])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(df.iloc[i][col], style={'padding': '5px', 'textAlign': 'center', 'borderBottom': '1px solid #ddd'}) for col in df.columns
                ]) for i in range(len(df))
            ])
        ], style={'width': '100%', 'margin': '20px 0', 'textAlign': 'center', 'border': '1px solid black', 'borderCollapse': 'collapse'})

        header = html.H4(f"{selected_champion} 상대 챔피언 승률", style={'textAlign': 'center', 'marginBottom': '10px'})
        return [header, table]
    else:
        return "선택된 챔피언에 대한 데이터가 없습니다."

# 앱 실행
if __name__ == '__main__':
    app.run_server(debug=True)
