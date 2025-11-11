# Live Conversational Threads - Product Vision

**Status**: Draft
**Last Updated**: 2025-11-10
**Owner**: Product Team

## Mission Statement

Create a privacy-first, AI-assisted conversation analysis tool that helps humans have better conversations by:
1. **Tracking parallel insights** that emerge during discourse
2. **Decomposing implicit claims** (factual, normative, worldview)
3. **Facilitating real-time** with intelligent nudges and suggestions
4. **Respecting privacy** through open-source, self-hosted architecture

## Core Philosophy

**The Alignment Problem as Product:**
> "I want the model to chunk my linear conversations JUST the way I would segment it. That is where the alignment aspect comes in."

This project serves dual purposes:
1. **Product**: Improve human conversation quality through AI assistance
2. **Research**: Test alignment approaches on a concrete, measurable task (conversation segmentation)

## Competitive Positioning

### vs Google Recorder
| Feature | Google Recorder | LCT |
|---------|----------------|-----|
| **Privacy** | Cloud storage, closed source | Self-hosted, open source |
| **Platform** | Pixel only | Platform agnostic |
| **Data Ownership** | Google owns | User owns |
| **Speaker Analytics** | Basic | Deep (bandwidth, interruptions, cruxes) |
| **Conversation Facilitation** | None | Real-time nudges, suggestions |
| **Multi-source** | Audio only | Calls, chats, social media |
| **Claim Analysis** | None | Factual/Normative/Worldview taxonomy |

### Unique Selling Propositions (USPs)

1. **Privacy-First**: Own your data, open source, self-hostable
2. **Parallel Thread Tracking**: Never lose a tangent again
3. **Claim Decomposition**: Understand the implicit worldviews in discourse
4. **Real-time Facilitation**: AI as conversation coach, not just recorder
5. **Multi-source Aggregation**: Unified view across all communication channels
6. **Obsidian Integration**: Seamless knowledge management workflow
7. **Personal Alignment Training**: Fine-tune on your own segmentation preferences

## Feature Categories

### Tier 1: Foundation (MVP)
*Current state + Google Meet transcripts*

- [x] Live audio streaming with chunking
- [x] Conversation graph visualization (structural + contextual)
- [x] Bookmarks and contextual progress markers
- [x] Obsidian Canvas export/import
- [ ] **Google Meet transcript import with speaker diarization** (ADR-001)

### Tier 2: Core Differentiators (Next 3 months)
*Features that set us apart*

- [ ] **Parallel Thread Management** (ADR-002)
  - Track tangents as they emerge
  - Suggest retrieval during conversation lulls
  - Queue of pinned topics with opportunity cost visibility

- [ ] **Claim Taxonomy System** (ADR-003)
  - Factual claims (verifiable)
  - Normative claims (ought statements)
  - Worldview assumptions (implicit ideology)
  - Automatic classification with confidence scores

- [ ] **Speaker Dynamics Dashboard** (ADR-004)
  - Bandwidth hogging metrics (who talks most)
  - Interruption patterns
  - Turn-taking balance
  - Speaking time heatmaps

### Tier 3: AI Facilitation (3-6 months)
*Real-time conversation assistance*

- [ ] **Conversation Lull Detection** (ADR-005)
  - Identify natural pauses
  - Suggest tangent retrieval at appropriate moments
  - Score "richness potential" of dormant threads

- [ ] **Crux Detection** (ADR-006)
  - Identify agreement/disagreement points
  - Surface underlying assumptions causing divergence
  - Suggest clarifying questions

- [ ] **Real-time Suggestions**
  - Tangent connections ("This relates to [earlier topic]")
  - Fact-checking requests
  - Steelmanning unclear statements
  - Fallacy flagging

- [ ] **Agent-Assisted Research**
  - Spin out background agents to fetch facts
  - "Prayer for memes" fulfillment
  - Context injection at appropriate moments

### Tier 4: Meta-Conversation Features (6-12 months)
*Help groups optimize their discourse norms*

- [ ] **Goal Tracking & Drift Detection**
  - Set conversation intentions (clarify, bond, learn X, get advice)
  - Measure progress toward goal
  - Alert when rambling or quality-per-token drops

- [ ] **Local Norm Optimization**
  - Detect interruption culture
  - Suggest norm adjustments
  - A/B test facilitation strategies

- [ ] **Shared Transparency View**
  - All participants see the same graph in real-time
  - Collaborative thread management
  - Democratic "pin topic" voting

### Tier 5: Ecosystem Integration (12+ months)
*Network effects and multi-platform*

- [ ] **Multi-source Aggregation**
  - Import from Slack, Discord, Twitter DMs, email
  - Unified conversation history across channels
  - Cross-platform thread linking

- [ ] **Obsidian Deep Integration**
  - Auto-create notes from transcription
  - Fuzzy search across all conversations
  - Bidirectional linking with existing vault
  - CRM functionality

- [ ] **Legal/Professional Domains**
  - Compliance-ready audit trails
  - Deposition analysis
  - Meeting minutes automation
  - Action item extraction

