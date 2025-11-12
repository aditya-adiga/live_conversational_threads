# Perplexity API Integration for Fact-Checking

**Week 21**: Add real-time fact verification for factual claims

---

## Integration Architecture

### 1. Fact-Checking Service

```python
# lct_python_backend/services/fact_checker.py

import os
import requests
from typing import Dict, Any, List

class PerplexityFactChecker:
    """
    Wrapper around Perplexity API for fact-checking claims.
    Uses the fact_checker.py code provided by user.
    """

    API_URL = "https://api.perplexity.ai/chat/completions"
    DEFAULT_MODEL = "sonar-pro"

    def __init__(self):
        self.api_key = os.getenv("PPLX_API_KEY")
        if not self.api_key:
            raise ValueError("PPLX_API_KEY not found in environment")

        self.system_prompt = """You are a professional fact-checker with extensive research capabilities.
Your task is to evaluate claims for factual accuracy.
Focus on identifying false, misleading, or unsubstantiated claims.

Return results in this format:
{
    "rating": "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIABLE",
    "explanation": "Detailed explanation with evidence",
    "sources": ["URL1", "URL2", ...],
    "confidence": 0.0-1.0
}
"""

    async def check_claim(
        self,
        claim_text: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Fact-check a single claim using Perplexity.

        Args:
            claim_text: The claim to verify
            context: Optional context from conversation

        Returns:
            {
                "rating": "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIABLE",
                "explanation": str,
                "sources": List[str],
                "confidence": float,
                "citations": List[str]
            }
        """
        user_prompt = f"Fact check the following claim:\n\n{claim_text}"
        if context:
            user_prompt += f"\n\nContext from conversation:\n{context}"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            response = requests.post(self.API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            citations = result.get("citations", [])

            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"]

                # Parse response
                try:
                    import json
                    parsed = json.loads(content)
                    if "citations" not in parsed:
                        parsed["citations"] = citations
                    return parsed
                except json.JSONDecodeError:
                    # Fallback: return raw response
                    return {
                        "rating": "UNVERIFIABLE",
                        "explanation": content,
                        "sources": [],
                        "citations": citations,
                        "confidence": 0.5
                    }

            return {
                "rating": "UNVERIFIABLE",
                "explanation": "Unexpected API response",
                "sources": [],
                "citations": citations,
                "confidence": 0.0
            }

        except Exception as e:
            return {
                "rating": "UNVERIFIABLE",
                "explanation": f"Error during fact-checking: {str(e)}",
                "sources": [],
                "citations": [],
                "confidence": 0.0
            }

    async def batch_check_claims(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fact-check multiple claims in batch.

        Args:
            claims: List of claim dicts with 'id', 'claim_text', 'context'

        Returns:
            List of results with claim IDs
        """
        results = []

        for claim in claims:
            result = await self.check_claim(
                claim["claim_text"],
                claim.get("context", "")
            )

            result["claim_id"] = claim["id"]
            results.append(result)

            # Rate limiting: 1 request per second
            await asyncio.sleep(1)

        return results
```

### 2. Update Claim Model

```python
# Add fact-check fields to claims table
ALTER TABLE claims ADD COLUMN IF NOT EXISTS fact_check_result JSONB;
ALTER TABLE claims ADD COLUMN IF NOT EXISTS fact_checked_at TIMESTAMP;
ALTER TABLE claims ADD COLUMN IF NOT EXISTS verification_status TEXT
    CHECK (verification_status IN ('verified', 'false', 'misleading', 'unverifiable', 'pending'));
```

### 3. API Endpoints

