def generate_digest(records: list[dict]) -> str:
    findings = [r for r in records if r["tier"] > 0 and r["gate_passed"]]
    findings.sort(key=lambda r: r["tier"])
    findings = findings[:10]

    if not findings:
        return "# Signal Digest\n\nNo signals found in this run.\n"

    lines = ["# Signal Digest", ""]
    for r in findings:
        lines.append(
            f"- **{r['company']}** (Tier {r['tier']}, {r['sector']}) — "
            f"{r['signal_text'][:200]} "
            f"[[source]]({r['source_url']}) — {r['date_mentioned']}"
        )

    return "\n".join(lines) + "\n"
