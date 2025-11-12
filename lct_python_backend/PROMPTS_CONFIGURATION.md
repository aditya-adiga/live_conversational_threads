# Prompts Configuration System (Week 9)

## Overview

The **Prompts Configuration System** externalizes all LLM prompts into an editable JSON configuration file (`prompts.json`), enabling easy customization of AI behavior without code changes. This system includes versioning, validation, hot-reloading, and a web UI for managing prompts.

### Key Features

1. **Externalized Configuration**: All prompts stored in `prompts.json`
2. **Template Rendering**: Variable substitution using `$variable` syntax
3. **Version History**: Automatic versioning with rollback support
4. **Hot-Reload**: Changes take effect immediately without restart
5. **Validation**: Schema validation before saving
6. **Web UI**: Settings page for visual editing
7. **Model Configuration**: Specify model, temperature, max_tokens per prompt

---

## Architecture

### Backend Components

```
lct_python_backend/
├── prompts.json                    # Main configuration file
├── prompts_history/                # Version history directory
│   └── {prompt_name}_{timestamp}.json
├── services/
│   ├── prompt_manager.py           # Core prompt management service
│   └── graph_generation.py         # Uses PromptManager
└── backend.py                      # API endpoints for prompts
```

###Frontend Components

```
lct_app/src/
├── services/
│   └── promptsApi.js               # API client for prompts
├── pages/
│   └── Settings.jsx                # Settings UI with prompt editor
└── routes/
    └── AppRoutes.jsx               # Route: /settings
```

---

## prompts.json Structure

### File Format

```json
{
  "version": "1.0.0",
  "last_updated": "2025-11-11",
  "description": "Prompts for Live Conversational Threads AI analysis",

  "prompts": {
    "prompt_name": {
      "description": "What this prompt does",
      "model": "gpt-4",
      "temperature": 0.5,
      "max_tokens": 4000,
      "template": "Prompt text with $variables...",
      "output_format": "json_array",
      "constraints": {},
      "few_shot_examples": []
    }
  },

  "model_pricing": {
    "gpt-4": {
      "input_per_1k": 0.03,
      "output_per_1k": 0.06
    }
  },

  "defaults": {
    "default_model": "gpt-4",
    "default_temperature": 0.5,
    "default_max_tokens": 2000
  }
}
```

### Prompt Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | ✅ | Human-readable description of the prompt |
| `model` | string | ❌ | LLM model to use (defaults to global default) |
| `temperature` | float | ❌ | Temperature 0.0-2.0 (defaults to 0.5) |
| `max_tokens` | int | ❌ | Maximum tokens in response |
| `template` | string | ✅ | Prompt text with variable placeholders |
| `output_format` | string | ❌ | Expected output format: `json`, `json_array`, `json_object`, `plain_text` |
| `constraints` | object | ❌ | Additional constraints (prompt-specific) |
| `few_shot_examples` | array | ❌ | Example inputs/outputs for few-shot learning |

---

## Template Variable Substitution

### Syntax

Use `$variable` or `${variable}` in templates:

```
template: "Given a conversation with $utterance_count utterances from $participant_count participants..."
```

### Rendering

```python
# Backend
pm = get_prompt_manager()
rendered = pm.render_prompt("initial_clustering", {
    "utterance_count": 50,
    "participant_count": 3,
    "participants": "Alice, Bob, Carol",
    "transcript": "..."
})
```

### Available Variables by Prompt

#### initial_clustering
- `utterance_count`: Number of utterances
- `participant_count`: Number of participants
- `participants`: Comma-separated list of participant names
- `transcript`: Full transcript text

#### detect_contextual_relationships
- `nodes_json`: JSON representation of nodes

#### refine_node_summary
- `utterances_text`: Text of utterances in node

#### extract_keywords
- `text`: Text to extract keywords from

#### identify_speakers_in_segment
- `utterances_text`: Conversation segment text

