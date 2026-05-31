
from flask import Flask, render_template, request, jsonify
import sqlite3, requests
from datetime import datetime

app = Flask(__name__)

ICONS={0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",61:"🌧️",63:"🌧️",65:"🌧️",71:"❄️",73:"❄️",75:"❄️",95:"⛈️"}

def init_db():
    conn=sqlite3.connect("weather.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_type TEXT,
        place_name TEXT,
        temperature REAL,
        wind_speed REAL,
        search_date TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

def get_weather(lat,lon):
    data=requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,weather_code",
        timeout=15).json()

    return {
        "temp":data["current"]["temperature_2m"],
        "wind":data["current"]["wind_speed_10m"],
        "icon":ICONS.get(data["current"]["weather_code"],"🌍")
    }

def save_history(tp,name,temp,wind):
    conn=sqlite3.connect("weather.db")
    conn.execute(
        "INSERT INTO history(query_type,place_name,temperature,wind_speed,search_date) VALUES (?,?,?,?,?)",
        (tp,name,temp,wind,datetime.now().strftime("%d.%m.%Y %H:%M"))
    )
    conn.commit()
    conn.close()

@app.route("/", methods=["GET","POST"])
def index():
    weather=None

    if request.method=="POST":
        city=request.form["city"]

        geo=requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru&format=json",
            timeout=15).json()

        if geo.get("results"):
            p=geo["results"][0]
            w=get_weather(p["latitude"],p["longitude"])

            weather={
                "place":p["name"],
                "lat":p["latitude"],
                "lon":p["longitude"],
                **w
            }

            save_history("Поиск",p["name"],w["temp"],w["wind"])

    return render_template("index.html",weather=weather)

@app.route("/weather_click")
def weather_click():
    lat=request.args.get("lat")
    lon=request.args.get("lon")

    rev=requests.get(
        f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}",
        headers={"User-Agent":"WeatherCourseProject"},
        timeout=20).json()

    addr=rev.get("address",{})
    place=addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality") or rev.get("name") or "Неизвестное место"

    w=get_weather(lat,lon)

    save_history("Карта",place,w["temp"],w["wind"])

    return jsonify({
        "place":place,
        "lat":lat,
        "lon":lon,
        **w
    })

@app.route("/history")
def history():
    conn=sqlite3.connect("weather.db")
    rows=conn.execute("SELECT * FROM history ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("history.html",rows=rows)

if __name__=="__main__":
    app.run(debug=True)
