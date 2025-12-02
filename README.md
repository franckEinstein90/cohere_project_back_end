# Flask API Back-end

This repository contains a Flask-based API. The development entrypoint is `main.py`.

## Quick start (development)

1. Activate the virtual environment:

```bash
source .venv/bin/activate
```

2. (Optional) Install dependencies if not already installed:

```bash
pip install -r requirements.txt
```

3. Run the application directly (development server):

```bash
python main.py
```

The server will start on port 5000 by default. Visit `http://localhost:5000/ping` to verify.

## Using Flask CLI (factory support)

`main.py` exposes a `create_app()` factory. To run using the Flask CLI:

```bash
export FLASK_APP="main:create_app"
export FLASK_ENV=development
flask run --no-debugger --no-reload
```

Note: `--no-reload` is recommended when debugging from VS Code so the debugger attaches to the correct process.

## VS Code debugging

A `.vscode/launch.json` was added with two configurations:

- "Python: Run main.py" — runs `main.py` directly.
- "Python: Flask (module)" — launches Flask as a module (uses `FLASK_APP=main:application` by default; if you've switched to the factory pattern, update that to `main:create_app`).

Make sure to select the interpreter at `.venv` in VS Code before debugging.

## Production

For production use, consider a WSGI server such as Gunicorn and environment variables for configuration. Example:

```bash
# install gunicorn
pip install gunicorn
# run
gunicorn --bind 0.0.0.0:8000 "main:create_app()"
```

## Notes

- The repository already contains a `.venv` virtual environment and `requirements.txt` with basic dependencies.
- Keep secrets out of the repo; use environment variables or a secrets manager.
