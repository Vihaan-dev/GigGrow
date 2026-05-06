"""Tool-use chat for the financial copilot.

The chat endpoint runs in two passes:

  Pass 1 — TOOL SELECTION
    The user's message + a tool catalog go to Gemini. Gemini returns JSON:
        { tool_calls: [{name, args}, ...], rationale: str }
    No prose answer yet.

  Pass 2 — ANSWER COMPOSITION
    The backend executes each tool deterministically against real data,
    appends the (input, output) pairs to a second prompt, and asks Gemini
    to compose the final answer in the user's language using ONLY those
    tool outputs.

The tool calls are returned to the frontend so judges can see exactly
what data the model retrieved before answering. This is the antidote
to "just a chatbot wrapper".
"""

import json
import re
from datetime import date, datetime, timedelta

from .gemini_client import generate_text
from .profile_insights import build_profile_insights
from .forecast import forecast_days
from .safety import check_safety_status
from .schemes import match_schemes
from .loans import match_loans

LANGUAGE_LABEL = {
    "hindi": "Hindi (Devanagari script only)",
    "kannada": "Kannada (Kannada script only)",
    "english": "English",
}


# -------- Tool catalog --------
# Each tool has: name, description (for Gemini), args schema, executor fn.

def _last_n_days(daily, n):
    return daily[-n:] if len(daily) >= n else daily


def _aggregate_earnings(daily):
    return sum(d.get("earnings", 0) for d in daily)


def tool_get_earnings_for_period(ctx, period="last_7_days"):
    """Return earnings totals for a named period."""
    daily = ctx["insights"].get("daily", []) or []
    if period == "yesterday":
        days = daily[-1:] if daily else []
    elif period == "last_7_days":
        days = _last_n_days(daily, 7)
    elif period == "last_30_days":
        days = _last_n_days(daily, 30)
    else:
        return {"error": "unknown_period", "valid": ["yesterday", "last_7_days", "last_30_days"]}
    return {
        "period": period,
        "days_counted": len(days),
        "total_earnings": _aggregate_earnings(days),
        "avg_per_day": int(round(_aggregate_earnings(days) / max(len(days), 1))),
    }


def tool_get_spending_by_category(ctx, period="last_30_days"):
    """Return total spending grouped by category."""
    daily = ctx["insights"].get("daily", []) or []
    if period == "last_7_days":
        days = _last_n_days(daily, 7)
    else:
        days = daily
    by_cat = {}
    for d in days:
        for cat, amt in (d.get("spending_by_category") or {}).items():
            by_cat[cat] = by_cat.get(cat, 0) + amt
    total = sum(by_cat.values()) or 1
    return {
        "period": period,
        "days_counted": len(days),
        "by_category": by_cat,
        "by_category_pct": {k: round(v * 100 / total, 1) for k, v in by_cat.items()},
    }


def tool_get_dow_pattern(ctx):
    """Return earnings averaged by day of week."""
    pat = ctx["insights"].get("dow_pattern", {}) or {}
    return {
        "pattern": {info["name"]: info["avg"] for _, info in pat.items() if info.get("avg")},
        "best_day": ctx["insights"].get("best_day_of_week"),
        "worst_day": ctx["insights"].get("worst_day_of_week"),
    }


def tool_get_safety_status(ctx):
    return {
        "days_safe": ctx["safety"].get("days_safe"),
        "status": ctx["safety"].get("status"),
        "current_savings": ctx["user"].get("current_savings", 0),
        "daily_mandatory": int(ctx["user"]["mandatory_spend"] / 7),
    }


def tool_get_forecast(ctx, days=14, scenario="baseline"):
    """Run a forward forecast."""
    fc = forecast_days(
        ctx["insights"],
        ctx["spending_history"],
        days_ahead=int(days),
        scenario=scenario,
        starting_savings=ctx["user"].get("current_savings", 0),
    )
    return {
        "days_ahead": fc["days_ahead"],
        "scenario": fc["scenario"],
        "ending_savings": fc["ending_savings"],
        "predicted_net": fc["predicted_net"],
        "days_to_30d_buffer": fc["days_to_30d_buffer"],
    }


