# ADR-005: Externalized Prompts Configuration System

**Status**: Approved
**Date**: 2025-11-11
**Deciders**: Engineering Team, Product Team
**Related**: ADR-003 (Observability), TIER_2_FEATURES.md (Section 3)

## Context and Problem Statement

The Live Conversational Threads application relies heavily on LLM prompts for multiple features:
- Initial graph clustering
- Node summary generation
- Contextual relationship extraction
- Simulacra level detection
- Cognitive bias detection
- Implicit frame analysis
- Speaker role classification

**Current State:**
- Prompts are hardcoded in Python backend functions
- No way to A/B test prompt variations
- Prompt changes require code deployment
- No version history or rollback capability
- Difficult to optimize token usage
- No user customization possible

**User Needs:**
1. **Power Users**: Want to customize prompts for domain-specific conversations (e.g., medical, legal, academic)
2. **Researchers**: Need to experiment with prompt engineering without touching code
3. **Cost Optimization**: Need to test cheaper prompts to reduce API costs
4. **Quality Improvement**: Iterative refinement based on user feedback

**Key Pain Points:**
- Developer bottleneck for prompt changes
- No systematic way to track prompt performance
- Risk of breaking changes when modifying prompts
- Lost context on why specific prompts work

## Decision Drivers

1. **Developer Velocity**: Non-engineers should be able to iterate on prompts
2. **Experimentation**: A/B testing and staged rollouts for prompt changes
3. **Versioning**: Full history of prompt changes with rollback capability
4. **Observability**: Track performance metrics per prompt version
5. **User Control**: Power users can customize for their use cases
6. **Safety**: Validation and testing before deploying prompt changes
7. **Cost Efficiency**: Easy to test token-optimized variations

## Proposed Solution: JSON-Based Prompts Configuration

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Settings UI  │  │ Prompt Editor│  │ Version History  │ │
│  └───────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
└──────────┼──────────────────┼──────────────────┼───────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Prompts Service                                      │  │
│  │  - Load prompts.json                                  │  │
│  │  - Render templates with variables                    │  │
│  │  - Track usage metrics                                │  │
│  │  - Version management                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  prompts.json    │
                    │  (File Storage)  │
                    └──────────────────┘
