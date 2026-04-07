# Recency Sweep 2 — Concurrent Work Report

**Date:** 2026-04-07 | **Sweep ID:** 2 | **Window:** Jan 2025 – Apr 2026

## New Papers Found

| Paper | Relevance | Impact on Novelty |
|-------|-----------|-------------------|
| Eilertsen et al. (2025) — "Aligning Attention with Human Rationales..." (arXiv 2511.07065) | **HIGH — our direct baseline** | Confirmed as the SRA paper we replicate in C2. Claims "2.4x better explainability vs baselines." Our C4 achieves +111% comprehensiveness over C2 (their method). No overlap with sparsemax+MSE approach. |

## Threat Assessment

**No new concurrent work introduces sparsemax supervision for hate speech interpretability.**

- SRA (Eilertsen et al.) is known, included as C2, and we beat it.  
- No paper applies sparsemax with ERASER faithfulness evaluation to hate speech.  
- No paper performs the Jain-Wallace adversarial swap test on hate speech models.

## Decision: PROCEED — novelty intact