def tool_simulate_purchase(ctx, amount):
    """Simulate the impact of a purchase on safety and savings."""
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return {"error": "amount_must_be_number"}
    daily_mandatory = ctx["user"]["mandatory_spend"] / 7 or 1
    current_savings = ctx["user"].get("current_savings", 0)
    return {
        "purchase_amount": amount,
        "current_safety_days": round(current_savings / daily_mandatory, 1),
        "new_safety_days": round(max(0, (current_savings - amount) / daily_mandatory), 1),
        "savings_after": current_savings - amount,
    }


def tool_match_schemes(ctx):
    matched = match_schemes({
        "annual_income": ctx["user"].get("annual_income", 0),
        "age": ctx["user"].get("age", 0),
    })
    return {
        "matched_count": len(matched),
        "schemes": [
            {"name": s["name"], "annual_amount": s["annual_amount"], "annual_cost": s.get("annual_cost", 0)}
            for s in matched
        ],
    }


def tool_top_overspend(ctx):
    """Find the category most over its 30d baseline in the last 7 days."""
    daily = ctx["insights"].get("daily", []) or []
    if len(daily) < 7:
        return {"overspend": None, "reason": "insufficient_history"}
    last7 = daily[-7:]
    baseline = ctx["insights"].get("spending", {}).get("by_category_daily_baseline", {}) or {}
    recent = {}
    for d in last7:
        for cat, amt in (d.get("spending_by_category") or {}).items():
            if cat in {"rent", "transfer"}:
                continue
            recent[cat] = recent.get(cat, 0) + amt
    worst = None
    for cat, total in recent.items():
        bd = baseline.get(cat, 0)
        if bd <= 0:
            continue
        recent_daily = total / 7
        pct = int((recent_daily - bd) / bd * 100)
        if worst is None or pct > worst["pct_over"]:
            worst = {
                "category": cat,
                "recent_daily_avg": int(round(recent_daily)),
                "baseline_daily": int(bd),
                "pct_over": pct,
            }
    return {"overspend": worst}


TOOLS = {
    "get_earnings_for_period": {
        "fn": tool_get_earnings_for_period,
        "args": {"period": "yesterday | last_7_days | last_30_days"},
        "description": "Return total and average earnings for a named period.",
    },
    "get_spending_by_category": {
        "fn": tool_get_spending_by_category,
        "args": {"period": "last_7_days | last_30_days"},
        "description": "Return spending split by category over a period.",
    },
    "get_dow_pattern": {
        "fn": tool_get_dow_pattern,
        "args": {},
        "description": "Return average earnings for each day of the week, plus best and worst day.",
    },
    "get_safety_status": {
        "fn": tool_get_safety_status,
        "args": {},
        "description": "Return days_safe, status, current savings, and daily mandatory spend.",
    },
    "get_forecast": {
        "fn": tool_get_forecast,
        "args": {"days": "integer 7-90", "scenario": "baseline | optimistic | pessimistic"},
        "description": "Forecast future ending savings, predicted net, and days-to-30d-buffer.",
    },
    "simulate_purchase": {
        "fn": tool_simulate_purchase,
        "args": {"amount": "integer rupees"},
        "description": "Compute days-safe before and after spending a one-time amount.",
    },
    "match_schemes": {
        "fn": tool_match_schemes,
        "args": {},
        "description": "List the government schemes the user qualifies for.",
    },
    "top_overspend": {
        "fn": tool_top_overspend,
        "args": {},
        "description": "Return the category most over its 30d baseline in the last 7 days, if any.",
    },
}


def _strip_code_fences(text):
    if not text:
        return text
    cleaned = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, flags=re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return cleaned


