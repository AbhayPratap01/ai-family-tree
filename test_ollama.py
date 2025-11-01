import requests, json

prompt = "Create a simple family tree in JSON. Father: Raj, Mother: Neha, Son: Abhay, Daughter: Kavya."
data = {
    "model": "tinyllama",
    "prompt": prompt
}

response = requests.post("http://localhost:11434/api/generate", json=data, stream=True)

for line in response.iter_lines():
    if line:
        chunk = json.loads(line)
        print(chunk.get("response", ""), end="", flush=True)
