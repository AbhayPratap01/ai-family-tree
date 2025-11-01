import streamlit as st
import json, os, re, requests
import networkx as nx
import matplotlib.pyplot as plt

# ---------- Setup ----------
st.set_page_config(page_title="AI Family Tree", page_icon="🌳", layout="centered")

FAMILY_FILE = "family_tree.json"

# ---------- Utility Functions ----------
def load_tree():
    if os.path.exists(FAMILY_FILE):
        with open(FAMILY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tree(tree):
    with open(FAMILY_FILE, "w") as f:
        json.dump(tree, f, indent=4)

def extract_relationships(text):
    relation = {}
    text = text.lower()

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

def visualize_tree(tree):
    G = nx.DiGraph()
    for child, rel in tree.items():
        if "father" in rel and rel["father"]:
            G.add_edge(rel["father"], child, label="father")
        if "mother" in rel and rel["mother"]:
            G.add_edge(rel["mother"], child, label="mother")

    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=2000, font_size=10, font_weight="bold")
    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    st.pyplot(plt)

# ---------- Streamlit UI ----------
st.title("🌳 AI Family Tree Builder (TinyLlama Edition)")
st.write("Enter relationships like `Abhay's father is Raj and mother is Neha.`")

tree = load_tree()

with st.form("relationship_form"):
    user_input = st.text_input("🗣️ Add a relationship:")
    submit = st.form_submit_button("Add")

if submit and user_input.strip():
    rel = extract_relationships(user_input)
    if rel:
        child = rel.get("child")
        if child:
            tree[child] = {
                "father": rel.get("father", ""),
                "mother": rel.get("mother", "")
            }
            save_tree(tree)
            st.success(f"✅ Added relationship for {child}")
    else:
        st.warning("⚠️ Could not understand the relationship. Try again!")

if st.button("Show Family Tree"):
    if tree:
        visualize_tree(tree)
    else:
        st.info("No relationships added yet.")

if st.button("Reset All Data"):
    if os.path.exists(FAMILY_FILE):
        os.remove(FAMILY_FILE)
        st.warning("🗑️ All data cleared. Restart app to see changes.")
