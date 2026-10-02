# AI Family Tree

A local-first family-tree builder with a Streamlit interface, an interactive generation chart, and an optional Ollama language-model fallback.

## Run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`. The command-line interface is also available with `python interactive_family_tree.py`.

## Add relationships

Choose an existing person or add a new name, then choose whether the first person is the second person's father, mother, brother, or sister. Existing family members are offered in dropdowns to avoid spelling duplicates. The plain-English description is still available under the optional advanced section for phrases such as `Abhay's dad is Raj` or `Abhay and Mira share the same parents`.

Relationships are saved in `family_tree.json` using the existing child-to-parent structure, with sibling lists added compatibly for family members. The app prevents conflicting parent assignments and cycles; removing a person clears their parent and sibling references from the remaining tree.

Ollama is optional and is not required by other users. It runs on the machine hosting the app, not on each visitor's device. A hosted app can use Ollama only when that host has a reachable Ollama service and model; otherwise the dropdown workflow and built-in phrase parser work without an SLM.

## Deploy

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=AbhayPratap01/ai-family-tree&branch=main&mainModule=app.py)

This opens Streamlit Community Cloud's deployment setup for the public GitHub repository. Sign in with GitHub and select `app.py` as the entry point. A live deployment has not been created from this workspace; local changes must be published to GitHub before Cloud can deploy them.

**Data warning:** the current JSON file is a single shared local data store, not a production multi-user database. Do not publish real family data or use the public demo for private records. A production launch needs authenticated users and per-user persistent storage.

## Test

```powershell
python -m pip install pytest
python -m pytest -q
```

`python test_ollama.py` is an optional connectivity check and requires Ollama with the `tinyllama` model installed. It is not run during normal test collection.