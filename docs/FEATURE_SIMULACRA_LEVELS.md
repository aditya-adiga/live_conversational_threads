# Feature Specification: Simulacra Level Detection & Cognitive Bias Analysis

**Status**: Design Phase - Awaiting Implementation
**Date**: 2025-11-11
**Priority**: Tier 2 - Advanced Analysis
**Dependencies**: Tier 1 (Node detail panel, fallacy detection framework)

---

## Overview

This feature detects **Simulacra levels** (implicit frames and hidden intentions) and **cognitive biases** in conversation transcripts. It helps users understand not just *what* people are saying, but *why* they're saying it and what rhetorical strategies they're employing.

**Key capabilities**:
1. Classify utterances by Simulacra level (1-4)
2. Detect 25+ cognitive biases and logical fallacies
3. Visualize implicit frames and normative claims
4. Track rhetorical patterns per speaker

---

## Part 1: Simulacra Level Detection

### Framework Summary (Zvi Mowshowitz / Baudrillard)

```
Level 1: OBJECT-LEVEL TRUTH
├─ Attempting to describe reality accurately
├─ Sharing information because it's true
└─ Test: Would change if contrary evidence presented

Level 2: MANIPULATION / DECEPTION
├─ Saying things to cause desired actions/beliefs in others
├─ Words as tools to control listener behavior
└─ Test: Would change if audience started responding oppositely

Level 3: TRIBAL SIGNALING
├─ Saying things to signal group membership/identity
├─ Words convey political/social affiliation
└─ Test: Would change if your ingroup started saying opposite

Level 4: STRATEGIC ALLEGIANCE
├─ Choosing which group to signal based on personal benefit
├─ Symbol detached from reality, optimizing for advantage
└─ Test: Would change if you'd benefit more from opposite
```

### Detection Heuristics

**Question set for classification**:

1. **"Does sender identity matter?"**
   - No → Likely Level 1 or 2
   - Yes → Likely Level 3 or 4

2. **"Does audience identity matter?"**
   - No → Likely Level 1
   - Yes → Likely Level 2, 3, or 4

3. **"Is this claim verifiable against external reality?"**
   - Yes + attempting verification → Level 1
   - Yes but not attempting → Level 2 (lying/misleading)
   - No (normative/aesthetic) → Level 3 or 4

4. **"What would cause speaker to say the opposite?"**
   - New evidence → Level 1
   - Audience responds differently → Level 2
   - Ingroup changes position → Level 3
   - Personal benefit shifts → Level 4

### Backend Implementation

```python
@app.post("/api/analyze/simulacra-levels/{node_id}")
async def analyze_simulacra_levels(node_id: str):
    """
    Classify each utterance in a node by Simulacra level
    """
    node = await db.get_node(node_id)
    utterances = await db.get_utterances(node.utterance_ids)
    context = await get_conversation_context(node.conversation_id)

    prompt = load_prompt("detect_simulacra_levels")

    # Include conversation context for better inference
    response = await call_llm(prompt, {
        "utterances": [
            {
                "speaker": u.speaker_name,
                "text": u.text,
                "timestamp": u.start_time
            }
            for u in utterances
        ],
        "context": {
            "previous_statements": context.previous,
            "speaker_history": context.speaker_patterns,
            "topic": node.summary
        }
    })

    # Store analysis
    await db.cache_analysis(node_id, "simulacra_levels", response.classifications)

    return {
        "node_id": node_id,
        "classifications": response.classifications,
        "confidence": response.confidence
    }
```

### Prompt Engineering (prompts.json)

