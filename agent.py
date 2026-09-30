"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "suggest_outfit_item_id": None,   # id of the item suggest_outfit actually received
        "fit_card_item_id": None,         # id of the item create_fit_card actually received
        "error": None,               # set when the run ended early
    }


# ── query parsing (regex) ─────────────────────────────────────────────────────

STOPWORDS = {"looking", "for", "a", "an", "the", "i", "im", "want", "need", "some",
             "something", "find", "me", "show", "please", "any", "in", "with", "and",
             "or", "of", "to", "that", "is", "my", "under", "below", "size"}


def parse_query(query: str) -> dict:
    """Pull max_price and size out with regex, then keep the non-filler words."""
    text = query.lower()

    max_price = None
    m = re.search(r"(?:under|below|less than|max|up to)\s*\$?\s*(\d+(?:\.\d+)?)", text)
    if m:
        max_price = float(m.group(1))
        text = text.replace(m.group(0), " ")

    size = None
    m = re.search(r"\bsize\s+(one size|us\s*\d+(?:\.\d+)?|w\d+|xxs|xs|xxl|xl|s|m|l)\b", text)
    if m:
        size = "one size" if m.group(1) == "one size" else m.group(1).upper()
        text = text.replace(m.group(0), " ")

    words = [w for w in re.findall(r"[a-z0-9]+", text) if w not in STOPWORDS]
    return {"description": " ".join(words), "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Say what was searched and what the user could loosen."""
    parts = [f"'{parsed['description']}'" if parsed["description"] else "anything"]
    tips = []
    if parsed["size"]:
        parts.append(f"in size {parsed['size']}")
        tips.append("drop the size")
    if parsed["max_price"] is not None:
        parts.append(f"under ${parsed['max_price']:g}")
        tips.append("raise your max price")
    if parsed["description"]:
        tips.append("use fewer or different keywords")
    return f"Nothing matched {' '.join(parts)}. Try: " + ", or ".join(tips) + "."


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    next_step = "parse"
    count = 0
    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "parse":
            session["parsed"] = parse_query(session["query"])
            next_step = "search"

        elif next_step == "search":
            p = session["parsed"]
            session["search_results"] = search_listings(
                p["description"], size=p["size"], max_price=p["max_price"]
            )
            # THE BRANCH — decided by reading the result back out of the session.
            if len(session["search_results"]) == 0:
                session["error"] = _no_results_message(session["parsed"])
                next_step = "done"
            else:
                next_step = "select"

        elif next_step == "select":
            session["selected_item"] = session["search_results"][0]
            next_step = "suggest"

        elif next_step == "suggest":
            item = session["selected_item"]
            session["suggest_outfit_item_id"] = item["id"]
            session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])
            next_step = "fit_card"

        elif next_step == "fit_card":
            item = session["selected_item"]
            session["fit_card_item_id"] = item["id"]
            session["fit_card"] = create_fit_card(session["outfit_suggestion"], item)
            next_step = "done"

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
