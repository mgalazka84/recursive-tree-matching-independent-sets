# Online matching and independent sets on random recursive trees

Code, exact reference results and three figures for *Online matching and independent sets on random recursive trees: Exact values, policy losses and permutation bijections*, by Marek Gałązka and Hanna Wdowicka.

## Verify the calculations

Run the following command from the directory containing the scripts. The verifier uses Python 3.9 or later and the standard library.

```sh
python verify_results.py
```

The script computes each continuation value by maximizing over the available actions, then compares the result with the closed formulas in exact rational arithmetic for horizons up to 40. For all 46,233 parent sequences with 2 through 9 vertices, it inverts both permutation maps, compares the distributions with a separate enumeration of permutations, and checks which arrivals greedy accepts by restricting the final permutation to each prefix. It also checks the policy-loss identities in 90 cases.

The script writes its output to [verification_results.json](verification_results.json). To compare with the committed result after running the script in a clone, use `git diff --exit-code -- verification_results.json`. Python assertions must be enabled.

## Rebuild the figures

The three vector PDFs can be read directly. To regenerate them, use Python with Matplotlib. The reference figures were generated with Matplotlib 3.10.8.

```sh
python -m pip install matplotlib==3.10.8
python make_figures.py
```

- [Two decisions on the same four-vertex tree](figures/first_decision.pdf) shows the edges kept after accepting or rejecting the first edge.
- [A tree and its permutation](figures/bijection.pdf) pairs three matching edges with the first edge and two interior peaks of the permutation 24351.
- [The cost of rejecting a feasible arrival](figures/rejection_costs.pdf) compares the two problems at a horizon of ten vertices.

## Finite offline optima and joint laws

Run `python verify_finite.py` to regenerate [finite_results.json](finite_results.json). The script enumerates the same 46,233 trees. Two subtree recursions compute the maximum matching and independent set after the whole tree is known. The output gives exact ratios of the expected online size to the expected offline size at each horizon from 2 to 9. The script checks 64 two-time covariance identities against the joint greedy paths and records the successive permutations in the worked descent example.

To check both reference files from a clone after running both scripts, use `git diff --exit-code -- verification_results.json finite_results.json`.
