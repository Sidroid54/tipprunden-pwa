from process_kicker_matchday import assign_ranking_points


test_results = [
    {
        "name": "Björn",
        "kicker_name": "Björn",
        "raw_points": 80,
    },
    {
        "name": "Jan",
        "kicker_name": "Jan",
        "raw_points": 80,
    },
    {
        "name": "Marcus",
        "kicker_name": "Marcus",
        "raw_points": 70,
    },
]

results = assign_ranking_points(test_results)

for result in results:
    print(
        result["rank"],
        result["name"],
        result["ms_points"],
    )