#### suggest_zoom_levels
- `utterance_count`: Number of utterances in node
- `importance`: Importance score
- `granularity`: Granularity level

---

## PromptManager Service

### Initialization

```python
from services.prompt_manager import get_prompt_manager

# Get singleton instance
pm = get_prompt_manager()
```

### Methods

#### Load and Render

```python
# Get complete config
config = pm.get_prompts_config()

# Get specific prompt
prompt = pm.get_prompt("initial_clustering")

# Render template
rendered = pm.render_prompt("initial_clustering", {
    "utterance_count": 50,
    "participant_count": 3,
    "participants": "Alice, Bob, Carol",
    "transcript": "..."
})

# Get metadata only (without template)
metadata = pm.get_prompt_metadata("initial_clustering")
# Returns: {description, model, temperature, max_tokens, ...}
```

#### Save and Version

```python
# Save prompt (automatically versions)
result = pm.save_prompt(
    "initial_clustering",
    {
        "description": "...",
        "template": "...",
        "model": "gpt-4",
        "temperature": 0.5
    },
    user_id="john",
    comment="Updated clustering logic"
)

# Get version history
history = pm.get_prompt_history("initial_clustering", limit=10)

# Restore previous version
pm.restore_version(
    "initial_clustering",
    "2025-11-12T10-30-45-123456",  # timestamp from history
    user_id="john"
)
```

#### Validate

```python
# Validate before saving
validation = pm.validate_prompt({
    "description": "Test prompt",
    "template": "This is a test",
    "model": "gpt-4",
    "temperature": 0.5
})

if not validation["valid"]:
    print("Errors:", validation["errors"])
```

#### Hot-Reload

```python
# Force reload from file
pm.reload()

# Automatic reload
# PromptManager checks file mtime on every get_prompt() call
# and reloads if file has changed
```

---

## API Endpoints

### List Prompts

```http
GET /api/prompts
```

**Response:**
```json
{
  "prompts": ["initial_clustering", "detect_contextual_relationships", ...],
  "count": 6
}
```

---

### Get Prompts Config

```http
GET /api/prompts/config
```

**Response:** Complete `prompts.json` content

---

### Get Specific Prompt

```http
GET /api/prompts/{prompt_name}
```

**Response:**
```json
{
  "description": "Generate initial topic-based nodes from transcript",
  "model": "gpt-4",
  "temperature": 0.5,
  "max_tokens": 4000,
  "template": "You are analyzing a conversation...",
  "few_shot_examples": [...]
}
```

---

### Get Prompt Metadata

```http
GET /api/prompts/{prompt_name}/metadata
```

**Response:** Metadata without template (lighter payload)

```json
{
  "description": "...",
  "model": "gpt-4",
  "temperature": 0.5,
  "max_tokens": 4000,
  "output_format": "json_array",
  "constraints": {},
  "few_shot_examples": []
}
```

---

### Update Prompt

```http
PUT /api/prompts/{prompt_name}
Content-Type: application/json

{
  "prompt_config": {
    "description": "...",
    "template": "...",
    "model": "gpt-4",
    "temperature": 0.7
  },
  "user_id": "john",
  "comment": "Increased temperature for more creative responses"
}
```

**Response:**
```json
{
  "success": true,
  "prompt_name": "initial_clustering",
  "version_saved": true,
  "timestamp": "2025-11-12T10:30:45.123456"
}
```

---

### Delete Prompt

```http
DELETE /api/prompts/{prompt_name}?user_id=john&comment=Removing unused prompt
```

**Response:**
```json
{
  "success": true,
  "prompt_name": "old_prompt",
  "deleted": true,
  "timestamp": "2025-11-12T10:30:45.123456"
}
```

---

### Get Version History

```http
GET /api/prompts/{prompt_name}/history?limit=10
```

