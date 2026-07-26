# Variable-length report (R10.8.4 SS1.3)

Vectors may end after X or Y inside the final level; the partial level is represented explicitly with axis-specific uncertainty and the radial interval left unchanged (never padded, never rejected, no nine-digit maximum).

```json
{
 "1678523973": {
  "levels": [
   [
    1,
    6,
    7
   ],
   [
    8,
    5,
    2
   ],
   [
    3,
    9,
    7
   ]
  ],
  "partial": [
   "X"
  ],
  "axis_depths": [
   4,
   3,
   3
  ]
 },
 "16752349783": {
  "levels": [
   [
    1,
    6,
    7
   ],
   [
    5,
    2,
    3
   ],
   [
    4,
    9,
    7
   ]
  ],
  "partial": [
   "X",
   "Y"
  ],
  "axis_depths": [
   4,
   4,
   3
  ]
 },
 "1678295343": {
  "levels": [
   [
    1,
    6,
    7
   ],
   [
    8,
    2,
    9
   ],
   [
    5,
    3,
    4
   ]
  ],
  "partial": [
   "X"
  ],
  "axis_depths": [
   4,
   3,
   3
  ]
 },
 "16782953437": {
  "levels": [
   [
    1,
    6,
    7
   ],
   [
    8,
    2,
    9
   ],
   [
    5,
    3,
    4
   ]
  ],
  "partial": [
   "X",
   "Y"
  ],
  "axis_depths": [
   4,
   4,
   3
  ]
 }
}
```
