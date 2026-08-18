# Chapter 4 colour and label register

## Cluster identity

| Mode | Cluster | Descriptor | Colour |
|---|---|---|---|
| Rail | C0 | outer arrival-oriented | `#0072B2` |
| Rail | C1 | central departure-oriented | `#E69F00` |
| Rail | C2 | central interchange, direction-balanced | `#009E73` |
| Rail | C3 | late-night, extended-duration persistent | `#CC79A7` |
| Rail | C4 | inner-middle ring mixed | `#56B4E9` |
| Bus | C0 | low activity, weak night-persistence | `#4C93D3` |
| Bus | C1 | relatively high activity, stronger night-persistence | `#D1284B` |
| Bus | C2 | moderate activity and persistence, transitional | `#00A6A6` |
| Bus | C3 | moderate activity with destination characteristics | `#1B3A6B` |

Cluster colours identify clusters only. Rail and Bus palettes are deliberately
different: equal cluster numbers have no shared meaning across modes.

## Movement identity

| Mode | Movement | Colour | Line style |
|---|---|---|---|
| Rail | Entry | `#222222` | solid |
| Rail | Exit | `#757575` | dashed |
| Bus | Boarding | `#222222` | solid |
| Bus | Alighting | `#757575` | dashed |

Movement colour/line style never encodes cluster identity. Small multiples,
panel headings and direct cluster labels retain cluster identification in
grayscale and for colour-vision accessibility.
