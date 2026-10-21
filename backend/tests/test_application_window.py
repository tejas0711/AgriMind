from app.engine.application_window import assess_application_window


def test_no_application_needed():
    result = assess_application_window([], needs_application=False)
    assert result.recommendation == "NO"


def test_waits_on_heavy_rain():
    days = [
        {"date": "2026-08-27", "precipitation_mm": 25, "precipitation_probability_pct": 80, "wind_max_kmh": 10},
        {"date": "2026-08-28", "precipitation_mm": 2, "precipitation_probability_pct": 10, "wind_max_kmh": 8},
    ]
    result = assess_application_window(days, needs_application=True)
    assert result.apply_today == "WAIT"
    assert result.next_window == "2026-08-28"
    assert "heavy rain" in result.reason.lower()


def test_high_probability_light_rain_says_chance_not_heavy():
    """Regression test: previously the message always said 'Heavy rain
    expected' even when the trigger was a high PROBABILITY of light rain
    (e.g. 3.9mm at 100% probability) -- which is misleading since 3.9mm
    isn't actually heavy rain.
    """
    days = [{"date": "2026-08-27", "precipitation_mm": 3.9, "precipitation_probability_pct": 100, "wind_max_kmh": 10}]
    result = assess_application_window(days, needs_application=True)
    assert result.apply_today == "WAIT"
    assert "heavy rain" not in result.reason.lower()
    assert "chance of rain" in result.reason.lower()


def test_go_on_clear_day():
    days = [{"date": "2026-08-27", "precipitation_mm": 0, "precipitation_probability_pct": 5, "wind_max_kmh": 10}]
    result = assess_application_window(days, needs_application=True)
    assert result.apply_today == "GO"


def test_waits_on_high_wind():
    days = [{"date": "2026-08-27", "precipitation_mm": 0, "precipitation_probability_pct": 5, "wind_max_kmh": 40}]
    result = assess_application_window(days, needs_application=True)
    assert result.apply_today == "WAIT"