**Response:**
```json
{
  "prompt_name": "initial_clustering",
  "history": [
    {
      "prompt_name": "initial_clustering",
      "timestamp": "2025-11-12T10-30-45-123456",
      "user_id": "john",
      "comment": "Updated clustering logic",
      "change_type": "update",
      "prompt_config": {...},
      "config_hash": "a1b2c3d4e5f6g7h8"
    }
  ],
  "count": 1
}
```

---

### Restore Version

```http
POST /api/prompts/{prompt_name}/restore
Content-Type: application/json

{
  "version_timestamp": "2025-11-12T10-30-45-123456",
  "user_id": "john"
}
```

**Response:**
```json
{
  "success": true,
  "prompt_name": "initial_clustering",
  "version_saved": true,
  "timestamp": "2025-11-12T11:00:00.000000"
}
```

---

### Validate Prompt

```http
POST /api/prompts/{prompt_name}/validate
Content-Type: application/json

{
  "description": "Test prompt",
  "template": "This is a test",
  "model": "unknown-model"
}
```

**Response:**
```json
{
  "valid": false,
  "errors": [
    "Unknown model: unknown-model. Valid: ['gpt-4', 'gpt-3.5-turbo', 'claude-sonnet-4']"
  ]
}
```

---

### Reload Prompts

```http
POST /api/prompts/reload
```

**Response:**
```json
{
  "success": true,
  "message": "Prompts reloaded successfully",
  "timestamp": "2025-11-12T11:00:00.000000"
}
```

---

## Settings UI

### Access

Navigate to `/settings` in the frontend application.

### Features

**1. Prompt List** (Left Sidebar)
- Lists all available prompts
- Click to select and view

**2. Prompt Editor** (Main Panel)
- **View Mode** (default):
  - Read-only display of prompt configuration
  - Shows description, model, temperature, max_tokens
  - Displays template with syntax highlighting
  - "Edit Prompt" and "View History" buttons

- **Edit Mode** (after clicking "Edit Prompt"):
  - Editable fields for all configuration
  - Model dropdown (gpt-4, gpt-3.5-turbo, claude-sonnet-4)
  - Temperature slider/input (0.0-2.0)
  - Max tokens input
  - Template textarea
  - Description input
  - Save comment field (optional)
  - "Cancel" and "Save Changes" buttons
  - Real-time validation with error display

**3. Version History Modal**
- Lists all previous versions
- Shows timestamp, user, change type, comment
- Expandable config view
- "Restore" button for each version

**4. Toolbar**
- "Reload from File" button (hot-reload)

### User Workflow

1. **View Prompts**: Select from list to see current configuration
2. **Edit Prompt**:
   - Click "Edit Prompt"
   - Modify fields as needed
   - Add comment describing changes
   - Click "Save Changes"
   - Validation runs automatically
   - If valid, saves with versioning
3. **View History**:
   - Click "View History"
   - Browse previous versions
   - Click "Restore" to revert to old version
4. **Hot-Reload**: Click "Reload from File" to pick up external changes

---

## Versioning System

### How It Works

1. **Automatic Versioning**: Every save creates a version backup
2. **History Storage**: Versions saved in `prompts_history/` directory
3. **File Naming**: `{prompt_name}_{timestamp}.json`
4. **Metadata**: Each version includes user_id, comment, change_type, hash

### Version Record Structure

```json
{
  "prompt_name": "initial_clustering",
  "timestamp": "2025-11-12T10-30-45-123456",
  "user_id": "john",
  "comment": "Updated clustering logic",
  "change_type": "update",  // "create", "update", "delete", "pre_restore"
  "prompt_config": {
    "description": "...",
    "template": "...",
    "model": "gpt-4",
    "temperature": 0.5
  },
  "config_hash": "a1b2c3d4e5f6g7h8"
}
```

### Change Types

| Type | Description |
|------|-------------|
| `create` | New prompt created |
| `update` | Existing prompt modified |
| `delete` | Prompt deleted (backup before deletion) |
| `pre_restore` | Backup before restoring old version |

### Restoration Flow

