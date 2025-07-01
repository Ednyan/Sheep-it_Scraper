def scrape_team_data(username, password, progress_callback=None):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By 
    from selenium.webdriver.common.keys import Keys
    import time
    import csv
    import sys
    import os
    from datetime import datetime
    from selenium.webdriver.chrome.options import Options
    from IBU_scraper import name_to_color

    options = Options()
    options.add_argument('--headless')  # Optional: Run in background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Login Info
    #username = "Data_Seeker" #insert your username
    #password = "data_seeker_42" #insert your password

    def update_progress(msg, percentage):
        if progress_callback:
            progress_callback(msg, percentage)

    def resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            # Running from PyInstaller bundle
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    # Iniciates Browser
    update_progress("Opening Browser",0)
    CHROMEDRIVER_PATH = resource_path(os.path.join("driver", "chromedriver.exe"))
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    time.sleep(1)
    update_progress("Browser started successfully",10)


    print("Browser started successfully: " + CHROMEDRIVER_PATH)
    # Goes to the sheep-it I.B.U team web page
    update_progress("Browsing for SheepIt I.B.U Team",20)
    driver.get("https://www.sheepit-renderfarm.com/team/2109")
    time.sleep(1)
    # Does the login
    update_progress("Login in with credentials",30)
    input_element = driver.find_element(By.ID, "login_login")
    input_element.send_keys(username)

    input_element = driver.find_element(By.ID, "login_password")
    input_element.send_keys(password)

    input_element.send_keys(Keys.ENTER)

    time.sleep(1)

    update_progress("Login Successful", 50)

    time.sleep(1)

    update_progress("Waiting for page to load",55)
    # Waits for the website to load
    time.sleep(3)

    # Locates the team's HTML table elements
    update_progress("Extracting Data",60)
    table = driver.find_element(By.XPATH, "/html/body/section[2]/div/div[1]/table")
    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Ignores table header
    
    # Extracts the table data into an array
    team_data = []
    member_list = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 3:
            continue
        rank = cols[0].text.strip()
        member_name = cols[1].text.strip()
        member_list.append(member_name)
        points_text = cols[2].text.strip().replace(",", "")
        joined_date_text = cols[3].text.strip()
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

    time.sleep(1)

    update_progress("Extract Successful",80)

    # Creates a CSV file with the time stamp of the day it was created
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d") #time stamp
    csv_filename = f"Scraped_Team_Info/sheepit_team_points_{timestamp_str}.csv"

    time.sleep(1)

    update_progress("Saving Data to CSV",90)
    # Saves the table data into the CSV file
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Date", "Rank", "Member", "Points", "Joined Date", "Color"])
        for entry in team_data:
            writer.writerow([now.date(), entry["rank"], entry["member"], entry["points"], entry["joined_date"], entry["color"]])


    time.sleep(1)

    latest_file = os.path.abspath(csv_filename)
    latest_date_fmt = now.strftime("%B %d, %Y")
    if progress_callback:
        progress_callback("Data saved successfully!", 100, latest_date_fmt, latest_file)
    

    update_progress("",0)
    time.sleep(2)
    driver.quit()