```

### Prompts Configuration Schema

**File Location**: `lct_python_backend/config/prompts.json`

**Schema Structure**:
```json
{
  "version": "1.0.0",
  "last_updated": "2025-11-11T10:30:00Z",
  "schema_version": 1,

  "global_defaults": {
    "model": "gpt-4",
    "temperature": 0.5,
    "max_tokens": 2000,
    "timeout_seconds": 30
  },

  "prompts": {
    "initial_clustering": {
      "id": "initial_clustering_v1",
      "version": "1.0",
      "description": "Generate initial topic-based nodes from parsed transcript",
      "enabled": true,

      "template": "You are analyzing a conversation transcript to identify natural topic shifts and create meaningful conversation nodes.\n\n# Instructions\n1. Identify distinct topics discussed in the conversation\n2. Group utterances by topic coherence\n3. Create 5-15 nodes representing major topics\n4. Ensure temporal order is preserved\n\n# Transcript\n{utterances}\n\n# Output Format\nReturn JSON array of nodes:\n[\n  {\n    \"node_name\": \"Topic name (3-5 words)\",\n    \"summary\": \"2-3 sentence summary\",\n    \"utterance_ids\": [\"uuid1\", \"uuid2\"],\n    \"zoom_level_visible\": 3,\n    \"temporal_order\": 1\n  }\n]\n\n# Constraints\n- Each node must have 2-10 utterances\n- Avoid orphaned single-utterance nodes\n- Preserve speaker attribution\n- Nodes should be semantically coherent",

      "model": "gpt-4",
      "temperature": 0.5,
      "max_tokens": 2000,

      "variables": {
        "utterances": {
          "type": "string",
          "description": "Formatted transcript text with speaker attributions",
          "required": true
        }
      },

      "few_shot_examples": [
        {
          "input": "Speaker A ~: We need to improve performance.\nSpeaker B ~: Let's profile the database queries first.\nSpeaker A ~: Good idea. I'll set up monitoring.\nSpeaker C ~: What about caching?\nSpeaker B ~: That comes after we identify the bottleneck.",
          "output": [
            {
              "node_name": "Performance Investigation",
              "summary": "Team discusses approach to improving system performance, starting with database profiling and monitoring setup.",
              "utterance_ids": ["1", "2", "3"],
              "zoom_level_visible": 3,
              "temporal_order": 1
            },
            {
              "node_name": "Caching Strategy",
              "summary": "Discussion of caching as optimization, deferred until bottleneck is identified.",
              "utterance_ids": ["4", "5"],
              "zoom_level_visible": 3,
              "temporal_order": 2
            }
          ]
        }
      ],

      "validation": {
        "output_schema": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["node_name", "summary", "utterance_ids"],
            "properties": {
              "node_name": {"type": "string", "minLength": 3, "maxLength": 50},
              "summary": {"type": "string", "minLength": 10, "maxLength": 500},
              "utterance_ids": {"type": "array", "minItems": 2}
            }
          }
        }
      },

      "metrics": {
        "success_rate": 0.92,
        "avg_latency_ms": 4500,
        "avg_cost_usd": 0.48,
        "user_satisfaction": 4.3,
        "last_updated": "2025-11-10"
      }
    },

    "detect_cognitive_bias": {
      "id": "detect_cognitive_bias_v2",
      "version": "2.0",
      "description": "Identify cognitive biases in conversation utterances",
      "enabled": true,

      "template": "Analyze the following conversation segment for cognitive biases and logical fallacies.\n\n# Bias Types to Detect\n{bias_types}\n\n# Conversation Segment\n{context}\n\n# Target Utterances\n{target_utterances}\n\n# Instructions\n1. Identify specific biases or fallacies\n2. Provide confidence score (0.0-1.0)\n3. Explain reasoning with textual evidence\n4. Only flag high-confidence instances (>0.7)\n\n# Output Format\n[\n  {\n    \"bias_type\": \"confirmation_bias\",\n    \"utterance_id\": \"uuid\",\n    \"confidence\": 0.85,\n    \"explanation\": \"Speaker selectively cites evidence...\",\n    \"evidence_quote\": \"Exact text from utterance\"\n  }\n]\n\nIf no biases detected, return empty array [].",

      "model": "gpt-4",
      "temperature": 0.3,
      "max_tokens": 1000,

      "variables": {
        "bias_types": {
          "type": "string",
          "description": "Comma-separated list of bias types to check",
          "default": "confirmation_bias,straw_man,ad_hominem,whataboutism,false_dichotomy"
        },
        "context": {
          "type": "string",
          "description": "Preceding utterances for context",
          "required": true
        },
        "target_utterances": {
          "type": "string",
          "description": "Utterances to analyze",
          "required": true
        }
      },

      "few_shot_examples": [
        {
          "input": {
            "context": "Speaker A ~: Studies show renewable energy reduces emissions.\nSpeaker B ~: Maybe, but what about China's coal plants?",
            "target_utterances": "Speaker B ~: Maybe, but what about China's coal plants?"
          },
          "output": [
            {
              "bias_type": "whataboutism",
              "utterance_id": "uuid-b",
              "confidence": 0.9,
              "explanation": "Speaker deflects from renewable energy benefits by pointing to unrelated issue (China's coal usage) rather than addressing the claim.",
              "evidence_quote": "what about China's coal plants?"
            }
          ]
        }
      ],

      "validation": {
        "output_schema": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["bias_type", "confidence", "explanation"],
            "properties": {
              "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            }
          }
        }
      },

      "metrics": {
        "success_rate": 0.78,
        "avg_latency_ms": 2800,
        "avg_cost_usd": 0.35,
        "false_positive_rate": 0.25,
        "user_satisfaction": 3.9
      }
    },

    "extract_claims": {
      "id": "extract_claims_v1",
      "version": "1.0",
      "description": "Extract factual claims from conversation nodes",
      "enabled": false,  // Disabled for MVP, enable later

      "template": "Extract explicit factual claims from the following conversation segment...",
      "model": "gpt-3.5-turbo",  // Cheaper model
      "temperature": 0.2,
      "max_tokens": 500
    },

    "generate_contextual_edges": {
      "id": "generate_contextual_edges_v1",
      "version": "1.0",
      "description": "Identify contextual relationships between non-sequential nodes",
      "enabled": true,

      "template": "You are identifying thematic relationships between conversation nodes that are not sequentially connected.\n\n# Nodes\n{nodes}\n\n# Instructions\n1. Find nodes that discuss related topics\n2. Ignore temporal neighbors (already connected)\n3. Create edge only if relationship is meaningful\n4. Provide clear explanation for each edge\n\n# Output Format\n[\n  {\n    \"from_node_id\": \"uuid1\",\n    \"to_node_id\": \"uuid2\",\n    \"relationship_type\": \"contextual\",\n    \"label\": \"Both discuss authentication\",\n    \"confidence\": 0.8\n  }\n]",

      "model": "gpt-3.5-turbo",  // Good enough for this task
      "temperature": 0.4,
      "max_tokens": 1500
    },

    "detect_simulacra_level": {
      "id": "detect_simulacra_v1",
      "version": "1.0",
      "description": "Classify utterances by Simulacra level (1-4)",
      "enabled": true,

      "template": "Classify the following utterances according to the Simulacra Levels framework:\n\nLevel 1: Object-level truth (describing reality accurately)\nLevel 2: Manipulation (saying things to cause desired actions)\nLevel 3: Tribal signaling (showing group membership)\nLevel 4: Strategic allegiance (choosing sides for benefit)\n\n# Context\n{context}\n\n# Utterance to Classify\n{utterance}\n\n# Speaker\n{speaker}\n\n# Classification Questions\n1. Is the speaker primarily describing objective reality?\n2. Is the speaker trying to persuade or manipulate?\n3. Is the speaker signaling group membership?\n4. Is the audience more important than the content?\n\n# Output Format\n{\n  \"utterance_id\": \"uuid\",\n  \"simulacra_level\": 2,\n  \"confidence\": 0.75,\n  \"reasoning\": \"Speaker uses persuasive language to advocate for a position rather than neutrally describing facts.\",\n  \"key_indicators\": [\"should\", \"must\", \"emotional appeal\"]\n}",

      "model": "gpt-4",
      "temperature": 0.3,
      "max_tokens": 500,

      "variables": {
        "context": {"type": "string", "required": true},
        "utterance": {"type": "string", "required": true},
        "speaker": {"type": "string", "required": true}
      },

      "metrics": {
        "success_rate": 0.71,
        "avg_latency_ms": 3200,
        "avg_cost_usd": 0.42
      }
    }
  }
}
```

## Implementation Details

### Backend: Prompts Service

**File**: `lct_python_backend/services/prompts_service.py`

```python
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import jinja2
from pydantic import BaseModel, ValidationError

