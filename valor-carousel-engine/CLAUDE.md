# CLAUDE.md — Valor TikTok Carousel Engine

> **Project:** `valor-carousel-engine`
> **Purpose:** Automated TikTok photo carousel generator that promotes Valor Promotions digital products (starting with The Ultimate AI Business Starter Kit — $42).
> **Owner:** Valor — Valor Promotions
> **Environment:** Standalone Python 3.11+ app. Runs locally or on a VPS. Built by Claude Code.

---

## 1. What this app does (one paragraph)

It takes a short content brief (topic + product being promoted), generates a 6-slide TikTok photo carousel with AI-generated images and text overlays, writes a story-style caption with ≤5 hashtags, uploads everything to Postiz, and creates a **TikTok draft** so the human operator can attach a trending sound before publishing. Drafts, not direct posts. Music gets added manually because TikTok's Content Posting API does not allow adding sounds — this is by design and not a bug.

---

## 2. Architecture

```
content_brief.yaml
    → content_engine.py   (Anthropic → carousel_plan.json)
    → image_generator.py  (OpenAI gpt-image-1.5 → 6 PNGs)
    → overlay.py          (Pillow → hook text on slide 1, resize to 1080x1920)
    → postiz_client.py    (6 uploads + 1 draft post)
    → handoff_report.py   (run log + optional Slack)
```

---

## 3. Folder structure

See project tree. Key modules live in `src/`; prompts in `config/prompts/`;
example briefs in `briefs/`.

---

## 4. Locked rules (do NOT deviate)

- `type: "draft"` on every Postiz post — never `"now"` or `"schedule"`.
- `video_made_with_ai: true` — TikTok policy requirement for AI images.
- Exactly 6 slides. Exactly 5 hashtags.
- `privacy_level: SELF_ONLY` for drafts.
- No DALL·E. Only the `gpt-image-*` family.
- No faces in generated images (prompt suffix enforces this).
- No direct TikTok posting unless Postiz rejects the payload
  (see `src/tiktok_direct.py` for the fallback path).

For full spec see the README and the top-level spec Valor provided at project
kickoff.
