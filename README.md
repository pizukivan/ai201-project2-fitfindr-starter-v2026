# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr helps you find a thrifted piece and figure out how to wear it. You type what you're looking for in plain language, like "vintage graphic tee under $30, size M". It searches 40 secondhand listings from Depop, thredUp and Poshmark for the best match within your size and price. Then it suggests one or two outfits built from clothes you already own, and writes a short caption you could post about the find. If nothing matches, it stops and tells you what to loosen, such as the size, the price or the keywords, instead of making something up.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters `data/listings.json` by price and size, then ranks the remaining listings by how many keywords from `description` appear in their title, description, style_tags, category, and colors. It does not call the model.
- **Inputs:** `description` (str), the keywords the user typed, e.g. `"vintage graphic tee"`; `size` (str | None), where None skips the size filter; `max_price` (float | None), an inclusive ceiling, where None skips the price filter.
  - *Size match rule:* This is case-insensitive and matches whole tokens only. The listing's size is split on `/`, spaces, and parentheses, and it matches if the requested size equals one of those tokens, the whole string, or one `/`-separated piece with any parenthetical removed (so `"one size"` matches `"One Size (adjustable)"`). So `"M"` matches `"S/M"` and `"M/L"` but not `"XL"`, and `"S"` does not match `"US 9"`. `"One Size"` listings match only a request for `"one size"`.
  - *Price rule:* A listing passes if `listing["price"] <= max_price`.
  - *Scoring rule:* Lowercase `description` and split it on anything that isn't a letter or digit. The score is the number of distinct query words found as whole words in the listing's title, description, category, style_tags, and colors. A word also counts if it matches after a trailing "s" is dropped from either side, so "tees" matches "tee". Listings that score 0 are dropped. Ties keep their order in `listings.json`. If `description` is empty or whitespace, every listing that passes the size and price filters is returned in data order.
- **Returns:** A `list[dict]` of listing dicts, best match first, with at most `config.SEARCH_RESULT_LIMIT` (10) items. Each dict has `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str or None), and `platform` (str: depop / thredUp / poshmark).
- **When it has nothing:** It returns an empty list `[]`, never None and never an exception. The loop branches on `len(results) == 0`.

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for one or two outfits built around the new item. It names pieces the user already owns when the wardrobe has items.
- **Inputs:** `new_item` (dict), one listing dict from `search_listings`; `wardrobe` (dict), a wardrobe with an `items` key holding a `list[dict]`, where each item has `id`, `name`, `category`, `colors`, `style_tags`, and `notes`. The list may be empty.
- **Returns:** A non-empty `str` of outfit suggestions in plain text. Each outfit names the new item plus specific wardrobe pieces by their `name`, e.g. "Baggy straight-leg jeans, dark wash".
- **When it has nothing:** If `wardrobe["items"]` is `[]`, it returns a non-empty `str` of general styling advice for the item: what kinds of pieces, colors, and shoes pair with it, without naming owned items. It never returns `""` or None. It does not catch `ModelUnavailable` from `generate()`; that error passes up to `run_agent`.

### `create_fit_card`

- **What it does:** Asks the model, through `generate()`, for a two-to-four-sentence social-post caption about the find. The caption mentions the item title, price, and platform once each.
- **Inputs:** `outfit` (str), the string returned by `suggest_outfit`; `new_item` (dict), the same listing dict passed to `suggest_outfit`. The prompt skips `brand` when it is None.
- **Returns:** A `str` caption of 2–4 sentences, written like a real post rather than a product description. It varies between runs because `TEMPERATURE` is 0.9.
- **When it has nothing:** If `outfit` is empty or whitespace-only, it doesn't call the model and returns the fixed `str` `"Can't write a fit card: no outfit suggestion was provided for <title>."` As with `suggest_outfit`, `ModelUnavailable` passes up to `run_agent`.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` to a message that repeats the parsed filters and says what to loosen. For example: "Nothing matched 'ballgown' in size XXS under $5. Try raising your max price, dropping the size, or using fewer keywords." Then return the session without calling `suggest_outfit` or `create_fit_card`, so `selected_item`, `outfit_suggestion` and `fit_card` stay None. Otherwise, set `session["selected_item"]` to the first result and call `suggest_outfit(session["selected_item"], session["wardrobe"])`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. It pulls out `max_price` from phrases like "under $30", "below 25" or "up to $40", and `size` only when the word "size" comes right before it ("size M", "size US 8.5", "size W30"). Whatever's left is lowercased and filler words like "looking", "for" and "a" are dropped; the remaining words become `description`. Known limits: "medium tee" isn't read as size M, and "$30 tee" with no "under" leaves the price in the description.

**What moves through the session:** in order,
1. `query`, what the user typed.
2. `parsed`, a dict with `description`, `size` and `max_price`.
3. `search_results`, the list from `search_listings`. The branch reads this back out of the session.
4. `selected_item`, the first result.
5. `suggest_outfit_item_id`, the id of the item passed to `suggest_outfit`.
6. `outfit_suggestion`.
7. `fit_card_item_id`, the id of the item passed to `create_fit_card`.
8. `fit_card`.

`error` is set only when the run stops early. Every tool reads its inputs from the session, never from the previous call's return value directly.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1:
Pair the Y2K Baby Tee — Butterfly Print with your baggy straight-leg jeans, dark wash. Throw on your black cropped zip hoodie for a cool layered look, and finish with your chunky white sneakers and black crossbody bag.

Outfit 2:
Style the Y2K Baby Tee — Butterfly Print tucked into your wide-leg khaki trousers. Add your vintage black denim jacket on top, and wear your black combat boots to lean into that fun, retro Y2K vibe.

  Fit card: I am obsessed with this butterfly print Y2K baby tee that I just scored for only $18. I am listing it on Depop, but honestly, it was so hard not to keep for myself. You can layer it with baggy jeans and a zip hoodie for an effortless off-duty look, or dress it up with khaki trousers and combat boots for a total retro moment.
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth','layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Hey! Grab these vintage Levi's immediately—at $38, a classic 501 in a medium wash is an absolute thrift score that you will wear forever. Since you already own a white ribbed tank top and chunky white sneakers, you have the ultimate casual uniform ready to go. 

Outfit 1: Casual Sunday
Pair your new vintage Levi's 501 Jeans — Medium Wash with the white ribbed tank top tucked in. Add your chunky white sneakers, cinch the look with your brown leather belt, and toss your black crossbody bag across your shoulder. 

Outfit 2: Cozy Streetwear
Layer your oversized grey crewneck sweatshirt over the jeans, and pair them with your black combat boots and the black crossbody bag for an effortless, cool-girl vintage vibe.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Found the holy grail of denim on depop with these vintage Levi's 501 jeans in the absolute best medium wash for only $38. I am keeping the whole vibe super effortless by pairing them with crisp white sneakers for that classic off-duty look. Honestly, nothing beats finding the perfect pair of broken-in jeans that fit like a glove.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
