# Synthetic instances

All supplied instances are handcrafted for education and have no connection to
real terminal, vessel, or equipment data. Array order determines deterministic
tie-breaking in the reference enumeration. No random generator is used yet.

| File | Purpose | Units |
| --- | --- | --- |
| `berth_tiny_v1.json` | Two vessels, two berths, two time slots; one-slot service. | One abstract slot = 60 illustrative minutes. |
| `cranes_tiny_v1.json` | Two cranes, two vessels, two periods; all vessels available throughout. | Abstract work units, not calibrated container moves. |
| `disruption_tiny_v1.json` | One-slot delay to V1, with an optional stability weight. | Waiting slots per changed vessel. |

Slots represent half-open service intervals `[t, t+1)`. Arrivals are earliest
permitted start slots. A berth can serve only one vessel per slot. The crane
instance is independent of the berth schedule: it assumes both vessels are
available for service in both periods. Oversupply is allowed and clipped in
served-demand metrics. Cranes may be idle.

These original synthetic materials use the repository's Apache-2.0 license.
