import dash
from dash import dcc, html
from dash.dependencies import Input, Output
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
        # 기존 탭 1: 챔피언 성능 대시보드
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
        
        # 기존 탭 2: 챔피언 승률 및 픽률
        dcc.Tab(label='챔피언 승률 및 픽률', value='tab-2', children=[
            html.Div([
                html.Div([
                    html.Label("포지션 선택"),
                    dcc.Dropdown(id='position-dropdown', options=position_options, value=position_options[0]['value']),
                ], style={'width': '25%', 'padding': '20px', 'backgroundColor': '#F0F0F0', 'height': '90vh', 'overflowY': 'scroll'}),
                
                html.Div(id='win-pick-rate-table', style={'width': '75%', 'padding': '20px'})
            ], style={'display': 'flex'})
        ]),

        # 새로운 탭 3: 챔피언별 역할군 승률
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

# 정렬 기준 관리 함수
def sort_winrate(df, sort_order):
    if sort_order == 'ascending':  # 오름차순 정렬
        return df.sort_values(by='승률', ascending=True)
    elif sort_order == 'descending':  # 내림차순 정렬
        return df.sort_values(by='승률', ascending=False)
    else:  # 기본 순서 (1명~5명)
        return df

# 새로운 콜백: 챔피언별 역할군 승률 테이블 업데이트
@app.callback(
    Output('role-winrate-table', 'children'),
    [Input('champion-role-dropdown', 'value'), Input('sort-dropdown', 'value')]
)
def update_role_winrate_table(selected_champion, sort_order):
    tables = []
    
    if selected_champion in champion_winrate_by_role:
        # 챔피언 이름을 표 상단에 표시
        tables.append(html.H3(selected_champion, style={'textAlign': 'center'}))
        
        # 역할군별로 데이터를 정렬하고 표에 표시
        for role, df in champion_winrate_by_role[selected_champion].items():
            df = df.copy()
            df['승률'] = df['승률'].apply(lambda x: f"{round(x * 100, 2)}%" if pd.notna(x) else "데이터 없음")
            df = sort_winrate(df, sort_order)  # 정렬 적용
            
            # 정렬 후 승률에 맞는 헤더(1명, 2명 등)도 재정렬
            sorted_counts = df.index.tolist()

            # 역할군별 승률 테이블 생성 (1~5명 가로 정렬) + 테두리, 여백 조절, 고정 너비
            table = html.Table([
                html.Thead(html.Tr([
                    html.Th("역할군", style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center', 'width': '100px'}),
                    *[html.Th(f"{count}명", style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center', 'width': '100px'}) for count in sorted_counts]
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(role, style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center', 'width': '100px'}),
                        *[html.Td(df['승률'].iloc[i] if i < len(df) else "데이터 없음", style={'border': '1px solid black', 'padding': '5px', 'textAlign': 'center', 'width': '100px'}) for i in range(len(df))]
                    ])
                ])
            ], style={'width': '100%', 'margin': '20px 0', 'borderCollapse': 'collapse'})
            
            tables.append(html.Div([table]))
    
    return tables if tables else "선택된 챔피언에 대한 데이터가 없습니다."

# 앱 실행
if __name__ == '__main__':
    app.run_server(debug=True)
