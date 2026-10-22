# Program Registration & Attendance Data Hub

A small web app for UCI's Graduate & Postdoctoral Scholar Resource Center (GPSRC). Staff upload the attendee exports from CampusGroups and 12twenty, and the Hub builds one dataset and links the same person across events. Staff then ask questions in plain English ("How many unique postdocs came to any wellness event?"). An AI writes the database query, the Hub runs it read-only, and it shows the query and the result table, with Excel and CSV download.

It runs on one staff computer, with Docker. No data goes to the internet except what you choose to send to the AI model (see the [user guide](docs/user-guide.md#4-who-sees-the-data-the-two-switches)). SWE 277P capstone, Fall 2026. Sponsor: Kayleigh Anderson-Natale, PhD.

![A question, its answer, the SQL and the download buttons](docs/screenshots/03-chat-answer.png)

## Quick start

You need Docker Desktop (Mac or Windows) running. From this folder (`project/`):

```
cp .env.example .env
# open .env and fill in the three passwords and HUB_SECRET_KEY (setup guide, section 2)
docker compose up --build -d
docker compose exec api python -m app.samples    # optional: load the fake sample data
```

Then open http://127.0.0.1:8080. In **Settings**, click **Add AI model** to connect an AI provider, then ask questions in **Chat**. Stop it with `docker compose down` (your data stays).

The full steps, including how to make the secrets, back up, and upgrade, are in the [setup guide](docs/setup-guide.md).

## Documentation

| Read this | If you are |
|---|---|
| [Setup guide](docs/setup-guide.md) | Installing or upgrading the Hub, adding an AI model, backing up |
| [User guide](docs/user-guide.md) | Staff using the Hub: uploads, flags, questions, answers, downloads, the privacy switches |
| [Data dictionary](docs/data-dictionary.md) | Wondering what each column means or how an export maps to the dataset |
| [Known limitations](docs/known-limitations.md) | Deciding how far to trust an answer, or what is not done yet |
| [Handoff guide](docs/handoff.md) | Taking over the code: architecture, tests, extension points, backlog, moving to OIT |
| [Spec](docs/specs/2026-10-20-data-hub-design.md) | Needing the full design and its reasons |
| [Benchmark results](docs/benchmark-results.md) | Checking how well the chatbot answered the benchmark questions |
| [`CLAUDE.md`](CLAUDE.md), [`PROGRESS.md`](PROGRESS.md) | Working on the code with Claude Code: commands, rules, current state |

## Layout

```
docker-compose.yml   nginx + api + db        .env.example   settings to copy to .env
backend/             FastAPI app, Alembic migrations, sample data, tests, chatbot benchmark
frontend/            React + TypeScript app, nginx config, Playwright tests
db/init/             creates the database roles on first start
docs/                guides, spec, plans, design, benchmark results, screenshots
```

## Privacy in one paragraph

The Hub holds attendee names and emails, so keep the computer and backups protected. There is no login yet (see [known limitations](docs/known-limitations.md#no-login)). The AI that writes the queries never sees attendee rows or Student IDs. If you turn on result sharing, the AI also sees the rows a query returned, which can include names and emails. Whether that is allowed has not been confirmed with the sponsor, and it can be switched off per AI model in Settings. It starts off for every provider except the ZotGPT preset. All sample and test data is synthetic.
