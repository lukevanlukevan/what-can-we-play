import json

import streamlit as st
import requests

STEAM_API_KEY = st.secrets.get("STEAM_API_KEY", "your_steam_api_key_here")

def get_owned_games_with_names(steamid):
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
    params = {
        "key": STEAM_API_KEY,
        "steamid": steamid,
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        games = data.get("response", {}).get("games", [])
        return {game["appid"]: game["name"] for game in games}
    except Exception as e:
        st.error(f"Error fetching data for {steamid}: {e}")
        return {}

def filter_multiplayer(appids):
    multi = []
    for i, game in enumerate( appids ):
        url = "https://store.steampowered.com/api/appdetails"
        params = {
            "appids": game
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            cats = data[str(game)]['data']['categories']
            ismulti = True if any(item.get("id")==1 for item in cats) else False
            if ismulti:
                players = get_players(game)
                gameobj = {
                    "gameid": game,
                    "player_count": players
                }
                multi.append(gameobj)
        except Exception as e:
            print(game, "has error")
            # st.error(f"Error checking multiplayer for {game}: {e}")
    
    return multi

def get_players(gameid):
    url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    players = 0
    params = {
        "appid": gameid
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        players = data['response']['player_count']
    except:
        pass

    return players

st.title("🎮 Shared Steam Games Finder")

user_input = st.text_area(
    "Enter Steam64 IDs (one per line):",
    placeholder="76561198000000000\n76561198012345678"
)

if st.button("Find Shared Games"):
    steam_ids = [line.strip() for line in user_input.splitlines() if line.strip()]
    
    if not steam_ids:
        st.warning("Please enter at least one Steam64 ID.")
    else:
        with st.spinner("Fetching game libraries..."):
            user_libraries = [get_owned_games_with_names(sid) for sid in steam_ids]

        if any(len(lib) == 0 for lib in user_libraries):
            st.warning("Some users may have private profiles or no games.")

        shared_appids = set.intersection(*(set(lib.keys()) for lib in user_libraries)) if user_libraries else set()

        st.subheader("🎲 Multiplayer games owned by all")
        if shared_appids:
            name_lookup = user_libraries[0]
            with st.spinner("Getting game data..."):
                filtered_games = filter_multiplayer(shared_appids)
                sorted = filtered_games.sort(key=lambda x: x['player_count'], reverse=True)
                for gameobj in filtered_games:
                    appid = gameobj['gameid']
                    players = gameobj['player_count']
                    game_name = name_lookup.get(appid, f"AppID {appid}")
                    st.write(f"- [{game_name}](https://store.steampowered.com/app/{appid}) (Current players: {players})")
        else:
            st.info("No shared games found among these users.")