def _build_tool_catalog_text():
    lines = []
    for name, spec in TOOLS.items():
        args = ", ".join(f"{k}: {v}" for k, v in (spec["args"] or {}).items()) or "(no args)"
        lines.append(f"- {name}({args}) — {spec['description']}")
    return "\n".join(lines)


def _select_tools(user_message):
    catalog = _build_tool_catalog_text()
    prompt = (
        "You are the planning step of a financial copilot. The user asked:\n"
        '  "{msg}"\n\n'
        "You have these tools to fetch real data:\n{catalog}\n\n"
        "Decide which tools to call. Output ONLY a JSON object:\n"
        '{{ "tool_calls": [{{"name": "tool_name", "args": {{...}}}}], '
        '"rationale": "one short sentence in English" }}\n\n'
        "Rules:\n"
        "- Call at most 3 tools.\n"
        "- Pick the smallest set that answers the question.\n"
        "- If you cannot answer with these tools, return tool_calls: []."
    ).format(msg=user_message, catalog=catalog)

    raw = _strip_code_fences(generate_text(prompt) or "")
    raw_lower = raw.lower()
    if not raw or "api key" in raw_lower or "trouble thinking" in raw_lower:
        return None  # signals "no LLM available, fall back to heuristic"

    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None

    if not isinstance(parsed, dict) or "tool_calls" not in parsed:
        return None
    return parsed


def _heuristic_select_tools(user_message):
    """Deterministic fallback when Gemini is unavailable. Pattern-match
    the message to pick a sensible tool set so the chat still works."""
    m = user_message.lower()
    calls = []
    if any(k in m for k in ["yesterday", "kal", "ನಿನ್ನೆ"]):
        calls.append({"name": "get_earnings_for_period", "args": {"period": "yesterday"}})
    elif any(k in m for k in ["week", "हफ्त", "ವಾರ"]):
        calls.append({"name": "get_earnings_for_period", "args": {"period": "last_7_days"}})
    elif any(k in m for k in ["earn", "kamaya", "ಗಳಿಸ"]):
        calls.append({"name": "get_earnings_for_period", "args": {"period": "last_30_days"}})

    if any(k in m for k in ["safe", "buffer", "safety", "सुरक्षा"]):
        calls.append({"name": "get_safety_status", "args": {}})
    if any(k in m for k in ["bike", "phone", "buy", "afford", "ले सकता", "खरीद"]):
        # extract a number from the message if any
        nums = re.findall(r"\d{3,7}", user_message)
        if nums:
            calls.append({"name": "simulate_purchase", "args": {"amount": int(nums[0])}})
    if any(k in m for k in ["fuel", "spend", "खर्च", "petrol"]):
        calls.append({"name": "top_overspend", "args": {}})
    if any(k in m for k in ["scheme", "pmsby", "pmjjby", "kisan", "योजना"]):
        calls.append({"name": "match_schemes", "args": {}})
    if not calls:
        calls.append({"name": "get_safety_status", "args": {}})
        calls.append({"name": "get_dow_pattern", "args": {}})
    return {"tool_calls": calls[:3], "rationale": "Heuristic match (no LLM)."}


def _execute_tool(name, args, ctx):
    spec = TOOLS.get(name)
    if not spec:
        return {"error": "unknown_tool", "name": name}
    try:
        return spec["fn"](ctx, **(args or {}))
    except TypeError as exc:
        return {"error": "bad_args", "detail": str(exc)}
    except Exception as exc:  # safety net
        return {"error": "tool_failed", "detail": str(exc)}


def _compose_answer(user_message, tool_results, language):
    label = LANGUAGE_LABEL.get(language, "English")
    prompt = (
        "You are GigShield, a financial copilot for an Indian gig worker.\n"
        "Answer the user's question in {language}, in 2-4 sentences.\n\n"
        'User asked: "{msg}"\n\n'
        "Tool outputs (use ONLY these numbers):\n{results}\n\n"
        "Rules:\n"
        "- Use ONLY values from the tool outputs above. Do not invent or round.\n"
        "- Be concrete and brief. No filler.\n"
        "- If language is Hindi or Kannada, use the native script throughout.\n"
        "- Output the answer text only. No JSON, no preamble."
    ).format(
        language=label,
        msg=user_message,
        results=json.dumps(tool_results, ensure_ascii=False, indent=2),
    )

    raw = (generate_text(prompt) or "").strip()
    raw_lower = raw.lower()
    if not raw or "api key" in raw_lower or "trouble thinking" in raw_lower:
        return None
    return raw


