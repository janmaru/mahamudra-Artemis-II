import logging
from datetime import datetime, timezone, timedelta
from artemis.fetchers.horizons import HorizonsFetcher
from artemis.state import SharedState

logging.basicConfig(level=logging.INFO)

def test_trajectory_sync():
    state = SharedState()
    fetcher = HorizonsFetcher(state)
    
    print("Fetching trajectory data...")
    # Manually trigger trajectory fetch
    fetcher._fetch_trajectory()
    
    # Check state
    sc, dsn, wx, donki, traj, photo, errors = state.snapshot()
    
    if traj:
        print(f"Success! Found {len(traj.samples)} synchronized samples.")
        if len(traj.samples) > 0:
            s = traj.samples[0]
            print(f"First sample: {s.timestamp}")
            print(f"  Orion: {s.orion.x}, {s.orion.y}, {s.orion.z}")
            print(f"  Moon:  {s.moon.x}, {s.moon.y}, {s.moon.z}")
            
            # Check for any obvious desync in timestamps (all should be unique and matched)
            timestamps = [s.timestamp for s in traj.samples]
            if len(timestamps) == len(set(timestamps)):
                print("Timestamps are unique and synced.")
            else:
                print("WARNING: Duplicate timestamps found!")
    else:
        print("Failed to fetch trajectory.")

if __name__ == "__main__":
    test_trajectory_sync()
