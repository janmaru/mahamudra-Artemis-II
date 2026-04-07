from datetime import datetime, timezone, timedelta
from artemis.compute import format_met, format_ra_dec, flight_day, mission_elapsed_time
from artemis import config

def test_format_met():
    td = timedelta(days=5, hours=3, minutes=48, seconds=27)
    assert format_met(td) == "05d 03h 48m 27s"
    
    td_neg = timedelta(hours=-2)
    assert format_met(td_neg) == "-00d 02h 00m 00s"

def test_format_ra_dec():
    # Example: 180 degrees RA, 45 degrees Dec
    # RA: 180 / 15 = 12h
    # Dec: 45
    assert format_ra_dec(180.0, 45.0) == "12h 00m 00s / +45° 00' 00\""
    
    # Negative Dec
    assert format_ra_dec(0.0, -10.5) == "00h 00m 00s / -10° 30' 00\""
    
    # None handling
    assert format_ra_dec(None, None) == "N/A"

def test_flight_day():
    launch = config.LAUNCH_TIME
    assert flight_day(launch + timedelta(hours=1)) == 1
    assert flight_day(launch + timedelta(days=1, hours=1)) == 2
    assert flight_day(launch - timedelta(hours=1)) == 0

if __name__ == "__main__":
    try:
        test_format_met()
        print("test_format_met: PASSED")
        test_format_ra_dec()
        print("test_format_ra_dec: PASSED")
        test_flight_day()
        print("test_flight_day: PASSED")
        print("\nAll tests PASSED!")
    except AssertionError as e:
        print(f"Test FAILED: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
