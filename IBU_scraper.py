from flask import Flask, request, render_template, jsonify, Response
from bot3 import scrape_team_data
from utils import name_to_color
from datetime import datetime, timedelta
import pandas as pd
import os
import hashlib
import threading
import webbrowser
import queue
import json

DATA_FOLDER = os.getenv("DATA_FOLDER", "Scraped_Team_Info")

progress_queue = queue.Queue()
layout_height = 550
layout_width = 1000
aspect_ratio = layout_height / layout_width

def open_browser():
    webbrowser.open("http://127.0.0.1:5000/")

def name_to_color(name):
    # Hash the name to get a consistent value
    hash_object = hashlib.md5(name.encode())
    hex_color = "#" + hash_object.hexdigest()[:6]
    return hex_color

def get_latest_csv_file():
    files = [f for f in os.listdir(DATA_FOLDER) if f.startswith("sheepit_team_points_") and f.endswith(".csv")]
    if not files:
        return None, None
    files.sort(reverse=True)
    latest_file = files[0]
    file_path = os.path.join(DATA_FOLDER, latest_file)
    # Extract date from filename
    date_str = latest_file.replace("sheepit_team_points_", "").replace(".csv", "")
    return file_path, date_str

def get_chart_total():
    file, date_str = get_latest_csv_file()
    if not file or not os.path.exists(file):
        return {"error": "Data file not found."}
    # Load CSV
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"name": "Member", "points": "Points"})
    member = df["Member"]
    points = df["Points"]
    color = df["Member"].apply(name_to_color)
    return data_for_return(member, points, color)

def get_last_week_range():
    today = datetime.today().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    this_monday = last_monday + timedelta(days=6)
    print(last_monday, this_monday)
    end_date = this_monday.strftime("%Y-%m-%d")
    start_date = last_monday.strftime("%Y-%m-%d")
    # Define file paths
    file_start = os.path.join(DATA_FOLDER, f"sheepit_team_points_{start_date}.csv")
    file_end = os.path.join(DATA_FOLDER, f"sheepit_team_points_{end_date}.csv")
    return standardize_range_formats(file_start, file_end)

def get_last_month_range():
    today = datetime.today().date()
    first_of_this_month = today.replace(day=1)
    last_month_start = last_month_end.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    end_date = last_month_end.strftime("%Y-%m-%d")
    start_date = last_month_start.strftime("%Y-%m-%d")
    # Define file paths
    file_start = os.path.join(DATA_FOLDER, f"sheepit_team_points_{start_date}.csv")
    file_end = os.path.join(DATA_FOLDER, f"sheepit_team_points_{end_date}.csv")
    return standardize_range_formats(file_start, file_end)

def get_last_year_range():
    today = datetime.today().date()
    last_year = today.year - 1
    last_year_start = datetime(last_year, 1, 1).date()
    last_year_end = datetime(last_year, 12, 31).date()
    end_date = last_year_end.strftime("%Y-%m-%d")
    start_date = last_year_start.strftime("%Y-%m-%d")
    # Define file paths
    file_start = os.path.join(DATA_FOLDER, f"sheepit_team_points_{start_date}.csv")
    file_end = os.path.join(DATA_FOLDER, f"sheepit_team_points_{end_date}.csv")
    return standardize_range_formats(file_start, file_end)

def get_chart_data_for_range(start_date, end_date):

    file_start = os.path.join(DATA_FOLDER, f"sheepit_team_points_{start_date}.csv")
    file_end = os.path.join(DATA_FOLDER, f"sheepit_team_points_{end_date}.csv")

    # Check if both files exist
    if not os.path.exists(file_start) or not os.path.exists(file_end):
        return {"error": "One or both data files not found for the selected range."}

    return standardize_range_formats(file_start, file_end)

def standardize_range_formats(file_start_raw, file_end_raw):
    # Load CSVs
    df_start = pd.read_csv(file_start_raw)
    df_end = pd.read_csv(file_end_raw)

    # Clean and standardize column names
    df_start.columns = df_start.columns.str.strip()
    df_end.columns = df_end.columns.str.strip()

    # Rename columns to match
    df_start = df_start.rename(columns={"name": "Member", "points": "Points"})
    df_end = df_end.rename(columns={"name": "Member", "points": "Points"})

    
    # Find new members in end that are not in start
    new_members = set(df_end["Member"]) - set(df_start["Member"])
    if new_members:
        # Create DataFrame for new members with 0 points at start
        new_rows = pd.DataFrame({
            "Member": list(new_members),
            "Points": [0] * len(new_members)
        })
        # Append to df_start
        df_start = pd.concat([df_start, new_rows], ignore_index=True)

    # Merge and calculate difference
    merged = pd.merge(df_end, df_start, on="Member", suffixes=("_end", "_start"))
    merged["Delta"] = merged["Points_end"] - merged["Points_start"]
    #merged = merged[merged["Delta"] > 0] # Uncomment to filter out non-positive/0 points members
    color = merged["Member"].apply(name_to_color)
    member = merged["Member"]
    points = merged["Delta"]

    # Return data in pie chart format
    return data_for_return(member, points, color)

