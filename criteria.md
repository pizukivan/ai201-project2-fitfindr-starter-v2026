# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Search is plain keyword matching with no synonyms, so some phrasings will miss
or rank the wrong item first ("graphic tee" also returned cargo pants), and two
of the three steps call the model, which can fail. 4 of 5 leaves room for one
miss without calling the agent unreliable.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
The stop is a plain `if` check on an empty list, and no model runs before it.
The message is built from the parsed filters, so it names what to change every
time. Any miss here is a bug, not bad luck.

---

## 3. The selected item is the same item every tool receives

For 5 matching queries, the `id` of `session["selected_item"]` equals
`session["search_results"][0]["id"]`, and equals the `id` of the item passed to
both `suggest_outfit` and `create_fit_card` (as shown in the trace) — 5 of 5
tries.

**Why this target:**
The model never touches the id. The loop stores the item in the session and
passes that same dict along, all in plain code. If an id ever doesn't match,
the session handling is broken, not the model.

---

## 4. The fit card mentions price and platform exactly once and stays caption-length

For 5 different matching items, each fit card contains the price exactly once
(written as `$` plus the number, e.g. `$24`), contains the platform name exactly
once (case-insensitive), and is 2–4 sentences long (counting sentences ending in
`.`, `!`, or `?`) — in at least 4 of 5 cards.

**Why this target:**
The caption comes from a model at temperature 0.9. The prompt spells out these
rules, but the model can still repeat the price or drop the platform, so 4 of 5
allows one slip. I didn't go lower because the rules are explicit in the
prompt. I left the title out because the model paraphrases it, so "exactly
once" can't be checked by exact match.

---

## 5. No wardrobe piece is suggested twice within one outfit

With `get_example_wardrobe()` and 5 different matching items, split each outfit
suggestion into outfits at its "Outfit 1", "Outfit 2" headings (no headings =
the whole text is one outfit; text before the first heading is ignored). Within
each outfit, count case-insensitive occurrences of each wardrobe piece's
distinctive phrase: "straight-leg jeans", "khaki trousers", "ribbed tank",
"crewneck sweatshirt", "zip hoodie", "denim jacket", "white sneakers",
"combat boots", "leather belt", "crossbody bag". No phrase appears more than
once in any single outfit — in at least 4 of 5 suggestions.

**Why this target:**
The outfit comes from a model writing free text, and the prompt doesn't forbid
repeats, so a slip is possible; 4 of 5 allows one. Repeating a piece inside one
outfit is unusual even for a model, so I didn't go lower. Distinctive phrases
catch the pieces even when the model lowercases or shortens their names, and
skipping the intro keeps "since you already own the ribbed tank" from counting
as a repeat.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
