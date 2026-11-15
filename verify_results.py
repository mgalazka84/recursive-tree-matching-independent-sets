"""Exact finite checks for online matching and independent sets on recursive trees.

Run with Python 3.9 or later. The JSON report is written next to this file.
"""
from collections import Counter
from fractions import Fraction
from itertools import permutations, product
import json
from math import factorial
from pathlib import Path


def pk(word):
    """Number of interior peaks, excluding both endpoints."""
    return sum(a < b > c for a, b, c in zip(word, word[1:], word[2:]))


def des(word):
    """Number of adjacent descents."""
    return sum(a > b for a, b in zip(word, word[1:]))


def vertex_slots(word, occupied, independent):
    """Pair occupied/free vertices with neutral/creating slots in order."""
    statistic = des if independent else pk
    before = statistic(word)
    maximum = len(word) + 1
    neutral = []
    creating = []
    for slot in range(maximum):
        extended = word[:slot] + (maximum,) + word[slot:]
        increase = statistic(extended) - before
        assert increase in (0, 1)
        (creating if increase else neutral).append(slot)

    free = set(range(1, maximum + 1)) - occupied
    assert len(occupied) == len(neutral) and len(free) == len(creating)
    return dict(zip(sorted(occupied), neutral)) | dict(zip(sorted(free), creating))


def greedy_update(occupied, vertex, parent, independent):
    if parent not in occupied:
        occupied.add(vertex)
        if not independent:
            occupied.add(parent)


def encode(parents, independent=False):
    """Return the word and greedy size for a tree with at least two vertices."""
    word = (1,)
    occupied = {1} if independent else {1, 2}
    for vertex, parent in enumerate(parents[1:], start=3):
        slot = vertex_slots(word, occupied, independent)[parent]
        word = word[:slot] + (vertex - 1,) + word[slot:]
        greedy_update(occupied, vertex, parent, independent)
    size = len(occupied) if independent else len(occupied) // 2
    return word, size


def decode(word, independent=False):
    """Recover the parent list by successively deleting the largest symbol."""
    if len(word) == 1:
        return (1,)
    maximum = len(word)
    slot = word.index(maximum)
    previous = word[:slot] + word[slot + 1:]
    parents = decode(previous, independent)
    occupied = {1} if independent else set()
    for vertex, parent in enumerate(parents, start=2):
        greedy_update(occupied, vertex, parent, independent)
    pairing = vertex_slots(previous, occupied, independent)
    last_parent = next(parent for parent, position in pairing.items() if position == slot)
    return parents + (last_parent,)


def matching_gap(arrival, horizon):
    return Fraction((arrival - 1) * (arrival - 2), (horizon - 1) * (horizon - 2))


def independent_gap(arrival, horizon):
    return Fraction(arrival - 1, horizon - 1)


def bellman_checks(max_n=40):
    matching_states = selected_states = gap_checks = 0
    for horizon in range(2, max_n + 1):
        matching = {u: Fraction(0) for u in range(horizon % 2, horizon + 1, 2)}
        independent = {k: Fraction(0) for k in range(horizon + 1)}
        for time in range(horizon - 1, 0, -1):
            earlier = {}
            for free in range(time % 2, time + 1, 2):
                reject = matching[free + 1]
                value = reject
                if free:
                    accept = 1 + matching[free - 1]
                    probability = Fraction(free, time)
                    value += probability * (max(accept, reject) - reject)
                    if horizon >= 3:
                        assert accept - reject == matching_gap(time + 1, horizon)
                        gap_checks += 1
                if horizon >= 3:
                    denominator = (horizon - 1) * (horizon - 2)
                    intercept = Fraction(2 * horizon - 3 * time, 6)
                    intercept += Fraction(time * (time - 1) * (time - 2), 6 * denominator)
                    slope = Fraction(1, 2) * (1 - Fraction((time - 1) * (time - 2), denominator))
                    assert value == intercept + slope * free
                    matching_states += 1
                earlier[free] = value
            matching = earlier

            earlier = {}
            for selected in range(time + 1):
                reject = independent[selected]
                value = reject
                if selected < time:
                    accept = 1 + independent[selected + 1]
                    assert accept - reject == independent_gap(time + 1, horizon)
                    gap_checks += 1
                    probability = Fraction(time - selected, time)
                    value += probability * (max(accept, reject) - reject)
                intercept = Fraction(horizon * (horizon - 1) - time * (time - 1), 2 * (horizon - 1))
                slope = -Fraction(horizon - time, horizon - 1)
                assert value == intercept + slope * selected
                selected_states += 1
                earlier[selected] = value
            independent = earlier
        assert matching[1] == (1 if horizon == 2 else Fraction(horizon, 3))
        assert 1 + independent[1] == independent[0] == Fraction(horizon, 2)
    return {"maximum_horizon": max_n, "matching_states": matching_states,
            "independent_set_states": selected_states, "action_gap_checks": gap_checks}


