## ПРАВИЛА ОТВЕТА (ОБЯЗАТЕЛЬНЫЕ)

- Всегда отвечать на русском (кириллицей), без транслитерации.
- Максимально кратко, по делу, без воды и лишних слов.
- В каждом сообщении обращаться по имени: Yusif.

---

# Project notes

## Web search fallback

The built-in `WebSearch` tool may fail in this environment (model served via a non-Anthropic gateway, e.g. Fireworks GLM) with a `400` error mentioning tool type `web_search_20250305`. When `WebSearch` fails or is unavailable, use the shared local SearXNG — do not give up on web search.

- Search via Bash/curl:
  ```bash
  curl -s "http://localhost:8888/search?q=<urlencoded-query>&format=json&categories=generalformat=json&engines=bing,yandex,mojeek,brave,presearch"
  ```
- If `localhost:8888` is unreachable, recreate the shared container:
  ```bash
  docker run -d --name searxng-claude --restart unless-stopped -p 8888:8080 \
    -v "C:/Users/yusif/Desktop/projects/saas-autonomous-team/searxng-claude/settings.yml:/etc/searxng/settings.yml:ro" \
    searxng/searxng:latest
  ```
- `WebFetch` (direct URL fetch + summarization) works independently and needs no fallback.

---

# АКТИВНЫЕ ЗАДАНИЯ (память проекта)

Сегодня: 2026-06-30. Все дедлайны submit < 20 дней. Это папка №1 — **Solana / agent skills / QA / мини-хак**. Работать по двум объявлениям ниже. Приоритет: код и сабмит.

## 1. B17 — Break It Before Users Do: MultiHopper Agentic Flow Bugs & Fixes
- **Платформа:** Superteam Earn (Multihopper / Enigma Fund)
- **Дедлайн submit:** 2026-07-10 (осталось ~10 дней)
- **Приз:** 1000 USDC (250 × 4 победителям)
- **Что хотят:** ответственное тестирование MultiHopper API в agentic-воркфлоуах — найти баги и предложить фиксы. MultiHopper — programmable multi-hop token routing infra на Solana (планируемые транзакции/роутинг). Skills: Development, Solana, AI Agents, Security/QA.
- **URL:** https://earn.superteam.fun/listings/multihopper/break-it-before-users-do-multihopper-agentic-flow-bugs-and-fixes

## 2. B19 — Superteam Nepal Mini Hack
- **Платформа:** Superteam Earn (Superteam Nepal)
- **Дедлайн submit:** 2026-07-15 (осталось ~15 дней)
- **Приз:** 850 USDC (350 / 250 / 100 / 50 / 20…)
- **Что хотят:** выбрать реальную проблему и построить Solana-апп (vibecode допустим). Акцент на Token Extensions, Solana Mobile, State Compression, быстрые RPC, dev-tooling.
- **Требования:** ссылка на Demo Video + ссылка на Github Repo.
- **URL:** https://earn.superteam.fun/listings/superteamnp/superteam-nepal-mini-hack
