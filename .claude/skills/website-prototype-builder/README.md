# Website Builder

A Claude Code **skill** that turns a company name + a handful of customer reviews into a
production-ready, single-page cinematic landing site — and can optionally publish it to a live
URL via Vercel.

The skill (`website-prototype-builder`) acts as a senior brand strategist, conversion
copywriter, and web designer: it auto-detects the business vertical, mines the reviews for
voice-of-customer language, applies a matching design system, and ships a self-contained HTML
file with dual CTAs, accessibility, and SEO baked in.

## What it produces

1. **`outputs/{company-slug}-landing.html`** — a complete, self-contained landing page (inline
   CSS + JS, Google Fonts via CDN). Opens in any browser, no build step. Also written as
   `outputs/{company-slug}-site/index.html` so it's deploy-ready.
2. **`outputs/{company-slug}-prompt.md`** — a portable copy of the master build prompt,
   pre-filled for the client, so you can iterate in Lovable, v0, Bolt, Cursor, etc.
3. **(optional) a live `.vercel.app` URL** — when the Vercel MCP integration is connected.

## Install

Claude Code auto-loads skills from `.claude/skills/`, so just clone this repo (or copy the
`.claude/skills/website-prototype-builder/` folder into your project) and open it with Claude
Code:

```
git clone <this-repo> && cd website-builder
```

The skill registers automatically. Invoke it with `/website-prototype-builder`, or just ask
naturally, e.g.:

> Build a landing page for **Lumière Med Spa** in Charlotte, NC. Here are 12 reviews: …

You must provide a **company name** and **at least 5 reviews**. Location, CTA text, and a phone
number are optional but recommended.

## Optional integrations

Both are self-disabling — the skill fully works without them and skips silently if they're not
present.

### Live research (Perplexity)
Set a Perplexity API key in your environment to let the skill pull live 2026 design/conversion
research and fold it into the build:

```bash
export PERPLEXITY_API_KEY="pplx-..."
```

If unset, the skill relies on its internal design knowledge.

### Live deploy (Vercel)
Connect the **Vercel MCP** in your Claude Code session. When available, the skill can deploy the
generated site to a live preview URL (`deploy_to_vercel`), diagnose failed builds
(`get_deployment`), import the bundle into Vercel's design editor
(`import-claude-design-from-url`), and suggest available domains
(`check_domain_availability_and_price`). Deployment is outward-facing, so the skill always asks
for confirmation first and never auto-purchases a domain.

## Files

```
.claude/skills/website-prototype-builder/
├── SKILL.md                      # the skill definition / build procedure
└── references/
    └── master-prompt.md          # portable build prompt for other AI builders
```

## Security note

An earlier version of `SKILL.md` shipped with a hardcoded live Perplexity API key. It has been
**removed** — the research step now reads `PERPLEXITY_API_KEY` from the environment. Do not
reintroduce hardcoded secrets. If you cloned an older copy that contained the key, rotate that
key.
