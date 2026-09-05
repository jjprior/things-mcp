# Things 3 MCP Integration Horcrux

> **Canonical source.** This file on disk is the source of truth. Sync it into the
> "Goals and Tasks" Claude project knowledge after edits. Last refreshed: 2026-05-29
> (post May-2026 intentions restructure).

## TL;DR - Read This First

**Someday handling (UPDATED 2026-05-29):**
- The MCP now **excludes Someday by default** across `get_today`, `get_upcoming`,
  `get_anytime`, `get_todos`, and `search_advanced`. It catches BOTH tasks whose own
  start is `Someday` AND tasks inside a Someday project.
- To **flag in** parked items, pass `include_someday=True` (e.g. review step 5,
  activation candidates). `get_someday` always shows the parking lot.
- **In review/triage sessions: do NOT open with or dwell on Someday.** It is an
  intentional parking lot. Surface it only at the end as activation candidates, or
  when explicitly asked.

**Orphan tasks = inbox items (ADDED 2026-05-29):**
- A task sitting **directly in an area with no parent project** is treated as
  **unprocessed** — same status as an Inbox item. Jack routinely drags incomplete
  Inbox items into their area to deal with later, so area-level loose tasks are a
  to-process queue, not finished filing.
- In reviews: surface orphan/area-level tasks alongside the Inbox and triage them
  into a project (or Someday) rather than leaving them loose in the area.

**Status hierarchy (check in this order):**
1. Has `start_date` in future? → **Upcoming**
2. `start` = "Someday" OR inside a Someday project? → **Someday** (now filtered by default)
3. `start` = "Anytime"? → **Anytime** (active)
4. In Today view? → **Today**

**API blind spots:** Recurring task templates invisible. Trust screenshots over API.

---

## Session Bootstrap (efficiency)

At the start of a Things session, batch-load tools in ONE pass rather than trickling:
- `tool_search "things today anytime upcoming someday projects areas todos update add search"`
  → gets the full Things read/write set.
- `tool_search "filesystem read write edit"` if touching `~/Developer`.
Then rely on the UUID tables below instead of `get_projects` (which dumps ~150 rows).

---

## Key UUIDs (Eliminate Search Cycles)

### Areas (current as of 2026-05-29)
| Area | UUID | Notes |
|------|------|-------|
| Sanofi | TyBLncnyrdNTZGxfYsFLnm | |
| BioMetre | HYxV5Q3ogUgAqd4XSRzS1C | **UUID changed** (was AhbxHeTDyso5NJTx3AHuVE) |
| Thought Leader | BsvdgMWLEFTrUBGEQAgMnb | |
| PDA | FQ7rFuW8DFHdYE8itDN26 | new |
| MIT INM | CcBiJYanyeh9KitUNpFjTr | new |
| LGO | 7QY4b3Cf7dQXNftA7UkRLY | new |
| Next Role | Jna1qe2otTVZmzKpkPDJpi | |
| Digital Gemba | 5Qu5UWsAewaSHVK9YzrxUg | new in table |
| Father | 5Med76XbcEnPJqsz4ENxM3 | |
| Husband | R4zD9au1rHQgbzLEcQQ7rB | |
| Son | 35BoRvxUMGARdgxWuvFADF | was "Woodbury" |
| Nephew | CUGgXcpcZkiLGDjtVnTxiu | was "Pat" |
| Friends | 7ZD3Lg4qfzuGkAhhhEG6Ui | |
| Fig City News | Sn2EcSWW1qwYkoSYjS5Y55 | was "Fig City" |
| Homeowner | VFfdfGFEngJj5iz2f5hCYv | was "Chesley Rd" |
| Financial | Ui85eeqQ4jfE3wpgxJbTC7 | |
| Healthy | 9RktaHBAun7GGz5SdUviBh | |
| Templates | 88ZYnJU8mQxVFwejVsn1uK | utility |

(Removed: **Rotary** — area no longer exists; 2026 Citizen role is Fig City News only.)

### Goal / Intention Projects
Convention: `(i)` = intention-target project; numbered `2a`–`5d` = Sanofi Workday goals; `(g)` in intentions.yaml = formal goal.

