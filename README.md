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

## Front-end

This project has a separate front-end repository available at:

https://github.com/franckEinstein90/cohere_project_front_end/tree/main


## Query endpoint

POST /api/v1/<tool_id>/query

This endpoint accepts a JSON body matching the following schema:

```json
{
	"user_prompt": "<string>"
}
```

On success the endpoint returns a JSON object like:

```json
{
	"tool_id": "<tool_id>",
	"received": {"user_prompt": "..."},
	"status": "queued"
}
```

If the request body is not JSON, the endpoint returns 400. If the JSON
is syntactically valid but fails validation (for example `user_prompt` is
missing or not a string), the endpoint returns 422 with validation details.

Optional conversation history

You may include an optional `conversation` field containing a list of prior turns. Each turn must be an object with `role` (either `user` or `assistant`) and `content` (string). Example:

```json
{
	"user_prompt": "followup question",
	"conversation": [
		{"role": "user", "content": "Hello"},
		{"role": "assistant", "content": "Hi — how can I help?"}
	]
}
```

When `tool_id` is `system`, the validated `conversation` (if present) is forwarded to the system processor along with the `user_prompt` and `system` description. The processor receives the conversation as a list of objects and may use it when producing a response.


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
