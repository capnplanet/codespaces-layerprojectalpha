# Documentation Index

Welcome to the DARPA MoE Intermediary Layer documentation. This guide will help you navigate all available documentation.

## 📚 Complete Documentation Suite

### 1. **Quick Start** → [README.md](../README.md)
Start here if you want to:
- Get the system running quickly
- See basic usage examples
- Understand the make commands
- Run demo queries

**Time to read:** 5 minutes

---

### 2. **Executive Summary** → [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
**👈 READ THIS FIRST for comprehensive understanding**

A Feynman-style explanation covering everything about this repository:

**Contents:**
- **What This Repository Is**: Simple story of MoE intermediary layer
- **What It Does**: Core functions (routing, policy, retrieval, fusion, audit, memory)
- **How It Works**: Complete technical architecture with step-by-step query flow
- **Algorithmic Functions**: All algorithms with locations and purposes
- **Cross-Domain Applications**: Use cases across:
  - Defense & National Security
  - Aerospace Engineering
  - Biopharmaceutical R&D
  - Commercial Applications (enterprise, financial, healthcare, manufacturing)
- **LLM Integration**: Comprehensive strategies and implementation
- **System Guarantees**: What it does and doesn't guarantee
- **Security Model**: Threat boundaries and compliance readiness
- **Future Extensibility**: How to extend and customize

**Time to read:** 45-60 minutes  
**Who should read:** Everyone (technical and non-technical)  
**Format:** Plain language with minimal jargon

---

### 3. **Algorithm Reference** → [ALGORITHM_REFERENCE.md](ALGORITHM_REFERENCE.md)
**Technical deep-dive into all algorithms**

**Contents:**
- Complete algorithm table with complexity analysis
- Detailed descriptions of 10 core algorithms:
  1. BM25 Ranking
  2. Dense Embedding Search
  3. Hybrid Search
  4. Router Scoring
  5. Route Planning
  6. Intent Classification
  7. Policy Evaluation
  8. Answer Fusion
  9. Hash Computation
  10. HMAC Signing
- Mathematical formulas and pseudocode
- Performance benchmarks
- Tuning parameters
- Extensibility examples

**Time to read:** 30-40 minutes  
**Who should read:** Developers, algorithm engineers, researchers  
**Format:** Technical with formulas and code examples

---

### 4. **LLM Integration Guide** → [LLM_INTEGRATION.md](LLM_INTEGRATION.md)
**Step-by-step guide to integrate real LLMs**

**Contents:**
- **Option 1:** Cloud APIs (OpenAI, Anthropic, Google)
  - Complete code examples
  - API key management
  - Cost and latency configuration
- **Option 2:** Self-hosted models (Llama, Mistral)
  - vLLM setup with Docker
  - Ollama integration
  - GPU configuration
- **Option 3:** Hybrid deployment
- **Advanced Use Cases:**
  - Retrieval-Augmented Generation (RAG)
  - Chain-of-Thought reasoning
  - Multi-agent debate
  - Tool-using agents
  - Evaluation and red-teaming
- **Policy Configuration** for LLM access control
- **Monitoring** with Prometheus metrics
- **Troubleshooting** common issues
- **Production Checklist**

**Time to read:** 40-50 minutes  
**Who should read:** Developers integrating LLMs  
**Format:** Practical with complete code examples

---

### 5. **Performance Baseline** → [PERFORMANCE_BASELINE.md](PERFORMANCE_BASELINE.md)
**HF end-to-end KPI definitions and measured baseline results**

**Contents:**
- Baseline benchmark profile and exact command
- KPI definitions (p95 latency, throughput, cost units, policy compliance)
- Latest measured values and pass/fail status
- Thresholds used for `make perf-assert`
- Reproduction steps for Codespaces secrets + HF endpoint mode

**Time to read:** 5-10 minutes  
**Who should read:** Engineers, SRE, MLOps  
**Format:** Operational runbook + measured metrics

---

### 6. **Use Cases and Operational Fit** → [USE_CASES_AND_OPERATIONAL_FIT.md](USE_CASES_AND_OPERATIONAL_FIT.md)
**Defense and commercial use cases grounded in both architecture and measured baseline behavior**

**Contents:**
- Defense and commercial application areas
- What the current repo can credibly claim today
- What the current baseline proves and what it does not prove
- Feynman-style framing for operational fit

**Time to read:** 8-12 minutes  
**Who should read:** Executives, product, engineering, mission owners  
**Format:** Decision-support narrative tied to current implementation

---

### 7. **Security & Compliance**

#### [threat_model.md](threat_model.md)
**Security threat analysis**

**Contents:**
- Scope and assumptions (zero-trust, offline-first, FIPS-friendly)
- Assets (queries, audit logs, policies)
- Threats (injection, unauthorized access, tampering, exfiltration)
- Controls (policy-as-code, HMAC, RBAC, rate limiting)