**Sanofi**
| Project | UUID |
|---------|------|
| 2a. Partner with Guillaume (process performance) | 3GNeWNtsnQbRdDsiZDskiF |
| 2b. Support MSAT as guardian of process capability | H1Ny3KdpiAUkrnvtrbSemh |
| 2c. Define DSD role | 2vossD1zwxp8eDbHprMMVp |
| 3a. Simply Yield (90% DS coverage) | D6h3PCex7kn3kpcjtKAS6D |
| 3b. SeeQ/VIE supervision → MBC MVP | H5g4gQPQ9WKHYF3eV6PoZf |
| 3c. Digital Twins (support ICB) | Vg9HAb4uvMMmQiqgTpxnGt |
| 3d. aMAB synthetic data set | QCA1fKhGLAiaSTWoT5NYye |
| 3e. eCOA next steps | CRBsfeXN7nDpVDxpMqtujX |
| 5a. Check-ins and review | 6iKWBZeBVEf7c6Y2XGpiE6 |
| 5b. Development plan updated | U5oH6F31N43WRsigETS2Vw |
| 5c. Mentoring sustained | 8aiiad7ZtxD6ypDbxceKw8 |
| Process Monitoring & Data Science | UNZRT3zoGzrs8omy6doDAi |
| Leadership skills developed | 57VvqawSy6jYD5Kzktzrrh |

**Thought Leader / BioMetre / PDA / MIT INM / LGO**
| Project | UUID | Area |
|---------|------|------|
| 1a. BioMetre scoring cycles | 9LQA7z2P5v1CuRymdED2aq | BioMetre |
| 1b. Deliver published manuscript | QgkYQYjPij25QgToGhjiak | BioMetre |
| 4c. MIT BioMAN benchmarking launch | CxuNznJRiYVqEo6LrD1NbJ | BioMetre |
| BioMetre framework for external audiences (i) | 5XWdHdpFQHvzXr3QbbY6pd | BioMetre |
| Analytics Scorecard published (i) | MdRNKfL5VWMagp7o7qmpvA | BioMetre |
| 1c. Barcelona and PDA presentations | DSfuY9T13UpWP6hGZnMJDW | Thought Leader |
| Digital twin vision deck (i) | QR7ZkkR4pTraPgoLWPF32g | Thought Leader |
| Jackprior dot ai posted | 2KGtdqFdmJ33DZh34DwRkp | Thought Leader |
| SAB/PDA active participation (i) | SvXywM7rjDDdERaxdWmjBn | PDA |
| 5d. Contribute/Influence via PDA SAB | TSCjFaDhTaWYHV1s2WyZbt | PDA |
| 4b. Engage with INM (AI rep/interim) | WFzMqxff1TC1Y4VGMLpjx7 | MIT INM |
| 4b.1 John Carrier Lean group | 26cRUDv1RMqYdkjgmx6dZN | MIT INM |
| 4b.2 ai-mab.org launched (i) | 69ggKWLBXyHgE2kdwNJEBP | MIT INM |
| 4a. Manage MIT LGO relationships | TEfz3K4hyeGtVLX4mQxovb | LGO |

**Next Role (i)**
| Project | UUID |
|---------|------|
| Clarified brand, value prop, and vision (i) | TojCg84JDnPyQjLN7N2psW |
| Nifty 50 network active and engaged (i) | We1UWEh1bqj3C6PGytTNt |
| 4h/week carved to leadership development (i) | YWBSRgeRb3PqqFPk2NzreT |
| Courses and reading list aligned to values (i) | RADNcxVKK5obSXg93YrTsN |
| "How I want to be known" narrative (i) | 9xWDJbv88sdH8gkMtTaeMt |
| 5 target roles identified with pre-reqs (i) | Y5xvwacejzfChwg21j8jJ7 |

**Relationships / Citizen / Athlete (i) anchors**
| Project | UUID | Area |
|---------|------|------|
| Kayla can get a house if she likes (i) | LH4Lnqm5L5DUsqGDLzAGS2 | Father |
| Jared working from home w/ good transition (i) | Rdbmkq8HTu5xULQooxYEZG | Father |
| Cook, shop, date once a week (i) | 6iSBrtmfXfCjf9p7pFnwjM | Husband |
| 3 vacations (i) | 6Pb7S6mKDfMUdsxwE27puy | Husband |
| Retirement on track (i) | 2n3W78kVYzR6mfJQmZD8BW | Husband |
| House and finances maintained (i) | GA6oHKWozSDad2vhP6hwtM | Homeowner |
| Visit family members regularly (i) | 6qAZL8iTCYvo1f1N4JnYnr | Son |
| Care management for parents and in-laws (i) | M3Hvq3ZuZ8VnKBggs7sDiE | Son |
| Financial/trust matters for Pat (i) | U5qJWBwDAuASt8VhEwfwjw | Nephew |
| Fab 5 identified (i) | BC7wzE5xjVi3hNKy5b4iLf | Friends |
| Terrific 20 built around Fab 5 (i) | TtZWEsKHKCaVz9va7xiWic | Friends |
| Regular rhythm of connection established (i) | 4hSsC4uwvNzHFU6ZB8Ukoj | Friends |
| Fig City News strategic plan sustained (i) | GTHwzfgnJ3KwrcUB1PVu16 | Fig City News |
| 182 lbs (i) | VyYnSmRmzMuJB2TcD9S9kD | Healthy |
| PMC/thons/5k/FF on calendar & trained (i) | NWqzYTQRG1gb6G6d143ect | Healthy |
| B2 level in French | MZ5fJBKaepYtVfBRhjf6Zw | Healthy |