class PromptConfig(BaseModel):
    """Schema for individual prompt configuration"""
    id: str
    version: str
    description: str
    enabled: bool
    template: str
    model: str
    temperature: float
    max_tokens: int
    variables: Dict[str, Any]
    few_shot_examples: List[Dict] = []
    validation: Optional[Dict] = None
    metrics: Optional[Dict] = None

class PromptsService:
    """Service for loading and rendering LLM prompts"""

    def __init__(self, config_path: str = "config/prompts.json"):
        self.config_path = Path(config_path)
        self.prompts_config = self._load_config()
        self.jinja_env = jinja2.Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def _load_config(self) -> Dict:
        """Load prompts configuration from JSON file"""
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Validate schema version
        if config.get('schema_version') != 1:
            raise ValueError("Unsupported prompts schema version")

        return config

    def get_prompt(self, prompt_id: str) -> PromptConfig:
        """Get prompt configuration by ID"""
        if prompt_id not in self.prompts_config['prompts']:
            raise KeyError(f"Prompt '{prompt_id}' not found")

        prompt_data = self.prompts_config['prompts'][prompt_id]

        # Merge with global defaults
        defaults = self.prompts_config['global_defaults']
        prompt_data = {**defaults, **prompt_data}

        # Check if enabled
        if not prompt_data.get('enabled', True):
            raise ValueError(f"Prompt '{prompt_id}' is disabled")

        return PromptConfig(**prompt_data)

    def render_prompt(
        self,
        prompt_id: str,
        variables: Dict[str, Any],
        include_examples: bool = True
    ) -> str:
        """Render prompt template with provided variables"""
        prompt_config = self.get_prompt(prompt_id)

        # Validate required variables
        required_vars = {
            k: v for k, v in prompt_config.variables.items()
            if v.get('required', False)
        }
        missing = set(required_vars.keys()) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        # Apply defaults for optional variables
        for var_name, var_config in prompt_config.variables.items():
            if var_name not in variables and 'default' in var_config:
                variables[var_name] = var_config['default']

        # Render template
        template = self.jinja_env.from_string(prompt_config.template)
        rendered = template.render(**variables)

        # Optionally include few-shot examples
        if include_examples and prompt_config.few_shot_examples:
            examples_text = self._format_examples(prompt_config.few_shot_examples)
            rendered = f"{examples_text}\n\n{rendered}"

        return rendered

    def _format_examples(self, examples: List[Dict]) -> str:
        """Format few-shot examples for inclusion in prompt"""
        formatted = "# Examples\n\n"
        for i, example in enumerate(examples, 1):
            formatted += f"## Example {i}\n"
            formatted += f"Input: {json.dumps(example['input'], indent=2)}\n"
            formatted += f"Output: {json.dumps(example['output'], indent=2)}\n\n"
        return formatted

    def get_model_config(self, prompt_id: str) -> Dict[str, Any]:
        """Get model configuration for a prompt"""
        prompt_config = self.get_prompt(prompt_id)
        return {
            'model': prompt_config.model,
            'temperature': prompt_config.temperature,
            'max_tokens': prompt_config.max_tokens
        }

    def update_prompt_metrics(
        self,
        prompt_id: str,
        metrics: Dict[str, Any]
    ):
        """Update performance metrics for a prompt"""
        if prompt_id in self.prompts_config['prompts']:
            self.prompts_config['prompts'][prompt_id]['metrics'] = {
                **self.prompts_config['prompts'][prompt_id].get('metrics', {}),
                **metrics,
                'last_updated': datetime.now().isoformat()
            }
            self._save_config()

    def _save_config(self):
        """Save prompts configuration back to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.prompts_config, f, indent=2)

# Global instance
prompts_service = PromptsService()
```

### Usage in Backend Endpoints

**Example: Graph Generation**

```python
# lct_python_backend/services/graph_generation_service.py

from services.prompts_service import prompts_service
from instrumentation.decorators import track_api_call
import openai

class GraphGenerationService:

    @track_api_call("initial_clustering")
    async def generate_initial_clusters(
        self,
        conversation_id: str,
        utterances: List[Utterance]
    ) -> List[Node]:
        """Generate initial topic-based nodes from utterances"""

        # Format utterances for prompt
        formatted_utterances = "\n".join([
            f"{utt.speaker} ~: {utt.text}"
            for utt in utterances
        ])

        # Get rendered prompt
        prompt = prompts_service.render_prompt(
            prompt_id="initial_clustering",
            variables={"utterances": formatted_utterances}
        )

        # Get model config
        model_config = prompts_service.get_model_config("initial_clustering")

        # Call LLM
        response = await openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}],
            **model_config
        )

        # Parse and validate response
        nodes_data = json.loads(response.choices[0].message.content)

        # Update prompt metrics
        prompts_service.update_prompt_metrics("initial_clustering", {
            "last_used": datetime.now().isoformat(),
            "token_count": response.usage.total_tokens
        })

        return [Node(**node_data) for node_data in nodes_data]
```

### Frontend: Prompts Editor UI

**Component**: `src/components/Settings/PromptsEditor.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { usePrompts, useUpdatePrompt } from '@/hooks/usePrompts';
import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';

export const PromptsEditor: React.FC = () => {
  const { data: prompts, isLoading } = usePrompts();
  const updatePrompt = useUpdatePrompt();
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [editedTemplate, setEditedTemplate] = useState<string>('');
  const [isDirty, setIsDirty] = useState(false);

  const selectedPrompt = selectedPromptId
    ? prompts?.prompts[selectedPromptId]
    : null;

  useEffect(() => {
    if (selectedPrompt) {
      setEditedTemplate(selectedPrompt.template);
      setIsDirty(false);
    }
  }, [selectedPrompt]);

  const handleSave = async () => {
    if (!selectedPromptId) return;

    await updatePrompt.mutate({
      promptId: selectedPromptId,
      updates: {
        template: editedTemplate,
        version: incrementVersion(selectedPrompt.version)
      }
    });

    setIsDirty(false);
  };

  return (
    <div className="prompts-editor">
      <div className="sidebar">
        <h3>Available Prompts</h3>
        {Object.entries(prompts?.prompts || {}).map(([id, config]) => (
          <div
            key={id}
            className={`prompt-item ${selectedPromptId === id ? 'selected' : ''}`}
            onClick={() => setSelectedPromptId(id)}
          >
            <div className="prompt-name">{id}</div>
            <div className="prompt-meta">
              Version: {config.version} | Model: {config.model}
            </div>
            <div className="prompt-metrics">
              Avg Cost: ${config.metrics?.avg_cost_usd?.toFixed(3)}
            </div>
          </div>
        ))}
      </div>

      <div className="editor-pane">
        {selectedPrompt && (
          <>
            <div className="editor-header">
              <h2>{selectedPromptId}</h2>
              <p>{selectedPrompt.description}</p>
              <div className="actions">
                <button
                  onClick={handleSave}
                  disabled={!isDirty}
                  className="btn-primary"
                >
                  Save Changes
                </button>
                <button onClick={() => setEditedTemplate(selectedPrompt.template)}>
                  Reset
                </button>
              </div>
            </div>

            <CodeMirror
              value={editedTemplate}
              height="600px"
              extensions={[json()]}
              onChange={(value) => {
                setEditedTemplate(value);
                setIsDirty(true);
              }}
            />

            <div className="prompt-details">
              <h4>Configuration</h4>
              <ul>
                <li>Model: {selectedPrompt.model}</li>
                <li>Temperature: {selectedPrompt.temperature}</li>
                <li>Max Tokens: {selectedPrompt.max_tokens}</li>
              </ul>

              <h4>Performance Metrics</h4>
              {selectedPrompt.metrics && (
                <ul>
                  <li>Success Rate: {(selectedPrompt.metrics.success_rate * 100).toFixed(1)}%</li>
                  <li>Avg Latency: {selectedPrompt.metrics.avg_latency_ms}ms</li>
                  <li>Avg Cost: ${selectedPrompt.metrics.avg_cost_usd.toFixed(3)}</li>
                  <li>User Satisfaction: {selectedPrompt.metrics.user_satisfaction}/5.0</li>
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
```

### API Endpoints

**Get All Prompts:**
```
GET /api/prompts/

Response:
{
  "version": "1.0.0",
  "prompts": { ... }
}
```

**Get Single Prompt:**
```
GET /api/prompts/{prompt_id}

Response:
{
  "id": "initial_clustering",
  "template": "...",
  "model": "gpt-4",
  ...
}
```

**Update Prompt:**
```
PATCH /api/prompts/{prompt_id}

Request:
{
  "template": "Updated template text...",
  "version": "1.1"
}

Response:
{
  "success": true,
  "new_version": "1.1"
}
```

**Test Prompt:**
```
POST /api/prompts/{prompt_id}/test

Request:
{
  "variables": {
    "utterances": "Test input..."
  }
}

Response:
{
  "rendered_prompt": "Full rendered prompt...",
  "estimated_tokens": 1500,
  "estimated_cost_usd": 0.045
}
```

## Versioning Strategy

### Semantic Versioning for Prompts

**Format**: `{major}.{minor}.{patch}`

- **Major**: Breaking changes to output schema
- **Minor**: Significant prompt logic changes
- **Patch**: Typo fixes, minor wording improvements

### Version History Table

**Database**: `prompt_versions`

```sql
CREATE TABLE prompt_versions (
  id UUID PRIMARY KEY,
  prompt_id VARCHAR(100),
  version VARCHAR(20),
  template TEXT,
  config JSONB,
  created_at TIMESTAMP,
  created_by VARCHAR(100),
  metrics JSONB,
  is_active BOOLEAN DEFAULT FALSE
);
```

### Rollback Mechanism

```python
def rollback_prompt(prompt_id: str, target_version: str):
    """Rollback prompt to previous version"""
    # Get version from history
    version_data = db.query(
        PromptVersion
    ).filter_by(
        prompt_id=prompt_id,
        version=target_version
    ).first()

    if not version_data:
        raise ValueError(f"Version {target_version} not found")

    # Update active prompt
    prompts_service.prompts_config['prompts'][prompt_id] = version_data.config
    prompts_service._save_config()

    # Log rollback
    logger.info(f"Rolled back {prompt_id} to version {target_version}")
```

## A/B Testing Framework

### Feature Flags for Prompts

```json
{
  "prompts": {
    "initial_clustering": {
      "ab_test": {
        "enabled": true,
        "variant_a": {
          "template": "Original template...",
          "weight": 0.5
        },
        "variant_b": {
          "template": "Experimental template...",
          "weight": 0.5
        },
        "metrics_to_track": [
          "success_rate",
          "user_satisfaction",
          "cost_usd"
        ]
      }
    }
  }
}
```

### A/B Test Service

```python
def select_prompt_variant(prompt_id: str, user_id: str) -> str:
    """Select A/B test variant for user"""
    prompt_config = prompts_service.get_prompt(prompt_id)

    if not prompt_config.get('ab_test', {}).get('enabled'):
        return prompt_config['template']

    # Deterministic assignment based on user_id hash
    hash_value = int(hashlib.md5(f"{user_id}{prompt_id}".encode()).hexdigest(), 16)
    variant_choice = hash_value % 100

    # Select variant based on weights
    weights = prompt_config['ab_test']
    if variant_choice < weights['variant_a']['weight'] * 100:
        return weights['variant_a']['template']
    else:
        return weights['variant_b']['template']
```

## Safety & Validation

### Prompt Validation Rules

1. **Schema Validation**: Output must match defined JSON schema
2. **Token Limit**: Rendered prompt must not exceed model's context window
3. **Variable Validation**: All required variables must be present
4. **Syntax Check**: Template must be valid Jinja2 syntax
5. **Cost Estimation**: Warn if estimated cost exceeds threshold

### Pre-Deployment Checklist

```python
def validate_prompt_update(prompt_id: str, new_template: str) -> ValidationResult:
    """Validate prompt changes before deployment"""
    results = ValidationResult()

    # 1. Syntax check
    try:
        jinja2.Environment().from_string(new_template)
        results.add_pass("Syntax valid")
    except jinja2.TemplateError as e:
        results.add_fail(f"Syntax error: {e}")

    # 2. Render test with sample data
    try:
        rendered = prompts_service.render_prompt(
            prompt_id,
            variables=get_sample_variables(prompt_id)
        )
        results.add_pass("Rendering successful")
    except Exception as e:
        results.add_fail(f"Rendering failed: {e}")

    # 3. Token count check
    token_count = count_tokens(rendered)
    if token_count > 8000:  # GPT-4 limit
        results.add_warning(f"High token count: {token_count}")

    # 4. Cost estimation
    estimated_cost = calculate_cost("gpt-4", token_count, max_tokens=2000)
    if estimated_cost > 1.0:
        results.add_warning(f"High cost estimate: ${estimated_cost:.2f}")

    # 5. Test against validation dataset
    if has_validation_dataset(prompt_id):
        accuracy = test_on_validation_set(prompt_id, new_template)
        if accuracy < 0.7:
            results.add_fail(f"Low accuracy on validation set: {accuracy:.2f}")
        else:
            results.add_pass(f"Validation accuracy: {accuracy:.2f}")

    return results
```

## Performance Considerations

### Hot-Reloading

```python
# Watch prompts.json for changes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PromptsFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('prompts.json'):
            logger.info("Prompts config changed, reloading...")
            prompts_service._load_config()

observer = Observer()
observer.schedule(PromptsFileHandler(), path='config/', recursive=False)
observer.start()
```

### Caching Rendered Prompts

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_prompt(
    prompt_id: str,
    variables_hash: str  # Hash of variables dict
) -> str:
    """Cache rendered prompts to avoid repeated rendering"""
    variables = deserialize_variables(variables_hash)
    return prompts_service.render_prompt(prompt_id, variables)
```

## Migration Plan

### Week 9 Implementation Timeline

**Days 1-2: Backend Service**
- Create `PromptsService` class
- Implement JSON loading and template rendering
- Add validation logic
- Write unit tests

**Days 3-4: API Endpoints**
- Build CRUD endpoints for prompts
- Add version history tracking
- Implement rollback functionality
- Add A/B testing support

**Day 5: Frontend UI**
- Create prompts editor component
- Build version history viewer
- Add test/preview functionality
- Integrate with settings page

### Backward Compatibility

```python
# Decorator to support both hardcoded and config-based prompts
def use_prompt(prompt_id: str, fallback_template: str):
    """Use external prompt if available, fallback to hardcoded"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Try external config
                prompt = prompts_service.get_prompt(prompt_id)
                kwargs['prompt_template'] = prompt.template
            except (KeyError, ValueError):
                # Fallback to hardcoded
                logger.warning(f"Using hardcoded prompt for {prompt_id}")
                kwargs['prompt_template'] = fallback_template

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

