# schema-drift

> Detect and report schema changes in databases over time with a diffable changelog format.

---

## Installation

```bash
pip install schema-drift
```

---

## Usage

Capture a snapshot of your database schema and compare it against a previous baseline to detect drift.

```bash
# Take an initial snapshot
schema-drift snapshot --db postgresql://user:pass@localhost/mydb --output schema.json

# Compare against a previous snapshot and generate a changelog
schema-drift diff --before schema_v1.json --after schema_v2.json

# Watch for changes and output a diffable report
schema-drift watch --db postgresql://user:pass@localhost/mydb --interval 60
```

Example diff output:

```diff
[2024-03-15] Schema changes detected in database: mydb

+ TABLE orders
+   COLUMN discount DECIMAL(10,2) DEFAULT 0.00
- TABLE sessions
~   COLUMN user_id INT → BIGINT
```

You can also use `schema-drift` as a library:

```python
from schema_drift import SchemaWatcher

watcher = SchemaWatcher(dsn="postgresql://user:pass@localhost/mydb")
changelog = watcher.diff(previous="schema_v1.json", current="schema_v2.json")
print(changelog.render())
```

---

## Configuration

Create a `schema-drift.toml` file in your project root to set defaults:

```toml
[database]
dsn = "postgresql://user:pass@localhost/mydb"

[output]
format = "diff"   # options: diff, json, markdown
```

---

## License

This project is licensed under the [MIT License](LICENSE).