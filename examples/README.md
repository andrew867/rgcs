# Example vector lists

```bash
python -m r1053 path $(grep -v '^#' path_erie_toronto.txt | tr '\n' ' ')
python -m r1053 polygon "$(grep -v '^#' polygon_orange_stonehenge.txt | paste -sd,)"
```

| file | shows |
|---|---|
| `vectors_basic.txt` | the seven known vectors, annotated |
| `path_erie_toronto.txt` | two fit anchors, 178.846 km |
| `path_toronto_drummondville.txt` | 582.465 km via the Kingston–Montréal corridor |
| `polygon_orange_stonehenge.txt` | four branch-117 vectors over Wiltshire, 105.268 km² |
| `polygon_b01_contradiction.txt` | one vector, two admissible pinnings, 5121.7 km apart |

The last one needs an explicit second coordinate, because it is the *same* vector
twice:

```bash
python -m r1053 path 165879243 165879243 --b-latlon 45.8418969,-72.6788251
```

Anchor vectors land correctly because they were fitted. That is
`TRAINING_EQUALITY`, not confirmation.