### Recurring / Utility Projects
| Project | UUID | Notes |
|---------|------|-------|
| Chessley reoccuring | M5Fb2pirS7ByN2UYxMV4Kp | Recurring home/car |
| Someday Home Projects | 3zscoUZTwGWAK41fyGjxna | Mega-bucket |
| Health repeating | AA9qkXdvyzQq9FVesq2YsM | Daily health |
| Finance repeating | 3k4XfWBSzLgsbqUrmfcPrF | Recurring finance |

---

## Tool Decision Tree

```
See a standard list        → get_inbox / get_today / get_upcoming / get_anytime / get_someday
Big picture projects       → get_projects(include_items=false)  [or use tables above]
Area contents              → get_areas(include_items=true)
Tasks in a project         → get_todos(project_uuid="...")
Active items in an area    → search_advanced(area="...")   ← now Someday-filtered by default
Area + type filter together→ search_advanced(area="...", type="to-do")  ← now works (was a collision)
Orphan/loose area tasks    → get_orphans(area="..."?)   ← second inbox: no project, has area
Show parked items          → add include_someday=true, or get_someday
Update/move/complete       → update_todo(id, ...)
Batch-update many at once  → update_todos(ids=[...], ...)  ← same mutation to every id
Create task / project      → add_todo / add_project   ← now return the new uuid (read-back)
Lean output for reviews    → pass brief=true to any list view (truncates notes, drops verbose fields)
```

---

## Common Command Patterns

| Action | Command |
|--------|---------|
| Cancel task | `update_todo(id, canceled=true)` |
| Complete task | `update_todo(id, completed=true)` |
| Move to Someday | `update_todo(id, when="someday")` |
| File into project but keep parked | `update_todo(id, list_id="PROJ", when="someday")` |
| Schedule for date | `update_todo(id, when="2026-01-03")` |
| Move to project/area | `update_todo(id, list_id="UUID")` |
| Add task to project | `add_todo(title, list_id="PROJ")` |

---

## Jack's Vocabulary

| Term | Meaning |
|------|---------|
| Bricolage | Dedicated home project catch-up time |
| Horcrux | This reference doc |
| Nifty 50 | Strategic network of 50 key professional connections (Next Role) |
| Fab 5 / Terrific 20 | Friendship network tiers (Friend role) |
| Jan 3 | Standard post-holiday Sanofi project activation date |
| (i) / (g) | intention-target project / formal goal |

---

## Intention Role → Area Mapping (2026)

| Intention Role | Things Areas |
|----------------|--------------|
| Sanofi Leader | Sanofi |
| Thought Leader | Thought Leader, BioMetre, PDA, MIT INM, LGO |
| Next Role Ready | Next Role, Digital Gemba |
| Father | Father |
| Husband | Husband |
| Elder Steward (was "Son") | Son, Nephew |
| Friend | Friends |
| Citizen | Fig City News |
| Athlete | Healthy |
| Household | Homeowner, Financial |

Source of truth for goals: `~/Developer/gtd/intentions/intentions.yaml`

---

## API Limitations

| Limitation | Workaround |
|------------|------------|
| Recurring task templates not searchable | Trust screenshots; manual moves in Things |
| Can't delete areas | Manual deletion in Things |
| Search misses some items | Multiple terms or browse by project |

---

## Weekly Review Checklist

1. [ ] **Inbox** → process to area/project
1b.[ ] **Orphan tasks** → loose tasks sitting directly in an area (no project) are
   unprocessed; triage into a project (or Someday). Treat as a second inbox.
2. [ ] **Today** → is this actually today's work?
3. [ ] **Upcoming (7d)** → ready?
4. [ ] **Anytime bloat** → move non-urgent to Someday?
5. [ ] **Stray tasks → projects** (priority over fretting about age)
6. [ ] **Someday (LAST)** → `include_someday=true`; anything ready to activate?
