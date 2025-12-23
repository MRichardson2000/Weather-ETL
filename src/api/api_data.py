import openmeteo_requests
import requests_cache
from retry_requests import retry
import json
from typing import Any
from pathlib import Path
from datetime import datetime, timedelta, UTC

JSON_DATA = Path(__file__).parent.parent.parent / "data.json"


class ApiData:
    def __init__(self) -> None:
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)
        self.url = "https://api.open-meteo.com/v1/forecast"
        self.params: dict[str, Any] = {
            "latitude": 52.52,
            "longitude": 13.41,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "snow_depth",
                "weather_code",
                "pressure_msl",
                "surface_pressure",
                "cloud_cover",
                "visibility",
                "vapour_pressure_deficit",
                "evapotranspiration",
                "et0_fao_evapotranspiration",
                "wind_speed_180m",
                "wind_direction_180m",
                "wind_gusts_10m",
                "temperature_180m",
                "soil_temperature_54cm",
                "soil_moisture_27_to_81cm",
            ],
            "timezone": "auto",
            "start_date": datetime.now(UTC).date().isoformat(),
            "end_date": (datetime.now(UTC).date() + timedelta(days=1)).isoformat(),
        }

    def get_data(self) -> dict[str, Any]:
        responses = self.client.weather_api(self.url, params=self.params)
        if not responses:
            raise RuntimeError("No response from Open-Meteo API")
        response = responses[0]
        hourly = response.Hourly()
        start_time = datetime.fromtimestamp(hourly.Time(), UTC)
        end_time = datetime.fromtimestamp(hourly.TimeEnd(), UTC)
        interval = timedelta(seconds=hourly.Interval())
        dates = []
        current = start_time
        while current < end_time:
            dates.append(current.isoformat())
            current += interval
        hourly_data = {"date": dates}
        steps = len(dates)
        for i, var in enumerate(self.params["hourly"]):
            values = [hourly.Variables(i).Values(j) for j in range(steps)]
            hourly_data[var] = values

        return {
            "coordinates": {
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "elevation": response.Elevation(),
                "utc_offset_seconds": response.UtcOffsetSeconds(),
            },
            "hourly": hourly_data,
        }


def main() -> None:
    api = ApiData()
    data = api.get_data()
    with open(JSON_DATA, "w") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    main()
