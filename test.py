import requests

OPENROUTER_API_KEY = "DEIN_API_KEY"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}"
}

response = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers=headers
)

data = response.json()

working_models = []

for model in data["data"]:

    model_id = model.get("id", "")

    # Nur Free Modelle
    if ":free" not in model_id:
        continue

    # Provider muss existieren
    top_provider = model.get("top_provider")

    if not top_provider:
        continue

    working_models.append(model_id)

print("\nFUNKTIONSFÄHIGE FREE MODELLE:\n")

for model in working_models:
    print(model)