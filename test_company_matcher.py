from src.extractor import load_companies, match_company

companies = load_companies()

samples = [
    "OpenText announced a new data centre expansion today.",
    "Mogo Inc. is exploring international markets.",
    "BlackBerry Limited reported quarterly earnings.",
    "A completely unrelated company said something.",
    "Canpotex signed a new potash supply agreement with Bangladesh.",
]

for text in samples:
    result = match_company(text, companies)
    print(f"{text!r} -> {result}")
