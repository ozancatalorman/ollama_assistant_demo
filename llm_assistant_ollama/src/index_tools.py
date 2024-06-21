import requests


def get_current_weather(location):
    """
    Fetches the current weather data of a given location
    """
    api_key = "your_api_key"
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
    response = requests.get(url)
    data = response.json()

    temperature = data["current"]["temp_c"]
    weather_condition = data["current"]["condition"]["text"]

    return {
        "location": location,
        "temperature": temperature,
        "weather_condition": weather_condition,
        "unit": "celsius"
    }