1. User clicks "Restore" on version from history
2. System saves current version as "pre_restore" backup
3. System loads old version config
4. System saves old config as new version with comment "Restored from {timestamp}"
5. prompts.json updated
6. UI refreshes

---

## Integration with Graph Generation

### Before Week 9

```python
# Old approach - hardcoded prompts
class GraphGenerationService:
    def _generate_nodes(self, transcript):
        prompt = f"Generate nodes from: {transcript}"
        # Call LLM with hardcoded prompt
```

### After Week 9

```python
# New approach - externalized prompts
from .prompt_manager import get_prompt_manager

class GraphGenerationService:
    def __init__(self):
        self.prompt_manager = get_prompt_manager()

    def _generate_nodes(self, transcript):
        # Render prompt from template
        prompt_text = self.prompt_manager.render_prompt(
            "initial_clustering",
            {
                "utterance_count": len(transcript.utterances),
                "participants": ", ".join(transcript.participants),
                "transcript": format_transcript(transcript)
            }
        )

        # Get model configuration
        metadata = self.prompt_manager.get_prompt_metadata("initial_clustering")

        # Call LLM with configured parameters
        response = llm.call(
            prompt=prompt_text,
            model=metadata["model"],
            temperature=metadata["temperature"],
            max_tokens=metadata["max_tokens"]
        )
```

### Benefits

1. **No Code Changes**: Update prompts without deploying code
2. **A/B Testing**: Easy to test prompt variations
3. **Version Control**: Track prompt evolution over time
4. **Rollback**: Quickly revert bad prompts
5. **Customization**: Users can tune prompts for their use case

---

## Best Practices

### Prompt Writing

1. **Clear Instructions**: Be explicit about task and format
2. **Examples**: Include few-shot examples when possible
3. **Variable Names**: Use descriptive variable names (`$utterance_count` not `$n`)
4. **Output Format**: Specify exact JSON structure expected
5. **Constraints**: State any limits or requirements

### Configuration

1. **Temperature**:
   - 0.0-0.3: Deterministic, factual tasks
   - 0.4-0.7: Balanced creativity and consistency
   - 0.8-1.0: Creative, varied outputs
   - 1.1-2.0: Highly creative (rarely needed)

2. **Max Tokens**:
   - Short summaries: 500-1000
   - Node generation: 2000-4000
   - Complex analysis: 4000-8000

3. **Model Selection**:
   - `gpt-4`: Best quality, highest cost, slower
   - `gpt-3.5-turbo`: Fast, cheap, good for simple tasks
   - `claude-sonnet-4`: High quality, good for analysis

### Versioning

1. **Meaningful Comments**: Describe why you made the change
2. **Test Before Deploying**: Validate on test data first
3. **Incremental Changes**: Make small changes, test, iterate
4. **Backup Important Versions**: Note timestamps of known-good versions

---

## Troubleshooting

### Issue: Prompt not loading

**Symptoms:**
- Error: "Prompt 'xyz' not found in prompts.json"

**Cause:**
- Prompt name misspelled
- prompts.json not in correct location
- JSON syntax error in file

**Solution:**
1. Check prompt name spelling
2. Verify `prompts.json` exists in `lct_python_backend/`
3. Validate JSON syntax: `python -m json.tool prompts.json`
4. Check server logs for file loading errors

---

### Issue: Variables not substituting

**Symptoms:**
- Rendered prompt contains `$variable` literally

**Cause:**
- Variable name mismatch
- Missing variable in render call

**Solution:**
```python
# Check variable names in template match render call
template: "Count: $utterance_count"  # Must use this exact name

# Render with matching variable
pm.render_prompt("prompt_name", {
    "utterance_count": 50  # Must match template
})
```

---

### Issue: Version history not showing

**Symptoms:**
- History modal is empty
- 404 error on history endpoint

**Cause:**
- `prompts_history/` directory doesn't exist
- No changes made yet (no versions saved)

