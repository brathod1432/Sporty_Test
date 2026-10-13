## [SportyQAD-020][API][Improvement] The user id - the only credential - travels in the URL

- **Severity:** High
- **Type:** Epic

### Summary

The `user-id` is passed as a query string on page load, so the sole credential
that unlocks an account (SportyQAD-019) is written into browser history, server
access logs, proxy logs, `Referer` headers and any screenshot taken of the URL.

Source: incoming test case "Authentication and Session Security (End-to-End)" -
the DevTools/Burp interception and token-tampering checks.

### Reproduction Steps
1. Open the app and watch the address bar.
2. Open DevTools, Network, and look at how the id is delivered.
3. Copy the URL from the address bar and read it end to end.
- Observe: the id is a plain query parameter, visible in the URL.

### Expected Result

The credential travels in a header or an `HttpOnly` cookie, never in the URL.
The page must load without the id being part of the address.

### Observed Result

- The app loads at `https://qae-assignment-tau.vercel.app/?user-id=candidate-AAAAAAAA`.
- The id is therefore recorded in browser history and in the address bar over
  the user's shoulder, shared verbatim in any support ticket, pasted into any
  bug report, and captured in every screenshot of the address bar.
- Any `Referer` sent to a third-party resource carries it.
- It is exposed to anyone with read access to the CDN or proxy access logs.

### Business Impact

The QA evidence in this very repository is a live demonstration: every bug
report and screenshot produced against this app was taken with the account
credential in the address bar. The same leak reaches production traffic logs,
where it is retained long after the user has moved on and is typically visible
to a much wider group of staff and tooling than the account owner.

Because the credential cannot be revoked (SportyQAD-019), a single copy in a log
file is a permanent compromise rather than a recoverable incident.

### Evidence

- App load logged 2026-10-12:
  `https://qae-assignment-tau.vercel.app/?user-id=candidate-AAAAAAAA`.
- Auth probe 2026-10-12: no `Set-Cookie` on the page or the API, so there is no
  alternative channel - the query string is the only delivery mechanism.

### Related

SportyQAD-019 covers the absence of real authentication. This epic is
actionable today and independently: move the id out of the URL even before a
login flow exists.