**Time to read:** 5 minutes  
**Who should read:** Security teams, compliance officers

#### [audit_spec.md](audit_spec.md)
**Audit logging specification**

**Time to read:** 3 minutes  
**Who should read:** Compliance teams, auditors

---

### 8. **Policy & Evidence**

#### [policy_spec.md](policy_spec.md)
**Policy engine specification**

**Time to read:** 3 minutes  
**Who should read:** Security teams configuring policies

#### [evidence_pack.md](evidence_pack.md)
**Evidence generation for compliance**

**Time to read:** 3 minutes  
**Who should read:** Compliance officers

---

## 🎯 Reading Paths by Role

### For Executives & Decision Makers
1. **EXECUTIVE_SUMMARY.md** - Sections: "What This Repository Is", "Cross-Domain Applications", "System Guarantees"
2. **README.md** - Quick demo examples
3. **threat_model.md** - Security overview

**Total time:** 20 minutes

### For Software Engineers (New to Project)
1. **README.md** - Get it running
2. **EXECUTIVE_SUMMARY.md** - Understand architecture
3. **ALGORITHM_REFERENCE.md** - Study algorithms
4. **LLM_INTEGRATION.md** - Integrate your LLM

**Total time:** 2-3 hours

### For Algorithm Researchers
1. **ALGORITHM_REFERENCE.md** - All algorithm details
2. **EXECUTIVE_SUMMARY.md** - Section: "Algorithmic Functions"
3. Source code in `app/services/`

**Total time:** 1 hour

### For Security/Compliance Teams
1. **threat_model.md** - Threat analysis
2. **EXECUTIVE_SUMMARY.md** - Section: "Security Model"
3. **audit_spec.md** - Audit requirements
4. **policy_spec.md** - Policy configuration

**Total time:** 30 minutes

### For Domain Specialists (Defense, Aerospace, Pharma)
1. **EXECUTIVE_SUMMARY.md** - Section: "Cross-Domain Applications" (your domain)
2. **LLM_INTEGRATION.md** - How to customize for your use case
3. **ALGORITHM_REFERENCE.md** - Tuning parameters

**Total time:** 1 hour

### For DevOps/SRE Teams
1. **README.md** - Deployment commands
2. **EXECUTIVE_SUMMARY.md** - Sections: "System Guarantees", "Scaling Recommendations"
3. **LLM_INTEGRATION.md** - Section: "Production Checklist"

**Total time:** 45 minutes

---

## 📊 Documentation Statistics

| Document | Lines | Words | Size | Complexity |
|----------|-------|-------|------|------------|
| EXECUTIVE_SUMMARY.md | 984 | ~15,000 | 33KB | Beginner-friendly |
| ALGORITHM_REFERENCE.md | 521 | ~7,500 | 16KB | Advanced |
| LLM_INTEGRATION.md | 607 | ~9,000 | 19KB | Intermediate |
| README.md | 54 | ~400 | 2KB | Beginner |
| threat_model.md | 29 | ~300 | 834B | Intermediate |
| **Total** | **2,195** | **~32,200** | **71KB** | - |

---

## 🔍 Key Concepts by Document

### Core Concepts to Understand

1. **Mixture of Experts (MoE)** → EXECUTIVE_SUMMARY.md
   - What it is, why it matters, how routing works

2. **Budget-Aware Routing** → ALGORITHM_REFERENCE.md
   - How cost and latency constraints affect expert selection

3. **Hybrid Retrieval** → ALGORITHM_REFERENCE.md
   - BM25 + dense embeddings combined

4. **Policy-as-Code** → EXECUTIVE_SUMMARY.md, policy_spec.md
   - YAML-based security enforcement

5. **Deterministic Replay** → ALGORITHM_REFERENCE.md
   - How hash-based verification works

6. **RBAC + JWT** → EXECUTIVE_SUMMARY.md, threat_model.md
   - Role-based access control

7. **RAG (Retrieval-Augmented Generation)** → LLM_INTEGRATION.md
   - How to implement with LLMs

8. **HMAC Audit Logs** → ALGORITHM_REFERENCE.md, audit_spec.md
   - Tamper-evident logging

---

## 🛠️ Common Tasks → Documentation Mapping