```json
{
  "detect_simulacra_levels": {
    "description": "Classify utterances by Simulacra level (1-4)",
    "template": "
Analyze these conversation utterances and classify each by Simulacra level:

**Simulacra Levels:**
- **Level 1 (Object-level)**: Attempting to describe reality accurately. Sharing info because it's true.
- **Level 2 (Manipulation)**: Saying things to cause desired actions/beliefs in others. Words as tools.
- **Level 3 (Signaling)**: Saying things to signal group membership. Tribal identity.
- **Level 4 (Strategic)**: Choosing which group to signal based on personal benefit.

**Detection questions:**
1. Does sender identity matter? (Yes → Level 3+)
2. Does audience matter? (Yes → Level 2+)
3. Is this verifiable? (No → Level 3+)
4. What would make them say opposite?
   - Evidence → Level 1
   - Audience response → Level 2
   - Ingroup shift → Level 3
   - Personal benefit → Level 4

**Utterances:**
{utterances}

**Context:**
- Previous discussion: {context.previous_statements}
- Speaker patterns: {context.speaker_history}
- Topic: {context.topic}

For each utterance, return JSON:
{
  \"utterance_id\": \"...\",
  \"speaker\": \"...\",
  \"text\": \"...\",
  \"simulacra_level\": 1|2|3|4,
  \"confidence\": 0.0-1.0,
  \"reasoning\": \"Why this level? What cues?\",
  \"flags\": [\"verifiable_claim\", \"tribal_language\", \"persuasive_intent\", etc.]
}
",
    "model": "gpt-4",
    "temperature": 0.2,
    "max_tokens": 1500,
    "few_shot_examples": [
      {
        "input": "The ASF camp deadline is in 10 days",
        "output": {
          "simulacra_level": 1,
          "reasoning": "Factual claim about external reality, verifiable, no apparent manipulation or signaling"
        }
      },
      {
        "input": "I think we should invite all the guests because it'll make us look more legitimate",
        "output": {
          "simulacra_level": 2,
          "reasoning": "Strategic reasoning about how action will affect others' perceptions. Goal is to manipulate perception, not describe truth."
        }
      },
      {
        "input": "As someone committed to EA principles, I believe we should...",
        "output": {
          "simulacra_level": 3,
          "reasoning": "Explicitly signals tribal affiliation (EA community) before making claim. Identity/membership matters."
        }
      },
      {
        "input": "I support [position] because that's what aligns with my career goals right now",
        "output": {
          "simulacra_level": 4,
          "reasoning": "Explicitly optimizing for personal benefit, choosing allegiance strategically"
        }
      }
    ]
  }
}
```

### Frontend Visualization

#### Node Detail Panel Section (Collapsible)

```
┌─────────────────────────────────────────┐
│ 🎭 Simulacra Analysis ▼                 │
├─────────────────────────────────────────┤
│                                         │
│ Speaker: Aditya                         │
│ ─────────────────────────────────────  │
│ [Lvl 1] "SK comes on 6th and leaves    │
│          by 12th"                       │
│ ✓ Factual claim, verifiable            │
│                                         │
│ Speaker: Sahil                          │
│ ─────────────────────────────────────  │
│ [Lvl 3] "As someone committed to EA     │
│          principles, I believe..."      │
│ ⚠️  Tribal signaling (EA affiliation)   │
│ [Expand reasoning] [Dismiss]            │
│                                         │
│ Speaker: Harshit                        │
│ ─────────────────────────────────────  │
│ [Lvl 2] "We should frame it this way    │
│          so people understand better"   │
│ ⚠️  Persuasive intent, audience-aware   │
│ [Expand reasoning] [Dismiss]            │
│                                         │
├─────────────────────────────────────────┤
│ Level Distribution:                     │
│ Level 1: ████████░░  42%                │
│ Level 2: ████░░░░░░  18%                │
│ Level 3: ██████░░░░  28%                │
│ Level 4: ██░░░░░░░░  12%                │
└─────────────────────────────────────────┘
```

**Color coding** (subtle, not overwhelming):
- **Level 1**: Default black text
- **Level 2**: Light orange highlight
- **Level 3**: Light blue highlight
- **Level 4**: Light red highlight

#### Graph View (Nodes colored by dominant level)

```
If a node contains mostly Level 1 utterances → default color
If node contains mostly Level 3 utterances → slight blue tint
If node contains Level 4 utterances → red flag icon
```

**Hover tooltip**:
```
┌────────────────────────┐
│ Node 7                 │
│ Simulacra Mix:         │
│ ● 60% Level 1          │
│ ● 20% Level 2          │
│ ● 20% Level 3          │
└────────────────────────┘
```

---

## Part 2: Cognitive Bias & Fallacy Detection