## Success Metrics

**Adoption:**
- 60% of power users customize at least one prompt
- 20% of users test prompt variations

**Performance:**
- Prompt updates deployed within 5 minutes (hot-reload)
- Zero downtime during prompt changes
- A/B test results visible within 24 hours

**Quality:**
- 10% reduction in average LLM cost through optimized prompts
- 15% improvement in user satisfaction scores
- 50% reduction in prompt-related bug reports

**Developer Experience:**
- Prompt iteration time reduced from 1 day to 30 minutes
- Non-engineers can modify prompts independently

## Alternatives Considered

### Alternative A: Database-Stored Prompts
- **Pro**: Easier versioning with database migrations
- **Con**: Requires database for local development, harder to version control

### Alternative B: Python Files with String Templates
- **Pro**: Type-safe, IDE support
- **Con**: Still requires code deployment, no user customization

### Alternative C: CMS/Admin Panel
- **Pro**: Rich editing experience
- **Con**: Over-engineered for MVP, steep learning curve

## Future Enhancements

1. **Visual Prompt Builder**: Drag-and-drop prompt construction
2. **Prompt Marketplace**: Share/import community prompts
3. **Auto-Optimization**: ML-based prompt improvement suggestions
4. **Multi-Language Support**: i18n for prompts
5. **Prompt Chaining**: Compose complex pipelines from simple prompts

## References

- [OpenAI Best Practices for Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [JSON Schema Specification](https://json-schema.org/)

---

**Decision Status**: Approved for implementation in Week 9 of roadmap.