| Task | Primary Document | Secondary Documents |
|------|-----------------|---------------------|
| Install and run system | README.md | - |
| Understand architecture | EXECUTIVE_SUMMARY.md | ALGORITHM_REFERENCE.md |
| Integrate OpenAI | LLM_INTEGRATION.md | EXECUTIVE_SUMMARY.md |
| Deploy self-hosted LLM | LLM_INTEGRATION.md | README.md |
| Tune BM25 parameters | ALGORITHM_REFERENCE.md | EXECUTIVE_SUMMARY.md |
| Configure policies | policy_spec.md | EXECUTIVE_SUMMARY.md |
| Set up RBAC | EXECUTIVE_SUMMARY.md | threat_model.md |
| Generate audit reports | audit_spec.md | EXECUTIVE_SUMMARY.md |
| Scale to production | EXECUTIVE_SUMMARY.md | LLM_INTEGRATION.md |
| Troubleshoot LLM issues | LLM_INTEGRATION.md | - |
| Customize routing logic | ALGORITHM_REFERENCE.md | Source code |
| Add new expert type | LLM_INTEGRATION.md | EXECUTIVE_SUMMARY.md |

---

## 💡 Quick Reference

### File Locations
- **Python code:** `app/` directory
- **Policies:** `policies/*.yaml`
- **Evaluation datasets:** `eval/datasets/`
- **Documentation:** `docs/`
- **Tests:** `tests/`

### Key Files
- **Router logic:** `app/services/router.py`
- **Retrieval algorithms:** `app/services/retrieval.py`
- **Policy engine:** `app/services/policy.py`
- **Expert implementations:** `app/services/experts.py`
- **Main orchestrator:** `app/services/orchestrator.py`
- **API endpoints:** `app/api/routes.py`

### Key Commands
```bash
make install       # Install dependencies
make migrate       # Run database migrations
make up            # Start all services
make test          # Run tests
make lint          # Check code style
make format        # Format code
make sbom          # Generate SBOM
```

---

## 🚀 Getting Started Checklist

- [ ] Read README.md (5 min)
- [ ] Read EXECUTIVE_SUMMARY.md sections 1-3 (20 min)
- [ ] Install and run system with `make install && make migrate && make up`
- [ ] Try demo query from README
- [ ] Read EXECUTIVE_SUMMARY.md sections 4-8 (30 min)
- [ ] Review ALGORITHM_REFERENCE.md for your areas of interest (20 min)
- [ ] If integrating LLMs, read LLM_INTEGRATION.md (40 min)
- [ ] If security/compliance focused, read threat_model.md and audit_spec.md (10 min)

**Total onboarding time: 2-3 hours**

---

## 📞 Support & Contribution

### Documentation Issues
- Unclear explanation → Open issue with "docs:" prefix
- Missing information → Open issue with "docs: missing" prefix
- Incorrect information → Open issue with "docs: correction" prefix

### Code Issues
- Bug found → Open issue with "bug:" prefix
- Feature request → Open issue with "feature:" prefix
- Performance issue → Open issue with "performance:" prefix

### Contributing Documentation
All documentation is written in Markdown and lives in `docs/`:
1. Follow existing style (Feynman-style for EXECUTIVE_SUMMARY)
2. Use clear headings and bullet points
3. Include code examples for technical content
4. Test all commands and code snippets
5. Update this INDEX.md if adding new documents

---

## 🔄 Documentation Versioning

This documentation corresponds to repository version: **v0.1.0**

Last updated: 2026-01-02

**Major sections updated:**
- Added EXECUTIVE_SUMMARY.md with comprehensive Feynman-style explanation
- Added ALGORITHM_REFERENCE.md with technical deep-dive
- Added LLM_INTEGRATION.md with step-by-step integration guide
- Updated README.md with documentation links

---

## 📖 External Resources

### Related Technologies
- **FastAPI:** https://fastapi.tiangolo.com/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **Redis:** https://redis.io/docs/
- **Celery:** https://docs.celeryproject.org/
- **OpenTelemetry:** https://opentelemetry.io/docs/
- **Prometheus:** https://prometheus.io/docs/
- **Grafana:** https://grafana.com/docs/

### LLM Providers
- **OpenAI:** https://platform.openai.com/docs
- **Anthropic (Claude):** https://docs.anthropic.com
- **Google (Gemini):** https://ai.google.dev/docs
- **vLLM (self-hosted):** https://docs.vllm.ai
- **Ollama (self-hosted):** https://ollama.ai/docs

### Algorithms & Concepts
- **BM25:** Robertson & Zaragoza (2009) "The Probabilistic Relevance Framework"
- **Sentence Transformers:** https://www.sbert.net/
- **HMAC:** FIPS 198-1 specification
- **SHA-256:** FIPS 180-4 specification

---

## 📋 Documentation Maintenance

**Responsibility:** Documentation should be updated when:
- API endpoints change
- New features added
- Algorithms modified
- Dependencies updated
- Security model changes

**Review Schedule:**
- After each major release
- After significant architectural changes
- When user feedback indicates confusion

**Quality Standards:**
- All code examples must be tested
- All commands must be verified
- Cross-references must be valid
- Screenshots updated if UI changes

---

**Welcome to the DARPA MoE Intermediary Layer project!**

Start with the [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) for the best onboarding experience.
