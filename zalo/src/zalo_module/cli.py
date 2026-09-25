"""Command line entrypoint — decision sheet section 7.

    python -m zalo_module.cli migrate
    python -m zalo_module.cli replay <event.json>
    python -m zalo_module.cli status
    python -m zalo_module.cli serve [--port N]

Every command loads settings from env (see ``settings.get_settings``) and
configures the audit log first so runtime file accesses land in
``runtime_root/access.jsonl``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import func, select

from zalo_module import audit
from zalo_module.database import (
    get_engine,
    init_db,
    run_migrations,
    session_scope,
)
from zalo_module.models import JournalEntry
from zalo_module.settings import get_settings


def _cmd_migrate(_args) -> int:
    settings = get_settings()
    audit.configure(settings.access_log_path)
    engine = get_engine(settings)
    # init_db() delegates to run_migrations; calling it directly yields the
    # applied count the contract asks us to print.
    applied = run_migrations(engine)
    print(json.dumps({"applied": applied}))
    return 0


def _cmd_replay(args) -> int:
    event_path = Path(args.event_json)
    event = json.loads(event_path.read_text(encoding="utf-8"))
    settings = get_settings()
    audit.configure(settings.access_log_path)
    engine = get_engine(settings)
    init_db(engine)

    from zalo_module.intake.journal import capture_event, source_key

    skey = source_key(event)
    with session_scope(engine) as session:
        existed = session.execute(
            select(func.count())
            .select_from(JournalEntry)
            .where(JournalEntry.source_key == skey)
        ).scalar_one()
        capture_id = capture_event(event, session, settings)
    print(
        json.dumps(
            {
                "capture_id": capture_id,
                "source_key": skey,
                "created": existed == 0,
            }
        )
    )
    return 0


def _cmd_status(_args) -> int:
    """Print the intake.service-status.v1 document.

    Goes through the real app + endpoint (TestClient) so the CLI can never
    drift from what ``serve`` returns over HTTP.
    """
    settings = get_settings()

    from fastapi.testclient import TestClient

    from zalo_module.app import create_app

    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.get("/intake/v1/status")
    if resp.status_code != 200:
        print(resp.text, file=sys.stderr)
        return 1
    print(json.dumps(resp.json(), ensure_ascii=False))
    return 0


def _cmd_serve(args) -> int:
    settings = get_settings()

    # Decision sheet §2: serve requires a registered consumer — fail fast
    # rather than accepting requests for a consumer we cannot authenticate.
    if not settings.consumer_id:
        print(
            "error: ZALO_INTAKE_CONSUMER_ID is not set — serve requires a "
            "registered consumer id (see .env.example)",
            file=sys.stderr,
        )
        return 2

    import uvicorn

    from zalo_module.app import create_app

    app = create_app(settings)
    uvicorn.run(app, host=settings.bind, port=args.port or settings.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zalo_module.cli",
        description="Zalo intake module — independent runtime CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="apply pending DB migrations")

    replay = sub.add_parser("replay", help="journal a raw listener event file")
    replay.add_argument("event_json", help="path to a JSON event file")

    sub.add_parser("status", help="print intake.service-status.v1 JSON")

    serve = sub.add_parser("serve", help="run the FastAPI app (loopback)")
    serve.add_argument(
        "--port",
        type=int,
        default=None,
        help="override ZALO_INTAKE_PORT",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = {
        "migrate": _cmd_migrate,
        "replay": _cmd_replay,
        "status": _cmd_status,
        "serve": _cmd_serve,
    }[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
