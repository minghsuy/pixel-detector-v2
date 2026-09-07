<!-- REVIEW-PROCESS-VERSION: 3 -->

<!-- REVIEW-PROCESS-BLOCK:START -->
## Review convergence

Automated review validates a frozen candidate; it is not an iterative coding loop.
Open implementation PRs as drafts, finish deterministic preflight, and request all
configured semantic reviewers only after freezing the head. Classify all feedback
before editing and make one consolidated correction batch rather than one push per
comment.

A **review round** is one complete feedback cycle on a frozen candidate: every
semantic reviewer the repository contract requires is requested once, and together
they return at least one new finding. Several reviewers on the same frozen head are
one round, not one round each — that is what keeps rounds one-to-one with
correction batches. Rounds one and two may each be answered by exactly one
consolidated batch, so `REVIEW-CORRECTION-BATCHES` starts at `0` and has a hard
maximum of `2`.

A third round receives dispositions and no fix push. Close the PR, name the
structural or scope problem it exposed, and take one of three routes: rebuild the
change from the ground up, split it into smaller pull requests, or carry the
verified work into a successor issue. Each starts a fresh review envelope.

Count rounds, not root-cause families. Root-cause counting is subjective, and
grouping each new finding into an existing family kept pull requests alive through
arbitrarily many passes. A cycle that returns no new finding consumes neither a
round nor a batch, and neither does an infrastructure, authentication, quota, or
runner failure. The stop rule never authorizes merging a known blocker. Merge only
when CI and every reviewer required by the repository contract agree on the same
unchanged head and base SHAs.
<!-- REVIEW-PROCESS-BLOCK:END -->