def data_for_return(data_member, data_points, color_data):
    return {
        "data": [
        {
            "type": "pie",
            "labels": data_member.tolist(),
            "values": data_points.tolist(),
            "hole": 0.5,
            "text": get_custom_text(data_points, data_member),
            "textinfo": "text",
            "textposition": "outside",
            "hoverinfo": "label+percent+value",
            "marker": {
                "colors": color_data.tolist(),
            },
            "automargin": False,
            "domain": {"x": [0, 1], "y": [0, 1]},
        }
    ],
    "layout": {
        "width": layout_width,
        "height": layout_height, 
        "margin": {"t": 30, "b": 30, "l": 0, "r": 0},
        "showlegend": True,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "shapes": [
            {
                "type": "circle",
                "xref": "paper",
                "yref": "paper",
                "x0": 0.325,
                "y0": 0.25,
                "x1": 0.675,
                "y1": 0.75,
                "line": {"color": "ffffff", "width": 3},
                "fillcolor": "rgba(0,0,0,0)"
            },
            {
                "type": "circle",
                "xref": "paper",
                "yref": "paper",
                "x0": 0.15,
                "y0": 0,
                "x1": 1-0.15,
                "y1": 1,
                "line": {"color": "ffffff", "width": 3},
                "fillcolor": "rgba(0,0,0,0)"
            }
        ],
        "font": {
            "color": "white",
            "family": "Arial",
            "size": 14
        },
        "legend": {
            "title": {
                "text": "<b>Team Members<b>",
                "font": {
                    "color": "white"
                }
            },
            "xanchor": "left",
            "x": 1.2,
            "y": 0.1,
            "font": {
                "color": "white"
            }
            }
        },
        "config": {
            "displaylogo": False,
            "displayModeBar": False,
            "showTips": False
        }
    }

def get_custom_text(values, labels):
    total = sum(values)
    result = []
    for i, v in enumerate(values):
        if v == 0 or total == 0:
            result.append("")
        else:
            percent = (v / total) * 100
            if percent >= 0.95:
                result.append(f"{labels[i]} ({percent:.1f}%)")
            else:
                result.append("")
    return result

app = Flask(__name__) #. .venv/bin/activate

@app.route('/')
def index():
    file_path, date_str = get_latest_csv_file()
    if "error" in file_path or not date_str:
        latest_file = "No data"
        latest_date = "No data"
    else:
    # Format the file string if possible
        try:
            latest_file = os.path.abspath(file_path)
            latest_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
        except Exception:
            latest_file = file_path
            latest_date = date_str
    print(f"Latest file: {latest_file}, Date: {latest_date}")
    return render_template('index_IBU.html',saved_file=latest_file, latest_date=latest_date)

@app.route("/get_chart_data")
def get_chart_data():
    chart_type = request.args.get("type")
    start = request.args.get("start")
    end = request.args.get("end")

    if chart_type == "last_week":
        data = get_last_week_range()
        if not data or "error" in data:
            return jsonify({"error": "Not enough data available for the selected range."}), 400
        return jsonify(data)
    elif chart_type == "last_month":
        data = get_last_month_range()
        if not data or "error" in data:
            return jsonify({"error": "Not enough data available for the selected range."}), 400
        return jsonify(data)
    elif chart_type == "last_year":
        data = get_last_year_range()
        if not data or "error" in data:
            return jsonify({"error": "Not enough data available for the selected range."}), 400
        return jsonify(data)
    elif chart_type == "custom" and start and end:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
        data = get_chart_data_for_range(start_date, end_date)
        if not data or "error" in data:
            return jsonify({"error": "Not enough data available for the selected range."}), 400
        return jsonify(data)
    elif chart_type == "total":
        data = get_chart_total()
        if not data or "error" in data:
            return jsonify({"error": "Not enough data available."}), 400
        return jsonify(data)
    else:
        return jsonify({"error": "Invalid request"}), 400

@app.route("/visualization")
def visualization():
    data = get_chart_total()
    _, date_str = get_latest_csv_file()
    if not data or "error" in data or not date_str:
        labels, values, colors = [], [], []
        latest_date_fmt = "No data"
    else:
        labels = data["data"][0]["labels"]
        values = data["data"][0]["values"]
        colors = data["data"][0]["marker"]["colors"]
        # Format the date string if possible
        try:
            from datetime import datetime
            latest_date_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
        except Exception:
            latest_date_fmt = date_str
    return render_template("graphs.html", labels=labels, values=values, colors=colors, latest_date=latest_date_fmt)

def flask_progress_callback(msg, progress_percent, latest_date=None, saved_file=None):
    payload = {"msg": msg, "percent": progress_percent}
    if latest_date is not None:
        payload["latest_date"] = latest_date
    if saved_file is not None:
        payload["saved_file"] = saved_file
    progress_queue.put(json.dumps(payload))

@app.route('/scrape', methods=['POST'])
def scrape():
    username = request.form['username']
    password = request.form['password']
    try:
        # Run the scraper (this creates the new file)
        scrape_team_data(username, password, progress_callback=flask_progress_callback)
        # Now get the latest file (should be the one just created)
        latest_file, date_str = get_latest_csv_file()
        latest_file = os.path.abspath(latest_file) if latest_file else "No data"
        latest_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y") if date_str else "No data"
        return jsonify({'success': True, 'saved_file': latest_file, 'latest_date': latest_date})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/progress_stream')
def progress_stream():
    def event_stream():
        while True:
            message = progress_queue.get()
            yield f"data: {message}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)