### Categories (25 Types from User Context)

**Systematic Biases** (built into human reasoning):
1. Affect heuristic (halo/horns effect)
2. Optimism bias
3. Confirmation bias
4. Fundamental attribution error
5. Anchoring
6. Scope insensitivity
7. Hindsight bias
8. Availability heuristic
9. Bystander apathy
10. Typical mind fallacy
11. Sunken cost fallacy
12. Just-world fallacy
13. Reification (map-territory confusion)

**Logical Fallacies** (argumentation errors):
14. No true Scotsman
15. Naturalistic fallacy
16. Whataboutism
17. Straw man (+ steelmanning counterpart)
18. Ad hominem
19. Law of the instrument
20. False dichotomy
21. Moving the goalposts
22. False premise
23. False equivalence
24. Appeal to false authority
25. Appeal to common sense

### Detection Strategy

**Two-stage analysis**:

1. **Pattern matching** (fast, rule-based):
   - Detect obvious patterns: "No true X would do Y" → No true Scotsman
   - Keyword flags: "natural", "common sense", "what about" → Trigger LLM analysis

2. **LLM analysis** (slower, semantic):
   - Contextual understanding
   - Detect subtle instances (straw man requires understanding the opponent's actual position)
   - Confidence scoring

### Backend API

```python
@app.post("/api/analyze/cognitive-biases/{node_id}")
async def analyze_cognitive_biases(node_id: str):
    """
    Detect cognitive biases and logical fallacies in node utterances
    """
    node = await db.get_node(node_id)
    utterances = await db.get_utterances(node.utterance_ids)

    # Stage 1: Pattern matching (fast)
    quick_flags = pattern_match_fallacies(utterances)

    # Stage 2: LLM analysis (contextual)
    prompt = load_prompt("detect_biases_fallacies")

    response = await call_llm(prompt, {
        "utterances": [u.text for u in utterances],
        "speakers": [u.speaker_name for u in utterances],
        "context": await get_node_context(node_id),
        "quick_flags": quick_flags  # Prime the LLM
    })

    # Merge results
    all_detections = merge_detections(quick_flags, response.detections)

    await db.cache_analysis(node_id, "biases_fallacies", all_detections)

    return {
        "node_id": node_id,
        "detections": all_detections,
        "severity_counts": {
            "high": len([d for d in all_detections if d.severity == "high"]),
            "medium": len([d for d in all_detections if d.severity == "medium"]),
            "low": len([d for d in all_detections if d.severity == "low"])
        }
    }
```

### Prompt Engineering

```json
{
  "detect_biases_fallacies": {
    "description": "Detect cognitive biases and logical fallacies with context",
    "template": "
Analyze this conversation segment for cognitive biases and logical fallacies.

**Categories to check:**

**Logical Fallacies:**
- No true Scotsman: \"They're not REAL [group members]\"
- Naturalistic fallacy: \"It's natural, therefore it's good/moral\"
- Whataboutism: Deflecting criticism by pointing to other issues
- Straw man: Misrepresenting opponent's argument to make it easier to attack
- Ad hominem: Attacking the person instead of the argument
- False dichotomy: Presenting only 2 options when more exist
- Moving goalposts: Changing criteria after objection is met
- False premise: Question assumes something controversial as true
- False equivalence: Comparing things that aren't actually comparable
- Appeal to false authority: Citing irrelevant expert or celebrity
- Appeal to common sense: \"It's obvious\" without justification

**Cognitive Biases:**
- Affect heuristic / Halo effect: One positive trait → assume all positive
- Optimism bias: Underestimating risks, overestimating success
- Confirmation bias: Only seeking evidence that supports existing belief
- Fundamental attribution error: Explaining by traits vs circumstances
- Anchoring: First number mentioned skews judgment
- Typical mind fallacy: Assuming others think like you
- Sunken cost fallacy: Continuing because already invested
- Just-world fallacy: Believing victims deserve their suffering
- Reification: Treating abstract concepts as concrete reality

**Utterances:**
{utterances}

**Speakers:**
{speakers}

**Context:**
{context}

**Quick flags** (from pattern matching):
{quick_flags}

For each detected bias/fallacy, return JSON:
{
  \"type\": \"straw_man\" | \"confirmation_bias\" | etc.,
  \"utterance_text\": \"...\",
  \"speaker\": \"...\",
  \"line_number\": 5,
  \"severity\": \"low\" | \"medium\" | \"high\",
  \"confidence\": 0.0-1.0,
  \"explanation\": \"Why this is [bias/fallacy]. What cues? How it manifests?\",
  \"impact\": \"How this affects the argument quality?\",
  \"counter\": \"How to address this constructively?\"
}

Only flag instances with confidence > 0.6. Avoid false positives.
",
    "model": "gpt-4",
    "temperature": 0.2,
    "max_tokens": 2000
  }
}
```

### Pattern Matching (Fast Pre-Filter)

```python
def pattern_match_fallacies(utterances: List[Utterance]) -> List[Dict]:
    """
    Quick regex-based detection for obvious patterns
    """
    flags = []

    for i, utt in enumerate(utterances):
        text = utt.text.lower()

        # No true Scotsman
        if re.search(r"no (true|real|actual)\s+\w+\s+would", text):
            flags.append({
                "type": "no_true_scotsman",
                "line": i,
                "text": utt.text,
                "confidence": 0.8,
                "method": "pattern_match"
            })

        # Naturalistic fallacy
        if re.search(r"\b(natural|unnatural)\b", text) and re.search(r"\b(should|moral|right|wrong)\b", text):
            flags.append({
                "type": "naturalistic_fallacy_candidate",
                "line": i,
                "text": utt.text,
                "confidence": 0.6,
                "method": "pattern_match"
            })

        # Whataboutism
        if re.search(r"\bwhat about\b", text):
            flags.append({
                "type": "whataboutism_candidate",
                "line": i,
                "text": utt.text,
                "confidence": 0.7,
                "method": "pattern_match"
            })

        # Appeal to common sense
        if re.search(r"\b(obviously|common sense|everyone knows|it's clear)\b", text):
            flags.append({
                "type": "appeal_to_common_sense",
                "line": i,
                "text": utt.text,
                "confidence": 0.5,
                "method": "pattern_match"
            })

        # Straw man indicators (needs LLM to confirm)
        if re.search(r"so (you're saying|you think|you believe)", text):
            flags.append({
                "type": "strawman_candidate",
                "line": i,
                "text": utt.text,
                "confidence": 0.4,
                "method": "pattern_match"
            })

    return flags
```

### Frontend Visualization

#### Node Detail Panel Section

```
┌─────────────────────────────────────────┐
│ ⚠️  Biases & Fallacies (3) ▼            │
├─────────────────────────────────────────┤
│                                         │
│ 🔴 Straw man fallacy                    │
│    Speaker: Harshit                     │
│    Line 3: "So you're saying we should  │
│            just give up?"               │
│    ─────────────────────────────────   │
│    Explanation: Misrepresents Aditya's  │
│    argument. Aditya suggested pausing,  │
│    not abandoning the project.          │
│    ─────────────────────────────────   │
│    Counter: "That's not what I said.    │
│    I suggested we pause to reassess."   │
│    ─────────────────────────────────   │
│    [✗ Not a fallacy] [✓ Confirm]        │
│    [📝 Add note]                        │
│                                         │
│ 🟡 Optimism bias                        │
│    Speaker: Sahil                       │
│    Line 5: "I'm sure we can get this    │
│            done in 2 weeks"             │
│    ─────────────────────────────────   │
│    Explanation: Underestimating timeline│
│    complexity. Historical data shows    │
│    similar tasks took 4-6 weeks.        │
│    ─────────────────────────────────   │
│    Impact: May lead to over-commitment  │
│    and rushed work.                     │
│    ─────────────────────────────────   │
│    [✗ Dismiss] [📊 Show data]           │
│                                         │
│ 🟢 Whataboutism                         │
│    Speaker: Aditya                      │
│    Line 8: "What about the budget       │
│            issues though?"              │
│    ─────────────────────────────────   │
│    Explanation: Deflecting from current │
│    topic (guest invites) to different   │
│    issue (budget).                      │
│    ─────────────────────────────────   │
│    Counter: "Let's table budget for now│
│    and finish this discussion first."   │
│    ─────────────────────────────────   │
│    [✗ Dismiss] [✓ Confirm]              │
└─────────────────────────────────────────┘
```

**Severity color coding**:
- 🔴 **High**: Significantly undermines argument quality
- 🟡 **Medium**: Weakens reasoning but not fatal
- 🟢 **Low**: Minor issue, worth noting

---

## Part 3: Implicit Frames & Normative Claims

### What Are "Implicit Frames"?

From user context:
> "If I say 'we should preserve the light of consciousness' or 'suffering should be reduced', I'm sneaking in some more subtle insidious normative claim."

**Goal**: Detect hidden value judgments masquerading as facts or neutral statements.

### Examples of Implicit Frames

1. **"Preserve the light of consciousness"**
   - **Hidden frame**: Consciousness is valuable, worth preserving
   - **Worldview**: Probably influenced by longtermism, cosmic perspective
   - **Alternative frame**: Consciousness might not be inherently good

2. **"Suffering should be reduced"**
   - **Hidden frame**: Suffering is bad, reduction is good
   - **Worldview**: Utilitarian ethics, preference for hedonic outcomes
   - **Alternative frame**: Some suffering may be necessary for growth

3. **"We need to move fast and break things"**
   - **Hidden frame**: Speed > caution, disruption > stability
   - **Worldview**: Tech accelerationist, startup culture
   - **Alternative frame**: Careful planning prevents costly mistakes

4. **"That's just how the market works"**
   - **Hidden frame**: Market outcomes are natural/inevitable/justified
   - **Worldview**: Capitalist realism, economic determinism
   - **Alternative frame**: Markets are social constructs we can change

### Detection Strategy

**LLM prompt chain**:

1. **Extract normative claims** (should, ought, must, need to)
2. **Identify hidden premises** (what values/beliefs must be true for this claim to make sense?)
3. **Name the frame** (which worldview/ideology does this align with?)
4. **Generate alternatives** (what would someone with a different worldview say?)

### Backend API

```python
@app.post("/api/analyze/implicit-frames/{node_id}")
async def analyze_implicit_frames(node_id: str):
    """
    Detect implicit frames and hidden value judgments
    """
    node = await db.get_node(node_id)
    utterances = await db.get_utterances(node.utterance_ids)

    # Step 1: Extract normative claims
    normative_claims = await extract_normative_claims(utterances)

    # Step 2: Analyze implicit frames
    prompt = load_prompt("detect_implicit_frames")

    response = await call_llm(prompt, {
        "utterances": [u.text for u in utterances],
        "normative_claims": normative_claims,
        "context": await get_node_context(node_id)
    })

    await db.cache_analysis(node_id, "implicit_frames", response.frames)

    return {
        "node_id": node_id,
        "normative_claims": normative_claims,
        "implicit_frames": response.frames
    }

async def extract_normative_claims(utterances: List[Utterance]) -> List[Dict]:
    """
    Quick extraction of should/ought/must statements
    """
    normative_keywords = ["should", "ought", "must", "need to", "have to", "wrong to", "right to"]

    claims = []
    for utt in utterances:
        for keyword in normative_keywords:
            if keyword in utt.text.lower():
                claims.append({
                    "text": utt.text,
                    "speaker": utt.speaker_name,
                    "keyword": keyword
                })
                break  # One claim per utterance

    return claims
```

### Prompt Engineering

```json
{
  "detect_implicit_frames": {
    "description": "Detect implicit frames and hidden value judgments in normative claims",
    "template": "
Analyze these normative claims for implicit frames and hidden values.

**Task**: Identify what worldview, ideology, or value system is being **assumed** (not explicitly stated).

**Examples of implicit frames:**
- \"Preserve the light of consciousness\" → assumes consciousness is valuable
- \"Suffering should be reduced\" → utilitarian ethics, hedonic focus
- \"Move fast and break things\" → tech accelerationist, disruption > stability
- \"That's how the market works\" → capitalist realism, economic determinism

**Utterances:**
{utterances}

**Normative claims identified:**
{normative_claims}

**Context:**
{context}

For each normative claim, return JSON:
{
  \"claim_text\": \"...\",
  \"speaker\": \"...\",
  \"implicit_frame\": {
    \"name\": \"Longtermism\" | \"Utilitarianism\" | \"Accelerationism\" | \"Conservatism\" | etc.,
    \"hidden_premise\": \"What value/belief is assumed?\",
    \"worldview_indicators\": [\"Keywords/phrases that signal this worldview\"],
    \"confidence\": 0.0-1.0
  },
  \"alternative_frames\": [
    {
      \"name\": \"Alternative worldview name\",
      \"how_they_would_say_it\": \"What would someone with this view say instead?\"
    }
  ]
}

Only flag claims with clear implicit frames (confidence > 0.6).
",
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 1500
  }
}
```

### Frontend Visualization

```
┌─────────────────────────────────────────┐
│ 🎯 Implicit Frames (2) ▼                │
├─────────────────────────────────────────┤
│                                         │
│ Claim: "We should preserve the light    │
│        of consciousness"                │
│ Speaker: Sahil                          │
│ ─────────────────────────────────────  │
│ 🔍 Implicit Frame: Longtermism          │
│    Hidden premise: Consciousness is     │
│    inherently valuable and worth        │
│    preserving at cosmic scales.         │
│    ─────────────────────────────────   │
│    Worldview indicators:                │
│    • "light of consciousness" (cosmic)  │
│    • "preserve" (future-oriented)       │
│    ─────────────────────────────────   │
│    Alternative frames:                  │
│    • Nihilism: "Consciousness may not   │
│      have inherent value"               │
│    • Buddhism: "Consciousness is        │
│      inherently suffering"              │
│    ─────────────────────────────────   │
│    [✗ Not implicit] [📝 Add note]       │
│                                         │
│ Claim: "Suffering should be reduced"    │
│ Speaker: Harshit                        │
│ ─────────────────────────────────────  │
│ 🔍 Implicit Frame: Utilitarianism       │
│    Hidden premise: Hedonic outcomes are │
│    the measure of moral worth.          │
│    ─────────────────────────────────   │
│    Alternative frames:                  │
│    • Stoicism: "Suffering is part of    │
│      growth, not inherently bad"        │
│    • Virtue ethics: "Character matters  │
│      more than suffering"               │
│    ─────────────────────────────────   │
│    [✗ Dismiss] [✓ Confirm]              │
└─────────────────────────────────────────┘
```

---

## Part 4: Speaker Rhetorical Patterns

### Analytics View - Rhetorical Profile

```
📈 Analytics > Speaker: Aditya

┌─────────────────────────────────────────┐
│ Rhetorical Pattern Analysis             │
├─────────────────────────────────────────┤
│                                         │
│ Simulacra Level Distribution:           │
│ ├─ Level 1 (Object-level): 62%          │
│ ├─ Level 2 (Persuasion):   18%          │
│ ├─ Level 3 (Signaling):    15%          │
│ └─ Level 4 (Strategic):     5%          │
│                                         │
│ Most Common Biases/Fallacies:           │
│ 1. Optimism bias (4 instances)          │
│ 2. Confirmation bias (2 instances)      │
│ 3. Appeal to common sense (2 instances) │
│                                         │
│ Implicit Frames Detected:               │
│ • Longtermism (3 mentions)              │
│ • Rationalist epistemology (2 mentions) │
│ • Effective Altruism (1 mention)        │
│                                         │
│ Rhetorical Style:                       │
│ • Primarily fact-based (Level 1)        │
│ • Occasionally signals tribal affil.    │
│ • Moderate use of persuasive language   │
│                                         │
│ Steelmanning Score: 7/10                │
│ (How often does speaker charitably      │
│  interpret opponents' arguments?)       │
└─────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Simulacra Level Detection (Week 11)
- [ ] Implement detection prompt
- [ ] Backend API for classification
- [ ] Frontend visualization in node detail panel
- [ ] User feedback mechanism (dismiss/confirm)

### Phase 2: Cognitive Bias Detection (Week 12)
- [ ] Pattern matching for 25 bias types
- [ ] LLM contextual analysis
- [ ] Integration with existing fallacy detection
- [ ] Severity scoring and color coding

### Phase 3: Implicit Frames (Week 13)
- [ ] Normative claim extraction
- [ ] Frame detection prompt
- [ ] Alternative frame generation
- [ ] Worldview taxonomy

### Phase 4: Speaker Rhetorical Profiles (Week 14)
- [ ] Aggregate analysis per speaker
- [ ] Rhetorical pattern dashboard
- [ ] Steelmanning score calculation
- [ ] Export rhetorical profiles

---

## User Feedback & Training Data

### Correction Workflow

```python
@app.post("/api/feedback/simulacra-level")
async def feedback_simulacra_level(
    utterance_id: str,
    ai_classification: int,
    user_classification: int,
    user_note: Optional[str] = None
):
    """
    User corrects AI's Simulacra level classification
    """
    await db.log_edit({
        "edit_type": "simulacra_level_correction",
        "utterance_id": utterance_id,
        "before": {"level": ai_classification},
        "after": {"level": user_classification},
        "user_note": user_note,
        "timestamp": datetime.now()
    })

    # Update confidence for similar patterns
    await update_classification_confidence(utterance_id, user_classification)
```

### Training Data Schema

```json
{
  "conversation_id": "conv_123",
  "node_id": "node_45",
  "utterance_id": "utt_789",
  "feature": "simulacra_level",
  "ai_output": {
    "level": 3,
    "confidence": 0.75,
    "reasoning": "Speaker signals EA affiliation"
  },
  "user_correction": {
    "level": 1,
    "note": "This is actually just a factual statement about what EA principles suggest, not tribal signaling"
  },
  "context": {
    "previous_utterances": [...],
    "speaker_history": {...}
  }
}
```

---

## Settings & Power User Controls

### Feature Toggles

```
⚙️  Settings > Advanced Analysis

┌──────────────────────────────────────────┐
│ 🎭 Simulacra Level Detection             │
│    [✓] Enable                            │
│    └─ [✓] Show in node detail panel      │
│    └─ [ ] Color-code nodes by level      │
│    └─ Confidence threshold: [0.7]        │
│                                          │
│ ⚠️  Cognitive Bias Detection             │
│    [✓] Enable                            │
│    └─ [✓] Pattern matching (fast)        │
│    └─ [✓] LLM analysis (contextual)      │
│    └─ [✓] Show severity indicators       │
│    └─ Minimum severity: [Medium ▼]       │
│                                          │
│ 🎯 Implicit Frame Detection              │
│    [ ] Enable (Experimental)             │
│    └─ [ ] Detect normative claims        │
│    └─ [ ] Identify worldviews            │
│    └─ [ ] Generate alternative frames    │
│                                          │
│ 📊 Speaker Rhetorical Profiles           │
│    [✓] Enable                            │
│    └─ [✓] Aggregate bias patterns        │
│    └─ [✓] Calculate steelmanning score   │
│    └─ [ ] Compare speakers               │
└──────────────────────────────────────────┘
```

---

## Success Metrics

1. **Detection Accuracy**: User corrections < 15% of AI classifications
2. **False Positive Rate**: Users dismiss < 20% of flagged biases
3. **Engagement**: Users expand "Reasoning" section > 40% of the time
4. **Training Data**: Collect 500+ corrections in first month
5. **User Satisfaction**: "This helped me understand hidden motivations" > 70% agree

---

## Future Enhancements

### Advanced Features
- **Argumentative move classification** (claim, evidence, warrant, backing)
- **Crux detection** (what beliefs, if changed, would resolve disagreement?)
- **Dialectical synthesis** (AI proposes synthesis of opposing views)
- **Historical comparison** (how have speaker's frames shifted over time?)

### Integration with Other Features
- **Fact-checking** integration (Level 1 claims should be verifiable)
- **Goal tracking** (detect when conversation drifts due to Level 3 signaling)
- **Thread detection** (Level 2/3 utterances often derail threads)

---

**Status**: Ready for review and prioritization
**Next Steps**:
1. Review detection heuristics
2. Test prompts on sample transcripts
3. Prioritize: Simulacra vs Biases vs Frames?
