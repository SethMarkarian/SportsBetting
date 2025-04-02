import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from datetime import datetime
import re

# Define the folder containing betting data
DATA_FOLDER = "../nba_saved_csv"

# Function to extract date from filename
def extract_date_from_filename(filename):
    match = re.search(r'\d{2}_\d{2}_\d{4}', filename)
    if match:
        return datetime.strptime(match.group(), "%m_%d_%Y")
    return None

# Function to load and process betting data
def load_betting_data():
    all_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    df_list = []
    
    for file in all_files:
        file_date = extract_date_from_filename(file)
        if file_date and file_date < datetime.today():
            file_path = os.path.join(DATA_FOLDER, file)
            df = pd.read_csv(file_path)
            df["Date"] = file_date  # Assign extracted date
            df_list.append(df)
    
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    else:
        return pd.DataFrame()

# Initialize Dash app
app = dash.Dash(__name__)

# Load data
df = load_betting_data()


# Layout of the dashboard
app.layout = html.Div([
    html.H1("NBA Betting Accuracy Dashboard"),
    
    dcc.Dropdown(
        id='bet-type',
        options=[{'label': col, 'value': col} for col in df.columns if 'bet' in col.lower()],
        value=df.columns[0] if not df.empty else None,
        placeholder="Select a bet type"
    ),
    
    dcc.Graph(id='bet-accuracy-graph')
])

# Callback to update graph
@app.callback(
    Output('bet-accuracy-graph', 'figure'),
    Input('bet-type', 'value')
)
def update_graph(selected_bet):
    df = load_betting_data()
    if df.empty or selected_bet is None or selected_bet not in df.columns:
        return px.bar(title="No Data Available")
    if df.empty or selected_bet is None:
        return px.bar(title="No Data Available")
    
    if 'Bet Hit' not in df.columns:
        print("Error: 'Bet Hit' column not found. Available columns:", df.columns)
        return px.bar(title="Missing 'Bet Hit' column in dataset")
    df['Correct'] = df[selected_bet] == df['Bet Hit']  # Adjust column names as needed
    accuracy = df.groupby('Date')['Correct'].mean().reset_index()
    accuracy.columns = ['Date', 'Accuracy']
    
    return px.line(accuracy, x='Date', y='Accuracy', title=f'Betting Accuracy for {selected_bet}')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
