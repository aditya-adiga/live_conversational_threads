# Feature Roadmap & Prioritization

## Analysis Framework

Each feature is evaluated on:
- **Impact**: Value to users (1-5)
- **Effort**: Development complexity (1-5, 1=easy)
- **Dependencies**: What must be built first
- **Risk**: Technical/product uncertainty (1-5, 1=low)
- **ROI Score**: Impact / (Effort + Risk)

---

## Phase 1: Foundation (Weeks 1-5) - HIGHEST PRIORITY

### ✅ Already Completed
- [x] Obsidian Canvas interoperability
- [x] Basic conversation tree visualization
- [x] Fact-checking integration

### 🔨 Currently Proposed
- [ ] **Google Meet Transcript Support** (ADR-001)
  - **Impact**: 5 - Unlocks all speaker-aware features
  - **Effort**: 4 - Major data model changes
  - **Risk**: 3 - Format parsing complexity
  - **ROI**: 0.7
  - **Status**: ADR written, ready for implementation

---

## Phase 2: Core Speaker Features (Weeks 6-10)

### 2.1 Bandwidth Metrics (Week 6-7)
**Description**: Track who's talking most, interruption patterns, speaking time distribution

- **Impact**: 4 - Immediately useful, quantifiable insights
- **Effort**: 2 - Simple once speaker data exists
- **Dependencies**: Google Meet transcript support (Phase 1)
- **Risk**: 1 - Straightforward calculation
- **ROI**: 2.0 ⭐
- **Technical Approach**:
  - Count words/utterances per speaker
  - Track speaker transitions for interruption detection
  - Visualize as pie chart + timeline
  - Export metrics as CSV

**Deliverables:**
- `/conversations/{id}/bandwidth-metrics` endpoint
- `BandwidthMetrics.jsx` component (pie chart, bar chart)
- Speaker talk-time timeline visualization
- Interruption frequency heatmap

---

### 2.2 Claim Taxonomy System (Week 8-9)
**Description**: Classify claims as factual, normative, or worldview/assumption-based

- **Impact**: 5 - Core intellectual value, unique differentiator
- **Effort**: 4 - Requires sophisticated LLM prompting + UI
- **Dependencies**: Google Meet transcript support
- **Risk**: 4 - LLM accuracy on nuanced claims
- **ROI**: 0.6
- **Technical Approach**:
  - Extend claim detection to classify types
  - Add `claim_type: "factual" | "normative" | "worldview"` field
  - LLM prompt engineering for accurate classification
  - UI to filter/group by claim type

**Example Classifications:**
```
Factual: "The API latency is 200ms" → verifiable
Normative: "We should prioritize user experience" → value judgment
Worldview: "Data-driven decisions are always better" → ideological assumption
```

**Deliverables:**
- Enhanced claim detection with taxonomy
- `ClaimTypeFilter.jsx` component
- Claim relationship graph (show worldview → normative → factual chains)
- Export claims by type

---

### 2.3 Shared Transparent View (Week 10)
**Description**: All participants can see the same real-time visualization during conversation

- **Impact**: 4 - Promotes transparency, reduces misunderstanding
- **Effort**: 3 - WebSocket broadcasting, sync challenges
- **Dependencies**: None (works with existing system)
- **Risk**: 2 - Real-time sync bugs
- **ROI**: 1.3 ⭐
- **Technical Approach**:
  - WebSocket room per conversation
  - Broadcast node updates to all connected clients
  - Show "X people viewing" indicator
  - Collaborative cursor positions (optional)

**Deliverables:**
- WebSocket room management
- Real-time sync of graph updates
- Viewer list component
- Collaborative highlighting (optional)

---

## Phase 3: AI-Assisted Facilitation (Weeks 11-15)

### 3.1 Parallel Thread Tracking (Week 11-12)
**Description**: Track tangents that get paused, retrieve them during lulls

- **Impact**: 5 - Addresses core "working memory" problem
- **Effort**: 4 - Complex state management + retrieval logic
- **Dependencies**: None
- **Risk**: 3 - Determining "right time" to resurface
- **ROI**: 1.0 ⭐⭐
- **Technical Approach**:
  - Detect topic pivots without closure
  - Track "paused threads" queue with context
  - Detect conversation lulls (silence, filler words, energy drop)
  - LLM-powered relevance scoring for retrieval
  - Surface top 3 threads during lulls

