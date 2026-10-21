# Setup guide

How to install the Hub on one computer, start it, load data, connect an AI model, back it up, and upgrade it. You do not need to know how to program. You need to copy commands into a terminal.

The Hub runs on one computer. Nothing is put on the internet. The web page only opens on that computer, at `http://127.0.0.1:8080`.

## 1. What you need

- A Mac or a Windows PC.
- **Docker Desktop**, installed and running. Download it from https://www.docker.com/products/docker-desktop/. On Windows, accept the option to use WSL 2 when the installer asks.
- The `project` folder of this code. The team gives it to you as a zip file or through its private GitHub repository.
- An API key for an AI model, if you want to ask questions. You can set this up later (see section 6).

Open a terminal:

- **Mac:** open the Terminal app.
- **Windows:** open PowerShell from the Start menu.

Check that Docker works:

```
docker --version
docker compose version
```

Both should print a version number. If you get an error, start Docker Desktop and wait until it says it is running.

Then go into the `project` folder. The folder you go to must contain the file `docker-compose.yml`:

```
cd path/to/project
```

## 2. Create the `.env` file

The `.env` file holds the passwords and keys. It stays on this computer and is never committed to git or shown on any web page.

**Mac:**

```
cp .env.example .env
```

**Windows (PowerShell):**

```
Copy-Item .env.example .env
```

Now fill in four lines. Open `.env` in any text editor (TextEdit in plain-text mode, Notepad, or VS Code) and replace the empty or `changeme` values:

| Line | What to put |
|---|---|
| `POSTGRES_PASSWORD=` | A random password, letters and digits only |
| `HUB_APP_PASSWORD=` | A different random password, letters and digits only |
| `CHATBOT_RO_PASSWORD=` | A third random password, letters and digits only |
| `HUB_SECRET_KEY=` | A secret key (see below). It locks the saved AI keys. |

Use letters and digits only in the three passwords, because they are placed inside web addresses.

**Make the values with Docker.** This works on Mac and Windows with nothing else installed. Run it four times (the first time downloads a small image, so it takes a minute):

For a password:

```
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_hex(24))"
```

For `HUB_SECRET_KEY`:

