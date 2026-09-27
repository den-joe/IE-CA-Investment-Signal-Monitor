MARKET_CAP_THRESHOLD_CAD = 500_000_000


def check_market_cap_gate(market_data: dict) -> dict:
    market_cap = market_data.get("market_cap")
    currency = market_data.get("currency")

    if market_cap is None:
        return {"passed": False, "reason": "No market cap data returned (possibly delisted)"}

    if currency != "CAD":
        return {
            "passed": False,
            "reason": f"Market cap is in {currency}, not CAD - cannot compare to threshold without conversion",
        }

    if market_cap < MARKET_CAP_THRESHOLD_CAD:
        return {
            "passed": False,
            "reason": f"Market cap CAD {market_cap:,} is below the CAD {MARKET_CAP_THRESHOLD_CAD:,} threshold",
        }

    return {"passed": True, "reason": f"Market cap CAD {market_cap:,} meets the threshold"}
