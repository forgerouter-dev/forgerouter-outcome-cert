# ratekit

A token bucket rate limiter, kept small enough to read in one sitting.

## Why this repository exists

It is the certification host for one specific piece of machinery in ForgeRouter: that a GitHub
`check_suite` event on the merge commit of a reviewed pull request is received, matched back to
the review session, and recorded as a decision outcome.

That loop had been wired for a long time and had never once been observed to fire, because it
only fires when CI **fails** on the merge commit of a **merged** pull request - a combination no
previous test had produced. The code here is real and the tests are real; the repository is small
so the signal is unambiguous.
