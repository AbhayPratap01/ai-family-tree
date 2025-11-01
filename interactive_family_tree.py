import re
import requests, json
import networkx as nx
import matplotlib.pyplot as plt
import os

FAMILY_FILE = "family_tree.json"

def load_tree():
    """Load existing family tree from JSON file if available."""
    if os.path.exists(FAMILY_FILE):
        with open(FAMILY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tree(tree):
    """Save current family tree to JSON file."""
    with open(FAMILY_FILE, "w") as f:
        json.dump(tree, f, indent=4)


# Global graph for family relationships
G = nx.DiGraph()

def query_ollama(prompt):
    """Send a query to the local Ollama model"""
    url = "http://localhost:11434/api/generate"
    payload = {"model": "tinyllama", "prompt": prompt}
    response = requests.post(url, json=payload, stream=True)

    output = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            output += data.get("response", "")
    return output.strip()

def extract_relationships(text):
    """Simple rule-based relationship extractor"""
    relation = {}

    # Convert to lowercase for easy pattern matching
    text = text.lower()

    # Detect father and mother relationships
    father_match = re.search(r"(\w+)'s father is (\w+)", text)
    mother_match = re.search(r"(\w+)'s mother is (\w+)", text)
    sibling_match = re.search(r"(\w+) is (\w+)'s (brother|sister|sibling)", text)

    if father_match:
        relation["child"] = father_match.group(1).capitalize()
        relation["father"] = father_match.group(2).capitalize()

    if mother_match:
        relation["child"] = mother_match.group(1).capitalize()
        relation["mother"] = mother_match.group(2).capitalize()

    if sibling_match:
        relation["sibling1"] = sibling_match.group(1).capitalize()
        relation["sibling2"] = sibling_match.group(2).capitalize()

    return relation if relation else None


def update_tree(relation):
    """Add relationships to the graph"""
    if "father" in relation and "child" in relation:
        G.add_edge(relation["father"], relation["child"], label="father")
    if "mother" in relation and "child" in relation:
        G.add_edge(relation["mother"], relation["child"], label="mother")
    if "sibling1" in relation and "sibling2" in relation:
        G.add_edge(relation["sibling1"], relation["sibling2"], label="sibling")

def visualize_tree():
    """Draw the current family tree"""
    plt.figure(figsize=(8,6))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=2000, font_size=10, font_weight="bold")
    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("AI Family Tree (TinyLlama)")
    plt.show()

def main():
    print("👋 Welcome to AI Family Tree Builder (TinyLlama Edition)")
    print("Type relationships like 'Abhay's father is Raj and mother is Neha.'")
    print("Type 'show tree' to visualize, 'save' to save data, or 'exit' to quit.\n")

    # Load old data if exists
    family_tree = load_tree()
    print(f"📂 Loaded {len(family_tree)} saved records.\n")

    # Restore old relationships into graph
    for child, rel in family_tree.items():
        if "father" in rel:
            G.add_edge(rel["father"], child, label="father")
        if "mother" in rel:
            G.add_edge(rel["mother"], child, label="mother")

    while True:
        user_input = input("🗣️  You: ")

        if user_input.lower() == "exit":
            print("👋 Exiting Family Tree Builder. Goodbye!")
            break

        elif user_input.lower() == "save":
            save_tree(family_tree)
            print("💾 Family tree saved successfully!")

        elif user_input.lower() == "show tree":
            visualize_tree()

        else:
            relation = extract_relationships(user_input)
            if relation:
                update_tree(relation)
                # Save new relationship in dictionary
                child = relation.get("child")
                if child:
                    family_tree[child] = {
                        "father": relation.get("father", ""),
                        "mother": relation.get("mother", "")
                    }
                print("✅ Relationship added and stored in memory.")
            else:
                print("⚠️ Could not understand the relationship. Try again.")


if __name__ == "__main__":
    main()