```
docker run --rm python:3.12-slim python -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

The key is the single line of 44 characters ending in `=`. Copy that whole line.

Developers with `uv` installed can make the key like this instead. Do not use the computer's own `python`: it usually lacks the `cryptography` package.

```
cd backend
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
cd ..
```

Copy each printed value into the matching line in `.env`, with no spaces and no quotes, and save the file.

Keep these safe:

- **Do not lose `HUB_SECRET_KEY`.** If it changes, the saved AI keys can no longer be read. You would enter them again in Settings. Keep a copy of the whole `.env` file somewhere private.
- The passwords are used when the database is first created. Changing them in `.env` later does not change the database.
- Never email or share `.env`.

You can leave every other line as it is. The `DATABASE_URL` lines near the top are only for programmers working on the code. Docker ignores them. The other lines, such as `DISPLAY_ROW_CAP`, have sensible defaults. Each is explained in `.env.example`.

## 3. First start

```
docker compose up --build -d
```

The first run builds the app and downloads the database, which takes several minutes. When it finishes, check the three parts:

```
docker compose ps
```

You should see `db`, `api` and `nginx`, all running (`api` and `db` say `healthy`). Then open **http://127.0.0.1:8080** in a browser. You see the Hub with four pages: Chat, Upload, Dataset and Settings.

To check the app without a browser:

```
curl http://127.0.0.1:8080/api/health
```

This prints `{"status":"ok"}`. (On Windows PowerShell, use `curl.exe` instead of `curl`, or just open the address in a browser.)

If port 8080 is already used by another program, change the line `HUB_HTTP_PORT=8080` in `.env` to another free number such as `8090`, run the `up` command again, and use that number in the address.

Docker Desktop starts the Hub again by itself when the computer restarts, as long as Docker Desktop is set to start at login.

**Stop and start:**

```
docker compose down      # stops the Hub; your data stays
docker compose up -d     # starts it again (no --build needed)
```

`docker compose down -v` also deletes all data. Do not use `-v` unless you want a clean start.

## 4. Load the sample data (optional)

The team's synthetic sample files (fake people, 10 events, 293 attendance records) are inside the app. To load them:

```
docker compose exec api python -m app.samples
```

It prints one line per file and ends with how many files it skipped as already imported. Run it twice if you like: the second time it adds nothing. Open the Dataset page to see the 10 files. Do not load the samples into a database that holds real data.

To load your own files, use the Upload page (see the [user guide](user-guide.md)).

## 5. Reset to empty

To throw away everything and start fresh:

```
docker compose down -v
docker compose up --build -d
```

You then need an AI model again (section 6).

## 6. Add an AI model

Questions need an AI model. The Hub works with any provider that speaks the OpenAI-style API: ZotGPT Gateway, OpenAI, DeepSeek, or a custom address.

1. Open the **Settings** page.
2. Click **Add AI model**.
3. Fill in:
   - **Name:** any label, for example `DeepSeek`.
   - **Provider:** pick one. The base URL fills in for OpenAI and DeepSeek.
   - **Base URL:** for ZotGPT or Custom, type the address your provider gave you.
   - **Model:** the model name (the box suggests names once the key is saved and tested).
   - **API key:** paste the key. It is stored encrypted, and it is never shown again, only its last four characters.
   - **Allow sending query results to this AI:** leave it off unless the sponsor has agreed that the AI may see the result rows. See the [user guide](user-guide.md#4-who-sees-the-data-the-two-switches) for what this means.
4. Save, then click **Test** on the new card. **Connected** means it works.

The first model you add becomes the default. The ZotGPT address, JSON support and model names have not been verified yet (see [known limitations](known-limitations.md)).

**Optional, for developers:** to create a model automatically on first start, fill the `LLM_SEED_*` lines in `.env` before you first run the Hub. They are described in `.env.example`.

## 7. Back up and restore

All data is in the database, in a Docker volume named `<folder>_hub-pgdata`. Back it up before every upgrade and regularly. The volume is named after the folder, so keep the folder name `project` when you upgrade. If the Hub opens empty after an upgrade, the old data is in the old folder's volume (go back to that folder), or restore the backup.

**Back up** (writes `hub-backup.sql` in the current folder):

```
docker compose exec db pg_dump -U postgres --clean --if-exists -f /tmp/hub-backup.sql hub
docker compose cp db:/tmp/hub-backup.sql ./hub-backup.sql
```

The backup file contains attendee names and emails. Store it where only authorized staff can open it. Also keep your `.env`: the backup holds the saved AI keys in encrypted form, and only the same `HUB_SECRET_KEY` can unlock them.

**Restore** (replaces the current data with the backup):

```
docker compose stop api
docker compose cp ./hub-backup.sql db:/tmp/hub-restore.sql
docker compose exec db psql -U postgres -d hub -v ON_ERROR_STOP=1 -f /tmp/hub-restore.sql
docker compose start api
```

## 8. Upgrade

1. Back up (section 7).
2. Replace the `project` folder with the new version, but keep your `.env` file. Keep the folder name `project`: the data volume is named after it. If you use git: `git pull`.
3. Run:

   ```
   docker compose up --build -d
   ```

The database updates itself when the app starts, and your data stays. Check `.env.example` for new lines and add any that are missing to your `.env`.

## 9. Something is wrong

| Problem | What to do |
|---|---|
| `docker compose` is not found, or "Cannot connect to the Docker daemon" | Start Docker Desktop and wait until it is running. |
| The page does not open | Run `docker compose ps`. If a service is not running, run `docker compose logs api` and send the last lines to the team. Start-up errors name the setting and never print its value. |
| "Not connected" shows in the page header | The Hub server is not reachable. Run `docker compose up -d`. |
| `api` keeps restarting and the log says `HUB_SECRET_KEY must be a Fernet key` | The key is missing or not valid. Generate a new one (section 2). A new key means saved AI keys must be entered again. |
| The database refuses the password after you edited `.env` | The passwords only apply when the database is first created. Put the old values back, or reset (section 5, deletes data). |
| Port 8080 in use | Change `HUB_HTTP_PORT` in `.env` (section 3). |

## For developers

Running the code outside Docker (dev server, tests) is described in [`CLAUDE.md`](../CLAUDE.md) under "Commands" and in the [handoff guide](handoff.md).
