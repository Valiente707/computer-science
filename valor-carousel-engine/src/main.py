from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import click
import yaml
from rich.console import Console

from config.settings import get_settings
from src.content_engine import ContentEngine
from src.handoff_report import print_handoff, save_run_record
from src.image_generator import generate_images_sync
from src.models import CarouselPlan, ContentBrief, RunRecord
from src.overlay import apply_overlays
from src.postiz_client import PostizClient


console = Console()


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "run"


def _load_brief(
    brief_path: Path | None,
    topic: str | None,
    product: str | None,
    price: str | None,
) -> ContentBrief:
    if brief_path:
        data = yaml.safe_load(brief_path.read_text(encoding="utf-8"))
        return ContentBrief.model_validate(data)

    settings = get_settings()
    if not topic:
        raise click.UsageError("Provide --brief or --topic.")
    return ContentBrief(
        topic=topic,
        product=product or settings.product_name,
        product_url=settings.product_url,
        price=price or settings.product_price,
    )


@click.group()
def cli() -> None:
    """Valor TikTok carousel engine."""


@cli.command()
@click.option("--brief", "brief_path", type=click.Path(exists=True, path_type=Path))
@click.option("--topic", type=str)
@click.option("--product", type=str)
@click.option("--price", type=str)
@click.option("--dry-run", is_flag=True, help="Skip Postiz upload.")
def generate(
    brief_path: Path | None,
    topic: str | None,
    product: str | None,
    price: str | None,
    dry_run: bool,
) -> None:
    """Run the full pipeline: plan → images → overlay → Postiz draft."""
    settings = get_settings()
    brief = _load_brief(brief_path, topic, product, price)

    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_slugify(brief.topic)}"
    run_dir = settings.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    record = RunRecord(
        run_id=run_id,
        created_at=datetime.now(timezone.utc),
        brief=brief,
        dry_run=dry_run,
    )

    try:
        console.print("[bold cyan]1/4[/] Generating carousel plan…")
        plan = ContentEngine().generate(brief)
        record.plan = plan
        (run_dir / "plan.json").write_text(
            plan.model_dump_json(indent=2), encoding="utf-8"
        )

        console.print("[bold cyan]2/4[/] Generating 6 images…")
        raw_paths = generate_images_sync(plan, run_dir / "raw")
        record.slide_image_paths = raw_paths

        console.print("[bold cyan]3/4[/] Applying overlay and resizing to 1080×1920…")
        final_paths = apply_overlays(plan, raw_paths, run_dir)
        record.final_image_paths = final_paths

        if dry_run:
            console.print("[bold cyan]4/4[/] Dry run — skipping Postiz upload.")
        else:
            console.print("[bold cyan]4/4[/] Uploading to Postiz and creating draft…")
            client = PostizClient()
            uploads = client.upload_images(final_paths)
            record.postiz_upload_ids = [u.id for u in uploads]
            post = client.create_draft(plan, uploads)
            record.postiz_post_id = post.identifier
    except Exception as e:
        record.errors.append(f"{type(e).__name__}: {e}")
        save_run_record(record)
        console.print(f"[red]Pipeline failed:[/] {e}")
        raise

    save_run_record(record)
    print_handoff(record)


@cli.command("regen-images")
@click.option("--run", "run_id", required=True, type=str)
def regen_images(run_id: str) -> None:
    """Re-run the image engine against an existing plan."""
    settings = get_settings()
    plan_path = settings.output_dir / run_id / "plan.json"
    if not plan_path.exists():
        raise click.UsageError(f"No plan found at {plan_path}")
    plan = CarouselPlan.model_validate(json.loads(plan_path.read_text(encoding="utf-8")))
    run_dir = settings.output_dir / run_id
    raw_paths = generate_images_sync(plan, run_dir / "raw")
    apply_overlays(plan, raw_paths, run_dir)
    console.print(f"[green]Regenerated images for {run_id}.[/]")


@cli.group()
def runs() -> None:
    """Inspect past runs."""


@runs.command("list")
def runs_list() -> None:
    settings = get_settings()
    files = sorted(settings.runs_dir.glob("*.json"))
    if not files:
        console.print("No runs yet.")
        return
    for f in files:
        console.print(f.stem)


@runs.command("show")
@click.argument("run_id")
def runs_show(run_id: str) -> None:
    settings = get_settings()
    f = settings.runs_dir / f"{run_id}.json"
    if not f.exists():
        raise click.UsageError(f"No run record at {f}")
    console.print_json(f.read_text(encoding="utf-8"))


if __name__ == "__main__":
    cli()