**Deliverables:**
- Paused thread detection algorithm
- Thread queue storage (priority queue)
- Lull detection (pause duration, energy metrics)
- `PausedThreads.jsx` sidebar component
- "Resurface this thread" suggestions

---

### 3.2 Tangent & Connection Suggestions (Week 13)
**Description**: Real-time suggestions for related topics, connections to explore

- **Impact**: 4 - Enriches conversation depth
- **Effort**: 3 - LLM context window + retrieval
- **Dependencies**: Parallel thread tracking
- **Risk**: 3 - Relevance accuracy, timing
- **ROI**: 1.0
- **Technical Approach**:
  - Semantic search over past nodes
  - External knowledge base (Wikipedia, papers)
  - LLM-generated "what if we explored..." prompts
  - Non-intrusive UI (subtle sidebar)

**Deliverables:**
- Real-time semantic search endpoint
- `TangentSuggestions.jsx` component
- External knowledge integration
- User feedback loop (thumbs up/down)

---

### 3.3 Crux Detection (Week 14)
**Description**: Identify key points of agreement/disagreement forming

- **Impact**: 5 - Accelerates productive debate
- **Effort**: 4 - NLP + disagreement modeling
- **Dependencies**: Claim taxonomy, speaker support
- **Risk**: 4 - Nuanced disagreement detection
- **ROI**: 0.7
- **Technical Approach**:
  - Track opposing claims between speakers
  - Identify shared assumptions vs divergences
  - Visualize as "crux tree" (what hinges on what)
  - Suggest "double crux" questions

**Deliverables:**
- Crux detection algorithm
- `CruxTree.jsx` visualization
- Agreement/disagreement heatmap
- "Test this crux" prompts

---

### 3.4 Goal Tracking & Drift Detection (Week 15)
**Description**: Track conversation goals, detect unproductive drift

- **Impact**: 4 - Keeps conversations on track
- **Effort**: 3 - Goal modeling + drift metrics
- **Dependencies**: None
- **Risk**: 2 - Defining "productive" subjectively
- **ROI**: 1.3 ⭐
- **Technical Approach**:
  - User sets goals at start ("learn X", "decide Y", "build rapport")
  - Track goal-relevant content percentage
  - Alert when drift exceeds threshold
  - Suggest course corrections

**Deliverables:**
- Goal setting UI at conversation start
- Goal tracking metrics
- Drift detection algorithm
- `GoalProgress.jsx` dashboard
- "Getting off-track" alerts

---

## Phase 4: Advanced Intelligence (Weeks 16-20)

### 4.1 Steelmanning & Legibilization (Week 16-17)
**Description**: AI helps clarify and strengthen unclear arguments

- **Impact**: 5 - Improves communication quality
- **Effort**: 3 - LLM prompting, careful UX
- **Dependencies**: Speaker support
- **Risk**: 3 - Must avoid putting words in mouths
- **ROI**: 1.1 ⭐⭐
- **Technical Approach**:
  - Detect unclear/ambiguous statements
  - Generate "Did you mean..." clarifications
  - Steelman weak arguments (optional, with consent)
  - Show original vs clarified side-by-side

**Deliverables:**
- Ambiguity detection
- Clarification generation
- Steelman mode toggle
- User approval workflow

---

### 4.2 Contradiction & Fallacy Detection (Week 18)
**Description**: Flag logical contradictions and common fallacies