## Known Issues & Risks

### Silent Failures
1. **Audio-to-text accuracy**: No user visibility when transcription is wrong
2. **Hallucinated summaries**: LLM may invent topics not actually discussed
3. **Bandwidth stats missing**: Current version lacks speaker participation metrics

### Technical Debt
1. Live streaming and transcript processing use different code paths
2. No A/B testing framework for segmentation quality
3. Limited observability into LLM decision-making
4. No user feedback loop for improving segmentation

### Privacy & Ethics
1. Recording consent flow unclear
2. Speaker identification may reveal PII
3. Claim classification could introduce bias
4. Facilitation suggestions might manipulate discourse

## Success Metrics

### Product Metrics
1. **Adoption**: 1000 weekly active users within 6 months
2. **Retention**: 60% 30-day retention
3. **Engagement**: Average 3 conversations analyzed per user per week
4. **Quality**: 80% user satisfaction with segmentation accuracy

### Alignment Research Metrics
1. **Segmentation Accuracy**: >90% agreement between user and LLM chunking
2. **Fine-tuning Effectiveness**: Personal model outperforms base by 15%+
3. **Claim Classification**: >85% accuracy on factual/normative/worldview taxonomy
4. **Interpretability**: Users can explain why LLM chose each segment boundary

## Target Users

### Primary Personas

**1. The Researcher (You)**
- Alignment researcher exploring concrete alignment problems
- Needs fine-grained control and interpretability
- Willing to tolerate rough edges for cutting-edge features
- Values privacy and data ownership

**2. The Facilitator**
- Professional meeting facilitators, coaches, mediators
- Needs real-time assistance during conversations
- Values speaker dynamics insights
- Wants to improve group discourse quality

**3. The Knowledge Worker**
- Researchers, writers, consultants
- Has many conversations across multiple platforms
- Needs to extract insights and action items
- Wants Obsidian integration

**4. The Privacy Advocate**
- Uncomfortable with Google/corporate data collection
- Willing to self-host
- Values open source
- Technically capable

### Secondary Personas

**5. The Legal Professional**
- Lawyers, paralegals, compliance officers
- Needs audit trails and searchable records
- Values accuracy and reliability
- Has budget for professional features

**6. The Team Lead**
- Manages distributed teams
- Needs meeting analytics and action tracking
- Wants to improve team communication patterns
- Values transparency

## Development Principles

### 1. Measurable Alignment
Every feature should have a clear alignment analog:
- Segmentation accuracy = Value alignment accuracy
- Claim decomposition = Understanding human values
- Facilitation = Helpful, harmless, honest assistance

### 2. User Feedback Loops
Build in continuous user correction:
- Allow manual re-segmentation with explanations
- Collect user preferences on facilitation suggestions
- A/B test prompts and show users the differences

### 3. Privacy by Design
- Local-first architecture where possible
- Encryption at rest and in transit
- Clear data retention policies
- Easy data export and deletion

### 4. Open Source Everything
- Core functionality open source
- Transparent algorithms
- Community contributions welcome
- Optional paid hosting/enterprise features

### 5. Iterative Deployment
- Ship MVPs quickly
- Gather user feedback
- Iterate based on real usage
- Don't wait for perfection

## Roadmap Timeline

**Q1 2025** (Current)
- ✅ Live audio streaming
- ✅ Graph visualization
- ✅ Obsidian Canvas integration
- 🚧 Google Meet transcript support (ADR-001)

**Q2 2025**
- Parallel thread management (ADR-002)
- Claim taxonomy system (ADR-003)
- Speaker dynamics dashboard (ADR-004)
- Privacy architecture refinement

**Q3 2025**
- Real-time conversation facilitation
- Crux detection
- Lull detection and retrieval
- Personal fine-tuning experiments

**Q4 2025**
- Goal tracking and drift detection
- Multi-source aggregation (Slack, Discord)
- Obsidian deep integration
- Public beta launch

**2026**
- Legal domain features
- Network effects and sharing
- Mobile apps
- Enterprise features

## Open Questions

1. **Fine-tuning approach**: RLHF vs supervised learning vs preference learning for personal alignment?
2. **Real-time latency**: How fast must facilitation suggestions be to be useful?
3. **Facilitation ethics**: When does helpful suggestion become manipulation?
4. **Business model**: Open source + paid hosting? Freemium? Enterprise licensing?
5. **Scaling architecture**: When to migrate from GCS to distributed system?
6. **Community vs product**: Should this be a tool or a platform?

## References

- [ADR-001: Google Meet Transcript Support](./adr/ADR-001-google-meet-transcript-support.md)
- [The Alignment Problem](https://www.amazon.com/Alignment-Problem-Machine-Learning-Values/dp/0393635821)
- [Discourse Quality Metrics](https://www.kialo.com/quality-metrics)
- [Privacy by Design Principles](https://www.ipc.on.ca/wp-content/uploads/Resources/7foundationalprinciples.pdf)
