from __future__ import annotations

import json

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import get_settings
from src.models import RunRecord


console = Console()


def save_run_record(record: RunRecord) -> None:
    settings = get_settings()
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    dest = settings.runs_dir / f"{record.run_id}.json"
    dest.write_text(record.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")


def print_handoff(record: RunRecord) -> None:
    settings = get_settings()

    table = Table(title=f"Run {record.run_id}", show_header=False, padding=(0, 1))
    table.add_row("Topic", record.brief.topic)
    table.add_row("Product", record.brief.product)
    if record.plan:
        table.add_row("Hook", record.plan.slides[0].overlay_text)
        table.add_row("Caption", record.plan.caption[:120] + ("…" if len(record.plan.caption) > 120 else ""))
        table.add_row("Hashtags", " ".join(record.plan.hashtags))
    table.add_row("Images", str(len(record.final_image_paths)))
    table.add_row("Postiz draft", record.postiz_post_id or ("skipped (dry run)" if record.dry_run else "not created"))
    console.print(table)

    if record.dry_run:
        console.print(
            Panel.fit(
                "[yellow]Dry run complete. No Postiz upload performed.[/]",
                title="Handoff",
            )
        )
        return

    if record.postiz_post_id:
        console.print(
            Panel.fit(
                "[green]TikTok draft created on Postiz.[/]\n\n"
                "[bold]Next step:[/] open the TikTok app on the phone → "
                "[bold]Profile → Drafts[/]. Attach a trending sound and publish.",
                title="Handoff",
            )
        )

    if settings.slack_webhook_url:
        _send_slack(record, settings.slack_webhook_url)


def _send_slack(record: RunRecord, webhook_url: str) -> None:
    hook_text = record.plan.slides[0].overlay_text if record.plan else ""
    lines = [
        f"*New Valor TikTok draft:* `{record.run_id}`",
        f"*Topic:* {record.brief.topic}",
        f"*Hook:* {hook_text}",
        f"*Product:* {record.brief.product}",
        "Open TikTok → Drafts → add trending sound → publish.",
    ]
    try:
        requests.post(
            webhook_url,
            json={"text": "\n".join(lines)},
            timeout=10,
        )
    except requests.RequestException as e:
        console.print(f"[yellow]⚠ Slack webhook failed: {e}[/]")
