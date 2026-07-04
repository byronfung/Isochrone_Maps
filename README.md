# Canada Isochronic Passage Chart

Streamlit app for a Canada-wide isochronic passage chart inspired by Francis Galton's 1881 travel-time map, using OpenStreetMap. The default origin is Toronto.

The app is published to https://isochronemaps-t38p9msumyvncyqearggv7.streamlit.app/

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Run the North America version with:

```bash
streamlit run northamerica.py
```

Run the worldwide version with:

```bash
streamlit run worldwide.py
```

Static cache CSVs for the North America and worldwide apps live in `cache/`. Rebuild them after airport or route-model edits with:

```bash
python build_cache_tables.py
```

The app uses a lightweight multimodal travel-time model to color Canada into passage-time bands from the selected origin. It does not require an API key.
