``` mermaid
flowchart TD
  A(Start) --> B(Define variables and paths)
  B --> C(For each file in base path)
  C --> D{Is HTML file}
  D -- Yes --> E(Call Get Body Content)
  E --> F{For each detection}
  F --> G(Check if TrackID exists in DB)
  G --> H(If not, create entry)
  H --> I(Check SubID unique)
  I --> J(Add detection to DB)
  F --> D
  D -- No --> K{Is JPG file}
  K -- Yes --> L(Extract TrackID and SubID)
  L --> M(Find detection in DB)
  M --> N{Does path match}
  N -- Yes --> O(Increment Images count)
  N -- No --> P(Search all SubIDs for path)
  P --> Q{Path found}
  Q -- Yes --> R(Increment Images count)
  Q -- No --> C
  K -- No --> C
  C --> S(Write CSV)
  S --> T(End)
```
