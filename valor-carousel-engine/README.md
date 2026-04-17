# Valor TikTok Carousel Engine

Automated 6-slide TikTok photo-carousel generator that drives sales for Valor
Promotions digital products. The operator picks up the generated draft on the
TikTok mobile app to attach a trending sound before publishing.

## Quick start

```bash
git clone <this-repo>
cd valor-carousel-engine

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in ANTHROPIC_API_KEY, OPENAI_API_KEY, POSTIZ_API_KEY,
# POSTIZ_TIKTOK_INTEGRATION_ID. See "Getting the Postiz integration ID" below.

# Dry run (no Postiz upload — writes PNGs + run record only)
python -m src.main generate --brief briefs/example_starter_kit.yaml --dry-run

# Full run (creates a TikTok draft)
python -m src.main generate --brief briefs/example_starter_kit.yaml
```

Within ~60 seconds the draft appears in the TikTok mobile app under
**Profile → Drafts** on the account owner's phone. Open it, pick a trending
sound, publish.

## Getting the Postiz integration ID

```bash
curl -H "Authorization: $POSTIZ_API_KEY" \
     https://api.postiz.com/public/v1/integrations
```

Find the TikTok integration in the response and copy its `id` into
`POSTIZ_TIKTOK_INTEGRATION_ID` in `.env`.

## CLI reference

```bash
python -m src.main generate --brief briefs/example_starter_kit.yaml
python -m src.main generate --topic "..." --product "..." --price "$42"
python -m src.main generate --brief briefs/example.yaml --dry-run
python -m src.main regen-images --run <run_id>
python -m src.main runs list
python -m src.main runs show <run_id>
```

## Running tests

```bash
pip install -e '.[dev]'
pytest -q
```

All network calls are mocked. Tests complete in under 30 seconds.

## Project layout

```
valor-carousel-engine/
├── CLAUDE.md                  # Operating rules for Claude Code
├── README.md                  # You are here
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── config/
│   ├── settings.py            # Loads/validates .env
│   └── prompts/               # System prompts
├── fonts/
│   └── Inter-Bold.ttf         # Run scripts/fetch_font.sh if missing
├── src/
│   ├── main.py                # Click CLI entrypoint
│   ├── content_engine.py      # Anthropic
│   ├── image_generator.py     # OpenAI Images (async)
│   ├── overlay.py             # Pillow text overlay
│   ├── postiz_client.py       # Postiz REST
│   ├── tiktok_direct.py       # Appendix A fallback
│   ├── handoff_report.py      # Summary + Slack
│   └── models.py              # Pydantic schemas
├── briefs/
│   └── example_starter_kit.yaml
├── output/                    # Gitignored — generated images
├── runs/                      # Gitignored — run logs
└── tests/
```

## Cost per carousel

At default settings (gpt-image-1.5, medium quality, 1024×1536):

- 6 images × $0.05 = **$0.30**
- Claude Sonnet content gen: **~$0.02**
- **Total: ~$0.32 per carousel**

Use `IMAGE_MODEL=gpt-image-1-mini` during testing for ~70% savings.

## Migrating this code to its own GitHub repo

This project currently lives as a subdirectory inside the
`valiente707/computer-science` repo because the session that created it was
scoped to that repo. To split it out:

```bash
# From the root of valiente707/computer-science
git subtree split --prefix=valor-carousel-engine -b valor-standalone

# Create the new repo on GitHub (UI or `gh repo create`), then:
git push git@github.com:<you>/valor-carousel-engine.git valor-standalone:main
```

After the split, the new repo's history only contains commits that touched
`valor-carousel-engine/`.

## Hard rules

- Every post uses `type: "draft"` on Postiz. No direct publishing.
- Every post sets `video_made_with_ai: true`. TikTok policy.
- Exactly 6 slides, exactly 5 hashtags.
- No faces in generated images (prompt suffix enforces this).
- No hardcoded API keys anywhere. All secrets come from `.env`.
