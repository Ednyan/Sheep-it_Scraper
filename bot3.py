import requests
from bs4 import BeautifulSoup
import time
import csv
import os
from datetime import datetime
from utils import name_to_color

def scrape_team_data(username, password, progress_callback=None):
    def update_progress(msg, percentage):
        if progress_callback:
            progress_callback(msg, percentage)

    session = requests.Session()

    # Step 1: Get login page (to get any cookies or CSRF tokens if needed)
    update_progress("Opening login page", 0)
    login_url = "https://www.sheepit-renderfarm.com/user/authenticate"
    team_url = "https://www.sheepit-renderfarm.com/team/2109"
    update_progress("Login page loaded", 10)
    # If there is a CSRF token, extract it here (not present on SheepIt as of July 2025)
    payload = {
        "login": username,
        "password": password,
    }

    # Step 3: Post login form
    update_progress("Logging in with credentials", 20)
    r = requests.post(login_url, data=payload)
    with requests.session() as s:
        s.post(login_url, data=payload)
        r = s.get(team_url)
        if "logout" not in r.text.lower():
            update_progress("Login failed", 100)
            raise Exception("Login failed: check your username and password.")
        soup = BeautifulSoup(r.content, "html.parser")
        update_progress("Login successful", 30)

        update_progress("Searching for Team Data", 50)

        table = soup.find("table")
        if not table:
            update_progress("Failed to find team table", 100)
            raise Exception("Could not find team table on the page.")
        rows = table.find_all("tr")[1:]  # skip header
        team_data = []
        member_list = []
        update_progress("Extracting data", 60)
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue
            rank = cols[0].get_text(strip=True)
            member_name = cols[1].get_text(strip=True)
            member_list.append(member_name)
            points_text = cols[2].get_text(strip=True).replace(",", "")
            joined_date_text = cols[3].get_text(strip=True)
            color = name_to_color(member_name)
            try:
                points = int(points_text)
            except ValueError:
                points = 0

            team_data.append({
                "rank": rank,
                "member": member_name,
                "points": points,
                "joined_date": joined_date_text,
                "color": color
            })

        update_progress("Extract successful", 80)


        # Step 6: Save to CSV
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d")
        csv_filename = f"Scraped_Team_Info/sheepit_team_points_{timestamp_str}.csv"
        os.makedirs(os.path.dirname(csv_filename), exist_ok=True)

        update_progress("Saving data to CSV", 90)
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Date", "Rank", "Member", "Points", "Joined Date", "Color"])
            for entry in team_data:
                writer.writerow([now.date(), entry["rank"], entry["member"], entry["points"], entry["joined_date"], entry["color"]])


        latest_file = os.path.abspath(csv_filename)
        latest_date_fmt = now.strftime("%B %d, %Y")
        if progress_callback:
            progress_callback("Data saved successfully!", 100, latest_date_fmt, latest_file)