def _fallback_answer(tool_results, user_message):
    """Simple deterministic answer composition when Gemini is unavailable."""
    parts = []
    for tr in tool_results:
        out = tr["output"]
        if "error" in (out or {}):
            continue
        if tr["name"] == "get_earnings_for_period":
            parts.append(
                "{period}: total Rs {total}, avg Rs {avg}/day across {n} days.".format(
                    period=out.get("period"),
                    total=out.get("total_earnings"),
                    avg=out.get("avg_per_day"),
                    n=out.get("days_counted"),
                )
            )
        elif tr["name"] == "get_safety_status":
            parts.append(
                "You have {d} days safe ({status}); savings Rs {s}.".format(
                    d=out.get("days_safe"),
                    status=out.get("status"),
                    s=out.get("current_savings"),
                )
            )
        elif tr["name"] == "simulate_purchase":
            parts.append(
                "Spending Rs {a} drops days-safe from {b} to {a2}.".format(
                    a=out.get("purchase_amount"),
                    b=out.get("current_safety_days"),
                    a2=out.get("new_safety_days"),
                )
            )
        elif tr["name"] == "top_overspend":
            o = out.get("overspend")
            if o:
                parts.append(
                    "{cat} spend is {pct}% above baseline (Rs {r}/day vs Rs {b}/day).".format(
                        cat=o["category"],
                        pct=o["pct_over"],
                        r=o["recent_daily_avg"],
                        b=o["baseline_daily"],
                    )
                )
        elif tr["name"] == "get_dow_pattern":
            best = out.get("best_day", {})
            worst = out.get("worst_day", {})
            parts.append(
                "Best day: {b} (Rs {ba}). Worst: {w} (Rs {wa}).".format(
                    b=best.get("name"), ba=best.get("avg"),
                    w=worst.get("name"), wa=worst.get("avg"),
                )
            )
        elif tr["name"] == "get_forecast":
            parts.append(
                "{scenario} forecast: ending savings Rs {e}, predicted net Rs {n} over {d} days.".format(
                    scenario=out.get("scenario"),
                    e=out.get("ending_savings"),
                    n=out.get("predicted_net"),
                    d=out.get("days_ahead"),
                )
            )
        elif tr["name"] == "match_schemes":
            names = ", ".join(s["name"] for s in (out.get("schemes") or [])[:3])
            if names:
                parts.append(f"You qualify for: {names}.")
    if not parts:
        return "I couldn't gather useful data for that question."
    return " ".join(parts)


def run_chat(user_message, ctx, *, language="english"):
    """Full two-pass tool-use chat. Returns dict with tool_calls + answer + source."""
    selection = _select_tools(user_message)
    selection_source = "gemini"
    if selection is None:
        selection = _heuristic_select_tools(user_message)
        selection_source = "heuristic"

    tool_results = []
    for call in (selection.get("tool_calls") or [])[:3]:
        name = call.get("name")
        args = call.get("args") or {}
        output = _execute_tool(name, args, ctx)
        tool_results.append({"name": name, "args": args, "output": output})

    answer = _compose_answer(user_message, tool_results, language)
    answer_source = "gemini"
    if answer is None:
        answer = _fallback_answer(tool_results, user_message)
        answer_source = "fallback"

    return {
        "answer": answer,
        "tool_calls": tool_results,
        "rationale": selection.get("rationale", ""),
        "selection_source": selection_source,
        "answer_source": answer_source,
        "language": language,
    }
