import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()


"""
TODO: Use the FastAPI get decorator make this function
a GET request for the endpoint /api/pokemon/{name}
"""
def get_pokemon(name: str):
    name = name.strip().lower()
    try:
        response = httpx.get("TODO: Put the right PokeAPI URL here", timeout=10.0)
        if response.status_code == 404:
            raise HTTPException(404, f'No Pokémon found for "{name}".')
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(502, "Could not reach PokéAPI. Please try again.") from exc

    data = response.json()
    return {
        "id": data["TODO: Put correct key based on schema"],
        "name": data["TODO: Put correct key based on schema"],
        "image": data["sprites"].get("other", {}).get("official-artwork", {}).get("front_default")
        or data["sprites"].get("front_default"),
        "types": [entry["type"]["name"] for entry in data["types"]],
        "height_m": data["height"] / 10,
        "weight_kg": data["weight"] / 10,
        "abilities": [entry["ability"]["name"] for entry in data["abilities"]],
        "stats": [
            {"name": entry["stat"]["name"], "value": entry["base_stat"]}
            for entry in data["stats"]
        ],
    }