- **Impact**: 4 - Improves argument quality
- **Effort**: 4 - Logic modeling + pattern recognition
- **Dependencies**: Claim taxonomy
- **Risk**: 4 - False positives damage trust
- **ROI**: 0.5
- **Technical Approach**:
  - Rule-based fallacy detection (ad hominem, straw man, etc.)
  - Contradiction detection across claims
  - Confidence scores (don't flag unless >80% confident)
  - Educational explanations

**Deliverables:**
- Fallacy detection rules
- Contradiction checker
- `FallacyWarning.jsx` component (subtle)
- Fallacy explanation tooltips

---

### 4.3 Fact-Fetching Agents (Week 19)
**Description**: Spin up agents to fetch supporting facts during conversation

- **Impact**: 4 - Reduces context switching
- **Effort**: 3 - Agent orchestration + API integrations
- **Dependencies**: None
- **Risk**: 3 - Rate limits, latency
- **ROI**: 1.0
- **Technical Approach**:
  - Detect factual questions ("What's the GDP of...")
  - Trigger Perplexity/Wikipedia/Wolfram agents
  - Cache results
  - Surface answers non-intrusively

**Deliverables:**
- Agent orchestration system
- Multiple knowledge source integrations
- `FactFetchResults.jsx` component
- "Fetching..." loading states

---

### 4.4 Interruption Culture Optimization (Week 20)
**Description**: Learn and enforce local norms for interruptions

- **Impact**: 3 - Contextual to group culture
- **Effort**: 4 - Norm learning + enforcement
- **Dependencies**: Bandwidth metrics
- **Risk**: 4 - Cultural sensitivity, false positives
- **ROI**: 0.4
- **Technical Approach**:
  - Learn baseline interruption patterns per group
  - Detect anomalies (sudden increase)
  - Prompt: "Higher interruptions than usual, intentional?"
  - User configures norms

**Deliverables:**
- Norm baseline calculation
- Anomaly detection
- User preference settings
- Gentle nudges (not intrusive)

---

## Phase 5: Network Effects & Integrations (Weeks 21-25)

### 5.1 Multi-Source Aggregation (Week 21-23)
**Description**: Import from Slack, Discord, Twitter, WhatsApp, etc.

- **Impact**: 5 - Massive value, cross-platform insights
- **Effort**: 5 - Each integration is custom work
- **Dependencies**: Google Meet transcript support (similar architecture)
- **Risk**: 3 - API changes, rate limits
- **ROI**: 0.7
- **Technical Approach**:
  - Generic "message stream" abstraction
  - Platform-specific adapters
  - Unified conversation format
  - OAuth flows for each platform

**Priority Order:**
1. Slack (enterprise focus)
2. Discord (community focus)
3. WhatsApp (personal focus)
4. Twitter/X (public discourse)

**Deliverables:**
- Message stream abstraction
- 2-3 platform integrations
- OAuth management
- Unified import UI

---

### 5.2 Obsidian Deep Integration (Week 24)
**Description**: Fuzzy search, auto-linking to Obsidian notes, tag suggestions

- **Impact**: 4 - Leverages existing Obsidian ecosystem
- **Effort**: 3 - Obsidian plugin development
- **Dependencies**: Canvas interop (already done)
- **Risk**: 2 - Plugin API stable
- **ROI**: 1.3 ⭐
- **Technical Approach**:
  - Build Obsidian plugin
  - Two-way sync: LCT ↔ Obsidian
  - Auto-link conversation topics to notes
  - Tag suggestions based on Obsidian vault

**Deliverables:**
- Obsidian plugin (TypeScript)
- Bidirectional sync
- Auto-linking algorithm
- Tag suggestion engine

---

### 5.3 CRM Features for Legal/Business (Week 25)
**Description**: Client relationship management, meeting summaries for legal domain

- **Impact**: 5 - Monetization opportunity (B2B)
- **Effort**: 4 - Domain-specific features
- **Dependencies**: Multi-source aggregation
- **Risk**: 2 - Well-defined use case
- **ROI**: 1.0 ⭐⭐
- **Technical Approach**:
  - Client entity extraction
  - Meeting summary templates (legal focus)
  - Action item tracking
  - Billable hours estimation

**Deliverables:**
- Entity extraction (clients, cases)
- Legal summary templates
- Action item tracker
- Billable hours dashboard

---

## Phase 6: Privacy & Open Source (Weeks 26-30)

### 6.1 Privacy-First Architecture (Week 26-28)
**Description**: Own your data, on-premise deployment, encryption

- **Impact**: 5 - Competitive advantage vs Google Recorder
- **Effort**: 4 - Security hardening + deployment
- **Dependencies**: None
- **Risk**: 2 - Security expertise needed
- **ROI**: 1.0 ⭐⭐
- **Technical Approach**:
  - End-to-end encryption option
  - Self-hosted deployment (Docker)
  - Local-only mode (no cloud)
  - Data export/delete tools (GDPR compliance)

**Deliverables:**
- E2E encryption implementation
- Docker compose for self-hosting
- Local-only mode
- GDPR compliance tools

---

### 6.2 Open Source Release (Week 29-30)
**Description**: Open source core, build community

- **Impact**: 5 - Community contributions, trust
- **Effort**: 3 - Documentation, contributor guidelines
- **Dependencies**: Privacy architecture
- **Risk**: 2 - Support burden
- **ROI**: 1.3 ⭐
- **Approach**:
  - Choose license (AGPL or Apache)
  - Clean up code, add docs
  - Contribution guidelines
  - Issue templates
  - Community Discord/forum

---

## Prioritization Summary

### Immediate (Weeks 1-10) - MVP Features
1. ✅ Obsidian Canvas interop (DONE)
2. 🔨 Google Meet transcript + speaker support (ADR-001)
3. 🎯 Bandwidth metrics (highest ROI: 2.0)
4. 🎯 Shared transparent view (ROI: 1.3)
5. 🎯 Claim taxonomy (unique value)

### Near-term (Weeks 11-20) - Differentiation
6. 🎯 Parallel thread tracking (ROI: 1.0, core feature)
7. 🎯 Goal tracking & drift detection (ROI: 1.3)
8. 🎯 Steelmanning (ROI: 1.1)
9. Tangent suggestions (ROI: 1.0)
10. Crux detection (high impact, but complex)

### Long-term (Weeks 21-30) - Scale & Monetization
11. 🎯 Privacy architecture (competitive advantage)
12. 🎯 CRM features (B2B monetization)
13. 🎯 Obsidian deep integration (leverage ecosystem)
14. Multi-source aggregation (massive scope)
15. Open source release (community building)

---

## Recommended Development Order

**Sprint 1-5 (Weeks 1-10): Foundation + Quick Wins**
1. Implement Google Meet transcript support (ADR-001)
2. Build bandwidth metrics (fast ROI)
3. Add shared transparent view (collaboration unlock)
4. Implement claim taxonomy (unique value)

**Sprint 6-10 (Weeks 11-20): Core Intelligence**
5. Parallel thread tracking (working memory solution)
6. Goal tracking & drift detection (productivity)
7. Steelmanning & legibilization (quality)
8. Tangent suggestions (depth)

**Sprint 11-15 (Weeks 21-30): Scale & Business**
9. Privacy-first architecture (trust)
10. CRM features (monetization)
11. Obsidian deep integration (ecosystem)
12. Open source release (community)

---

## Features to Defer or Drop

### Defer (Not Essential for MVP)
- **Interruption culture optimization**: Too culturally nuanced, risk of offense
- **Contradiction & fallacy detection**: High false positive risk
- **Multi-source aggregation**: Massive scope, each platform is a project

### Drop (Low ROI or High Risk)
- **Real-time note suggestions**: Overlaps with Obsidian integration
- **Fact-fetching agents**: Nice-to-have, not core

---

## Success Metrics by Phase

**Phase 1 (Weeks 1-10):**
- [ ] 100+ conversations imported from Google Meet
- [ ] Bandwidth metrics used in 60%+ of multi-speaker conversations
- [ ] 5+ active users providing feedback

**Phase 2 (Weeks 11-20):**
- [ ] Parallel threads resurfaced successfully 70%+ of time
- [ ] Goal tracking reduces drift by 30%
- [ ] Users report clearer communication

**Phase 3 (Weeks 21-30):**
- [ ] 10+ self-hosted deployments
- [ ] 3+ paying B2B customers (legal/consulting)
- [ ] 50+ GitHub stars, 5+ contributors

---

## Risk Mitigation

1. **LLM Accuracy**: Always show confidence scores, allow user correction
2. **Privacy**: Make privacy features opt-in, clear data policies
3. **Scope Creep**: Stick to roadmap, resist feature bloat
4. **Technical Debt**: Refactor every 3-4 sprints
5. **User Confusion**: Extensive user testing, progressive disclosure

---

## Questions for Discussion

1. **Monetization**: Open core model? Freemium? Enterprise only?
2. **LLM Costs**: Who pays for inference (user API keys vs hosted)?
3. **Target User**: Researchers? Teams? Individuals? Legal professionals?
4. **Mobile**: Should we build mobile apps or web-only?
5. **Real-time Priority**: How important is live audio vs transcript import?

---

## Next Steps

1. **Review ADR-001** - Approve Google Meet transcript approach
2. **Validate Priorities** - Which features resonate most?
3. **Choose Sprint 1 Focus** - Start implementation
4. **Set Success Metrics** - Define what "good" looks like
5. **Build in Public?** - Share progress for feedback/visibility
