import requests
from bs4 import BeautifulSoup

login_url = "https://www.sheepit-renderfarm.com/user/authenticate"
team_url = "https://www.sheepit-renderfarm.com/team/2109"
home_url = "https://www.sheepit-renderfarm.com/home"

payload = {
    "login": "data_seeker",
    "password": "data_seeker_42",
}

r = requests.post(login_url, data=payload)
with requests.session() as s:
    s.post(login_url, data=payload)
    r = s.get(team_url)
    soup = BeautifulSoup(r.content, "html.parser")
    print(soup.prettify())