def simulate_policy(parents, kind, seed, independent):
    """Compute realized reward and the labels of feasible rejections."""
    horizon = len(parents) + 1
    occupied = {1} if independent and seed == 0 else set()
    rejected = []
    history_sum = 0
    for vertex, parent in enumerate(parents, start=2):
        history_sum += parent
        if parent in occupied:
            continue
        if kind == "early":
            accept = vertex >= 4
        elif kind == "last":
            accept = vertex != horizon
        else:
            accept = (history_sum + vertex + sum(occupied) + seed) % 3 != 0
        if accept:
            greedy_update(occupied, vertex, parent, independent)
        else:
            rejected.append(vertex)
    reward = len(occupied) if independent else len(occupied) // 2
    return reward, rejected


def check_prefixes(parents, peak_word, descent_word):
    """Compare restrictions of the final words with direct greedy tree decisions."""
    matched = set()
    selected = {1}
    for vertex, parent in enumerate(parents, start=2):
        if parent not in matched:
            matched.update((parent, vertex))
        if parent not in selected:
            selected.add(vertex)
        peak_prefix = tuple(value for value in peak_word if value < vertex)
        descent_prefix = tuple(value for value in descent_word if value < vertex)
        assert len(matched) // 2 == 1 + pk(peak_prefix)
        assert len(selected) == 1 + des(descent_prefix)
    return 2 * len(parents)


def exhaustive_checks(max_n=9):
    total = policy_checks = prefix_checks = 0
    by_size = []
    cases = list(product(("early", "last", "history"), (0, 1), (False, True)))
    for size in range(2, max_n + 1):
        matching_counts, selected_counts = Counter(), Counter()
        matching_words, selected_words = set(), set()
        reward = Counter()
        rejection = {case: Counter() for case in cases}
        for parents in product(*(range(1, s) for s in range(2, size + 1))):
            peak_word, matching = encode(parents)
            descent_word, independent = encode(parents, independent=True)
            assert decode(peak_word) == parents
            assert decode(descent_word, independent=True) == parents
            assert matching == 1 + pk(peak_word) and independent == 1 + des(descent_word)
            prefix_checks += check_prefixes(parents, peak_word, descent_word)
            matching_words.add(peak_word)
            selected_words.add(descent_word)
            matching_counts[matching] += 1
            selected_counts[independent] += 1
            for case in cases:
                value, rejected = simulate_policy(parents, *case)
                reward[case] += value
                rejection[case].update(rejected)
            total += 1

        count = factorial(size - 1)
        assert len(matching_words) == len(selected_words) == count
        peak_counts, descent_counts = Counter(), Counter()
        for word in permutations(range(1, size)):
            peak_counts[1 + pk(word)] += 1
            descent_counts[1 + des(word)] += 1
        assert matching_counts == peak_counts and selected_counts == descent_counts
        for counts, mean, variance, threshold in (
            (matching_counts, 1 if size == 2 else Fraction(size, 3), Fraction(2 * size, 45), 5),
            (selected_counts, Fraction(size, 2), Fraction(size, 12), 3),
        ):
            assert sum(Fraction(k * v, count) for k, v in counts.items()) == mean
            if size >= threshold:
                assert sum(Fraction(v, count) * (k - mean)**2 for k, v in counts.items()) == variance
        for case in cases:
            independent = case[2]
            if size == 2 and not independent:
                continue
            optimum = Fraction(size, 2 if independent else 3)
            gap = independent_gap if independent else matching_gap
            weighted_loss = sum(gap(s, size) * Fraction(c, count) for s, c in rejection[case].items())
            assert optimum - Fraction(reward[case], count) == weighted_loss
            policy_checks += 1
        by_size.append({"n": size, "parent_sequences": count,
                        "matching_counts": dict(sorted(matching_counts.items())),
                        "independent_set_counts": dict(sorted(selected_counts.items()))})
    return {"maximum_size": max_n, "parent_sequences_total": total,
            "bijection_round_trips": 2 * total, "prefix_size_checks": prefix_checks,
            "policy_identity_checks": policy_checks, "exact_distributions": by_size}


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run with Python assertions enabled (omit -O).")
    result = {"arithmetic": "fractions.Fraction; no Monte Carlo", "bellman": bellman_checks(),
              "exhaustive": exhaustive_checks(), "status": "all checks passed"}
    target = Path(__file__).with_name("verification_results.json")
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["bellman"], indent=2))
    print(json.dumps({k: v for k, v in result["exhaustive"].items()
                      if k != "exact_distributions"}, indent=2))
