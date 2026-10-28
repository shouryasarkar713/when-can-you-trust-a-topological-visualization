# E3 Inspection Summary — structured task-based inspection by a single observer (pre-specified fallback; participant study NOT conducted)

- Inspection records: 13 (one per stimulus, fixed order S01..S13; single observer = the project author)
- Counts describe RECORDED INSPECTION JUDGMENTS of one observer against pre-specified expected properties. They are NOT measured human accuracy, NOT population-level readability, and NOT statistically significant. Computational metrics cited in the basis fields (persistences, gap ratios, component counts, cycle-basis lengths) come from saved results and are separate from these inspection judgments.

| Task | Representation | n | clearly_apparent | ambiguous | visually_obscured | not_represented | matches: yes/partial/no |
|---|---|---|---|---|---|---|---|
| T1 | diagram | 2 | 2 | 0 | 0 | 0 | 2/0/0 |
| T2 | diagram | 2 | 1 | 1 | 0 | 0 | 2/0/0 |
| T3 | mapper | 1 | 1 | 0 | 0 | 0 | 1/0/0 |
| T3 | scatter | 1 | 1 | 0 | 0 | 0 | 1/0/0 |
| T4 | mapper | 3 | 2 | 1 | 0 | 0 | 2/1/0 |
| T5 | scatter | 4 | 4 | 0 | 0 | 0 | 4/0/0 |

Overall (single-observer inspection result): {'clearly_apparent': 11, 'ambiguous': 2}; matches_expected: {'yes': 12, 'partial': 1}.

## Recorded misleading cues / rendering problems
- **S01 (T1, diagram)**: No legend: blue vs orange (H0 vs H1) is not explained in the figure; the dashed top line (essential H0 class) is not explained; as drawn, the essential-class point sits FARTHER from the diagonal (approx. 1.85) than the loop point (1.50), so a reader keying on distance-from-diagonal alone picks the wrong point.
- **S02 (T5, scatter)**: None material: thickness and noise fuzz the exact boundary and a few outliers stray from the band.
- **S03 (T2, diagram)**: Same as S01: unlabeled colors; unexplained dashed line; the unprimed viewing pass initially treated the top-line essential class as the prominent feature before settling on the count 1.
- **S04 (T4, mapper)**: The larger component's small internal cycles could suggest local loops; node-size variation is unexplained; in the NATIVE kk layout the two components are not clearly separated (component bbox IoU 0.036; 6.7% node interleaving) — the clean separation shown here is a property of the component-separated custom rendering; and the disconnected morphology itself is parameter-dependent: at cover (20, 0.50) the same data yields a connected graph with two 20-node cycles (E2).
- **S05 (T5, scatter)**: No axes or scale are drawn; a few outliers; subtle substructure would be hard to see at this density.
- **S06 (T4, mapper)**: Branches can be read as part of the cycle or as appendages; node sizes (cluster memberships) are unexplained; the loop signal vanishes at n_cubes=5 (tree graph) and the graph fragments at (20, 0.20) — parameter-dependent (E2).
- **S07 (T3, scatter)**: Outlier points could be debated as tiny extra components; cluster boundaries are fuzzy at the margins.
- **S08 (T2, diagram)**: No legend: the unprimed viewing pass anchored on the essential H0 point (drawn distance from diagonal approx. 0.68 vs 0.48 for the loops) and answered 1; the figure does not encode that only H1 points count as loops, nor that the dashed-line point is the essential class that never dies.
- **S09 (T5, scatter)**: Same as S07: outliers and fuzzy cluster edges.
- **S10 (T5, scatter)**: Scatter noise fuzzes the lobe boundaries; the central region is cluttered, leaving slight uncertainty between one crossing point and two nearly-touching loops.
- **S11 (T4, mapper)**: The ring-like visual circuit is itself the misleading cue: Mapper graph cycles are not automatically topological loops in the data; nothing in the rendering distinguishes noise-scale cycles (6 nodes) from data-scale loops (16 nodes on the annulus); node sizes unexplained.
- **S12 (T3, mapper)**: Per-group colors and band separation are features of the component-separated custom rendering; in the NATIVE kk layout the three components overlap (component bbox IoU 0.233; 14.4% node interleaving) and the count is much harder to read; node sizes unexplained.
- **S13 (T1, diagram)**: Several orange points sit mildly above the band; 'prominent' is a threshold the figure does not define; overplotting near the origin hides individual short-lived features; colors unlabeled.

## Limitations
- single observer; the observer is the invested author who designed the datasets and had seen the E1/E2 computational results beforehand
- observer bias and retrospective interpretation are possible and acknowledged; expected properties were pre-specified from construction, which limits but does not eliminate bias
- the evidence concerns the produced artifacts and one observer's reading of them — NOT how a population of users would interpret them
- no timing, no confidence ratings, no inferential statistics; no participant data exist for this experiment
- judgments from different tasks are not comparable (task-specific design)

Labeled everywhere as a single-observer inspection — never as a human-participant study.
