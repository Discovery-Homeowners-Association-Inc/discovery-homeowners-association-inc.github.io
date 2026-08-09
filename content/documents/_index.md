---
title: "Documents & Forms"
summary: "Every association form and notice in one place."
weight: 60
cascade:
  # A document is a PDF, not a web page. `render: never` means no HTML page is
  # generated for it, while `list: always` keeps it in .Site.RegularPages so it
  # still appears here and in the search index — pointing at the PDF itself.
  #
  # target restricts this to child pages. Without it the cascade also applies
  # to THIS page, and the documents index itself is never rendered.
  - build:
      render: never
      list: always
    target:
      kind: page
---

Forms, contracts, and notices published by the association. Each one links
straight to the PDF.

The association's **governing documents** — the By-Laws, the Declaration of
Covenants, and the Articles of Incorporation — are kept separately, because they
are the legal instruments the neighborhood actually runs on and they have one
canonical home.
