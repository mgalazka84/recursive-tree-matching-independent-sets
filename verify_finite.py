"""Exact finite-size comparisons and two-time checks for the recursive-tree article."""
from fractions import Fraction
from itertools import product
from math import factorial
from pathlib import Path
import json

from verify_results import encode


def offline_optima(parents):
    """Compute maximum matching and independent-set sizes by two subtree recursions."""
    n = len(parents) + 1
    unmatched_root = [0] * (n + 1)
    best_child_gain = [0] * (n + 1)
    root_in = [1] * (n + 1)
    root_out = [0] * (n + 1)
    for child in range(n, 1, -1):
        parent = parents[child - 2]
        best_matching = unmatched_root[child] + best_child_gain[child]
        unmatched_root[parent] += best_matching
        gain = 1 + unmatched_root[child] - best_matching
        best_child_gain[parent] = max(best_child_gain[parent], gain)
        root_in[parent] += root_out[child]
        root_out[parent] += max(root_in[child], root_out[child])
    return unmatched_root[1] + best_child_gain[1], max(root_in[1], root_out[1])


def online_paths(parents):
    matched, selected = set(), {1}
    edge_sizes, vertex_sizes = [0, 0], [0, 1]
    for vertex, parent in enumerate(parents, 2):
        if parent not in matched:
            matched.update((parent, vertex))
        if parent not in selected:
            selected.add(vertex)
        edge_sizes.append(len(matched) // 2)
        vertex_sizes.append(len(selected))
    return edge_sizes, vertex_sizes


def covariance_checks(products, n, independent):
    checked = 0
    count = factorial(n - 1)
    for r in range(2 if independent else 3, n + 1):
        if independent:
            mean_product = Fraction(r * n, 4)
            variance = Fraction(r, 12) if r >= 3 else Fraction(0)
            factor = Fraction(r - 1, n - 1)
        else:
            mean_product = Fraction(r * n, 9)
            variance = {3: Fraction(0), 4: Fraction(2, 9)}.get(r, Fraction(2 * r, 45))
            factor = Fraction((r - 1) * (r - 2), (n - 1) * (n - 2))
        assert Fraction(products[r], count) - mean_product == factor * variance
        checked += 1
    return checked


def compute(max_n=9):
    rows = []
    checks = 0
    for n in range(2, max_n + 1):
        count = factorial(n - 1)
        sums = [0] * 4
        products_m, products_j = [0] * (n + 1), [0] * (n + 1)
        for parents in product(*(range(1, v) for v in range(2, n + 1))):
            matching, independent = offline_optima(parents)
            assert matching + independent == n
            edges, vertices = online_paths(parents)
            for i, value in enumerate((edges[n], matching, vertices[n], independent)):
                sums[i] += value
            for r in range(2, n + 1):
                products_m[r] += edges[r] * edges[n]
                products_j[r] += vertices[r] * vertices[n]
        checks += covariance_checks(products_m, n, False)
        checks += covariance_checks(products_j, n, True)
        edge_mean, offline_m, vertex_mean, offline_j = (Fraction(v, count) for v in sums)
        assert edge_mean == (1 if n == 2 else Fraction(n, 3))
        assert vertex_mean == Fraction(n, 2)
        rows.append(dict(n=n, histories=count, matching_online=str(edge_mean),
                         matching_offline=str(offline_m), matching_ratio=str(edge_mean / offline_m),
                         independent_online=str(vertex_mean), independent_offline=str(offline_j),
                         independent_ratio=str(vertex_mean / offline_j)))
    example = (1, 1, 3, 2, 5)
    words = [''.join(map(str, encode(example[:t], independent=True)[0]))
             for t in range(1, len(example) + 1)]
    return dict(offline_table=rows, checked_two_time_covariances=checks,
                descent_example_parents=example, descent_example_words=words)


if __name__ == '__main__':
    if not __debug__:
        raise SystemExit('Run with Python assertions enabled (omit -O).')
    data = compute()
    path = Path(__file__).with_name('finite_results.json')
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(path.name, data['checked_two_time_covariances'], data['descent_example_words'])