**Solution:**
1. Make a change to trigger versioning
2. Check `prompts_history/` directory exists
3. Verify write permissions on directory

---

### Issue: Hot-reload not working

**Symptoms:**
- Changes to prompts.json not reflected
- Must restart server to see changes

**Cause:**
- File mtime check not working
- File system caching

**Solution:**
1. Click "Reload from File" button in UI
2. Call `POST /api/prompts/reload` endpoint
3. Restart backend server

---

## Performance Considerations

### Caching

- **Current**: PromptManager caches prompts in memory
- **Reload**: Checks file mtime on every `get_prompt()` call
- **Overhead**: Minimal (1 stat() syscall)

### Optimization Strategies

1. **Disable Hot-Reload in Production**:
   ```python
   # Modified PromptManager for production
   def _check_reload(self):
       # Skip mtime check in production
       if os.getenv("ENVIRONMENT") == "production":
           return
       # ... existing check
   ```

2. **Periodic Reload**:
   ```python
   # Instead of checking every call, reload every N minutes
   if time.time() - self.last_reload > 300:  # 5 minutes
       self.reload()
   ```

3. **Event-Based Reload**:
   ```python
   # Use file watcher (watchdog library)
   from watchdog.observers import Observer
   # Reload only when file actually changes
   ```

---

## Security Considerations

### Input Validation

1. **Template Injection**: Use `string.Template` (safe) not `str.format()` (unsafe)
2. **Model Validation**: Only allow whitelisted models
3. **Temperature Bounds**: Enforce 0.0-2.0 range
4. **Token Limits**: Prevent excessive token usage

### Access Control

Current implementation has **no authentication**. For production:

1. **Add User Authentication**:
   ```python
   @lct_app.put("/api/prompts/{prompt_name}")
   async def update_prompt(
       prompt_name: str,
       request: PromptConfigUpdate,
       user: User = Depends(get_current_user)  # Add auth
   ):
       # Verify user has permission to edit prompts
       if not user.can_edit_prompts:
           raise HTTPException(403, "Forbidden")
       # ... rest of logic
   ```

2. **Role-Based Permissions**:
   - Admin: Create, edit, delete prompts
   - Power User: Edit existing prompts
   - Regular User: View only

3. **Audit Logging**:
   - Log all prompt changes to database
   - Track who changed what and when

---

## Future Enhancements

### Phase 1
- [ ] Prompt templates marketplace (share with community)
- [ ] Diff viewer for version comparison
- [ ] Prompt testing sandbox (test before saving)
- [ ] Import/export prompt sets

### Phase 2
- [ ] A/B testing framework (compare prompt versions)
- [ ] Automatic prompt optimization (tune parameters)
- [ ] Cost estimation (show cost per prompt execution)
- [ ] Prompt analytics (track performance, token usage)

### Phase 3
- [ ] Multi-language support (translate prompts)
- [ ] Conditional prompts (different prompts for different conditions)
- [ ] Prompt composition (combine multiple prompts)
- [ ] LLM-powered prompt generation (meta-prompting)

---

## Related Documentation

- [GRAPH_GENERATION.md](./GRAPH_GENERATION.md) - How prompts are used in graph generation
- [INSTRUMENTATION.md](./INSTRUMENTATION.md) - API call tracking and cost monitoring
- [ROADMAP.md](../docs/ROADMAP.md) - Overall project roadmap

---

## Summary

Week 9 introduces a comprehensive prompts configuration system that:

1. **Externalizes all LLM prompts** into editable JSON
2. **Enables customization** without code changes
3. **Tracks versions** with full history and rollback
4. **Provides web UI** for easy management
5. **Supports hot-reload** for immediate changes
6. **Validates configurations** before saving

**Key Benefits:**
- Rapid prompt iteration and tuning
- A/B testing of prompts
- User customization for specific domains
- Version control and audit trail
- No code deployments needed for prompt changes

This completes Week 9 of the Live Conversational Threads V2 roadmap.