```python
# lct_python_backend/backend.py

@lct_app.post("/api/claims/{claim_id}/fact-check")
async def fact_check_claim(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Fact-check a single claim using Perplexity.
    """
    # Get claim
    query = select(Claim).where(Claim.id == uuid.UUID(claim_id))
    result = await db.execute(query)
    claim = result.scalar_one_or_none()

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.claim_type != 'factual':
        raise HTTPException(
            status_code=400,
            detail="Can only fact-check factual claims"
        )

    # Get context (surrounding utterances)
    context = await get_claim_context(db, claim)

    # Fact-check
    fact_checker = PerplexityFactChecker()
    result = await fact_checker.check_claim(claim.claim_text, context)

    # Update database
    claim.fact_check_result = result
    claim.fact_checked_at = datetime.now()
    claim.verification_status = result["rating"].lower()

    await db.commit()

    return {
        "claim_id": claim_id,
        "claim_text": claim.claim_text,
        "fact_check": result
    }


@lct_app.post("/api/conversations/{conversation_id}/fact-check-all")
async def fact_check_all_claims(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Fact-check all factual claims in a conversation.
    """
    # Get all factual claims
    query = select(Claim).where(
        Claim.conversation_id == uuid.UUID(conversation_id),
        Claim.claim_type == 'factual',
        Claim.is_verifiable == True
    )
    result = await db.execute(query)
    claims = result.scalars().all()

    # Prepare batch
    claims_batch = []
    for claim in claims:
        context = await get_claim_context(db, claim)
        claims_batch.append({
            "id": str(claim.id),
            "claim_text": claim.claim_text,
            "context": context
        })

    # Batch fact-check
    fact_checker = PerplexityFactChecker()
    results = await fact_checker.batch_check_claims(claims_batch)

    # Update database
    for result in results:
        claim_id = uuid.UUID(result["claim_id"])
        claim = next(c for c in claims if c.id == claim_id)

        claim.fact_check_result = result
        claim.fact_checked_at = datetime.now()
        claim.verification_status = result["rating"].lower()

    await db.commit()

    return {
        "conversation_id": conversation_id,
        "total_claims": len(claims),
        "results": results
    }


async def get_claim_context(db: AsyncSession, claim: Claim) -> str:
    """
    Get surrounding utterances for context.
    """
    # Get node containing this claim
    node = await db.get(Node, claim.node_id)

    if not node:
        return ""

    # Get utterances
    query = select(Utterance).where(
        Utterance.id.in_(node.utterance_ids)
    ).order_by(Utterance.sequence_number)

    result = await db.execute(query)
    utterances = result.scalars().all()

    # Format context
    context_lines = []
    for utt in utterances:
        context_lines.append(f"{utt.speaker_name}: {utt.text}")

    return "\n".join(context_lines)
```

### 4. Frontend UI

```jsx
// lct_app/src/pages/ClaimAnalysis.jsx

function FactualClaimCard({ claim }) {
  const [factCheck, setFactCheck] = useState(claim.fact_check_result);
  const [loading, setLoading] = useState(false);

  const handleFactCheck = async () => {
    setLoading(true);
    try {
      const result = await factCheckClaim(claim.id);
      setFactCheck(result.fact_check);
    } catch (error) {
      console.error('Fact-check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const ratingColors = {
    'verified': 'bg-green-100 text-green-800 border-green-500',
    'false': 'bg-red-100 text-red-800 border-red-500',
    'misleading': 'bg-yellow-100 text-yellow-800 border-yellow-500',
    'unverifiable': 'bg-gray-100 text-gray-800 border-gray-500',
  };

  return (
    <div className="border-l-4 p-4 rounded border-blue-500 bg-blue-50">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📊</span>
            <span className="font-semibold text-gray-700">FACTUAL</span>
            {claim.is_verifiable && (
              <span className="text-sm text-blue-600">✓ Verifiable</span>
            )}
          </div>

          <p className="text-lg mb-2">{claim.claim_text}</p>

          {/* Fact-Check Result */}
          {factCheck && (
            <div className={`mt-3 p-3 rounded border-2 ${ratingColors[factCheck.rating.toLowerCase()]}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold uppercase">{factCheck.rating}</span>
                <span className="text-sm">
                  Confidence: {(factCheck.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <p className="text-sm mb-2">{factCheck.explanation}</p>

              {factCheck.citations && factCheck.citations.length > 0 && (
                <div className="mt-2">
                  <div className="text-xs font-semibold mb-1">Sources:</div>
                  <ul className="text-xs space-y-1">
                    {factCheck.citations.map((citation, idx) => (
                      <li key={idx}>
                        <a
                          href={citation}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline"
                        >
                          {citation}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Fact-Check Button */}
          {claim.is_verifiable && !factCheck && (
            <button
              onClick={handleFactCheck}
              disabled={loading}
              className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'Fact-checking...' : 'Fact-Check This Claim'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## Cost Estimation

**Perplexity Pricing** (Sonar Pro):
- ~$0.001 - $0.005 per fact-check (depending on complexity)

**Per Conversation** (assuming 20 factual claims):
- 20 claims × $0.003 average = **$0.06**

**Very affordable** compared to other LLM calls!

---

## Usage Workflow

1. **Passive**: After conversation import, factual claims are detected
2. **User browses**: Claims page shows all factual claims with "Fact-Check" button
3. **On-demand**: User clicks to verify specific claims
4. **Batch option**: "Fact-check all claims" button for entire conversation
5. **Results cached**: Future views show cached fact-check results

---

## Integration Timeline

- **Week 21**: Implement Perplexity integration
- **Week 22**: Add batch fact-checking
- **Week 23**: Track fact-check history over time
- **Week 24**: Cross-conversation fact patterns

Ready to proceed with the full 20-week roadmap?
