## [SportyQAD-009][UI] Profile icon does nothing - no profile, history, or wallet details reachable

- **Severity:** Medium
- **Type:** Bug

### Reproduction Steps
1. Open the app with a valid `?user-id=`.
2. Locate the circular avatar (person) icon in the red header, right of the balance pill.
3. Click it (icon, its `div.avatar` parent, any header control).
4. Observe: absolutely nothing happens - no dropdown, modal, navigation, or panel.

### Expected Result
Clicking the profile icon opens profile details and routes to placed-bet history and wallet details.

### Observed Result
The icon is a plain `span.person` inside `div.avatar` (not a button, no click handler); the click is swallowed with zero UI change, so profile, history, and wallet details are unreachable from anywhere in the app. (History capability itself is tracked as Epic SportyQAD-007; this defect is the dead control.)

### Business Impact
Users have no path to their account details or wager
history - combined with the receipt-only bet record, their money trail is
invisible after every placement.

### Evidence
`../screenshots/profile_click2.png` (unchanged page
after click) + probe log: 1 `span` with text `person`, parent `div.avatar`,
click produces no page change.
