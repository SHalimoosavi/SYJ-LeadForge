# Plugins

This directory holds **example** plugins shipped with the project — they
don't load automatically. See [`docs/PLUGIN_GUIDE.md`](../docs/PLUGIN_GUIDE.md)
for the full plugin API and how to actually install one.

Quick version:

```bash
# find your plugin directory
leadforge doctor   # shows "data dir"

# copy an example in
cp plugins/examples/restaurant_pack.py ~/.leadforge/plugins/

# confirm it loaded
leadforge plugins
```

## What's here

- `examples/hello_world.py` — minimal template demonstrating every hook; start here if you're writing your own.
- `examples/restaurant_pack.py` — industry pack for restaurants/cafes: category weight bump, checks for a menu and online ordering, recommends adding them.
- `examples/legal_pack.py` — industry pack for law firms: category weight bump, checks for practice-area content and attorney bios.

A community plugin registry (a searchable index of third-party plugins) is on the roadmap but not built yet — for now, share plugins as a file or a small pip-installable package using the `leadforge.plugins` entry-point group (also documented in the Plugin Guide).
