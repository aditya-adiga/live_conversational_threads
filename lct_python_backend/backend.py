import anthropic
import os
import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from websockets.exceptions import ConnectionClosedError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, HttpUrl
import time
from typing import Dict, Generator, List, Any, Optional
import uuid
import random
import requests
import asyncio
import websockets
from google import genai
from google.genai import types
from pathlib import Path
from google.cloud import storage
from datetime import datetime
# from db import db
# from db_helpers import get_all_conversations, insert_conversation_metadata, get_conversation_gcs_path
# from lct_python_backend.db import db
# from lct_python_backend.db_helpers import get_all_conversations, insert_conversation_metadata, get_conversation_gcs_path
from firestore_db import get_all_conversations, insert_conversation_metadata, get_conversation_gcs_path
# from lct_python_backend.firestore_db import get_all_conversations, insert_conversation_metadata, get_conversation_gcs_path
# from contextlib import asynccontextmanager
# from dotenv import load_dotenv

# load_dotenv() 

# GLOBAL VARIABLES
BATCH_SIZE = 4
MAX_BATCH_SIZE = 12


# Directory to save JSON files
# SAVE_DIRECTORY = "../saved_json"

# db
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("[INFO] Connecting to database...")
#     try:
#         await db.connect()
#         print("[INFO] Connected to database.")
#     except Exception as e:
#         print("[ERROR] Failed to connect to database during startup:")
#         import traceback
#         traceback.print_exc()
#         raise e  # re-raise so the app still fails, but now you see why
#     yield
#     print("[INFO] Disconnecting from database...")
#     await db.disconnect()
    
# fastapi app
# lct_app = FastAPI(lifespan=lifespan)
lct_app = FastAPI()

# Configure CORS
lct_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from Vite frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Serve JS/CSS/assets from Vite build folder
# lct_app.mount("/assets", StaticFiles(directory="frontend_dist/assets"), name="assets")



# AssemblyAI API Key
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
ASSEMBLYAI_WS_URL = os.getenv("ASSEMBLYAI_WS_URL")

# perplexity api key
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

#anthropic api key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

#google ai api key
GOOGLEAI_API_KEY = os.getenv("GOOGLEAI_API_KEY")

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

GCS_FOLDER = os.getenv("GCS_FOLDER")


PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Pydantic Models
class TranscriptRequest(BaseModel):
    transcript: str

class ChunkedTranscript(BaseModel):
    chunks: Dict[str, str]  # Dictionary where keys are UUIDs and values are text chunks

class ChunkedRequest(BaseModel):
    chunks: Dict[str, str]  # Input to the streaming endpoint

class ProcessedChunk(BaseModel):
    chunk_id: str
    text: str

class SaveJsonRequest(BaseModel):
    file_name: str
    chunks: dict
    graph_data: List
    conversation_id: str

class SaveJsonResponse(BaseModel):
    message: str
    file_id: str  # UUID of the saved file
    file_name: str  # Original file name provided by the user
    
class generateFormalismRequest(BaseModel):
    chunks: dict
    graph_data: List
    user_pref: str

class generateFormalismResponse(BaseModel):
    formalism_data: List
    
class SaveJsonResponseExtended(BaseModel):
    file_id: str
    file_name: str
    message: str
    no_of_nodes: int
    created_at: Optional[str]
    
class ConversationResponse(BaseModel):
    graph_data: List[Any]
    chunk_dict: Dict[str, Any]
    
class Citation(BaseModel):
    title: str
    url: HttpUrl

class AnswerFormat(BaseModel):
    claim: str
    verdict: str  # "True", "False", "Unverified"
    explanation: str
    citations: List[Citation]  # max 2 preferred

class ClaimsResponse(BaseModel):
    claims: List[AnswerFormat]

class FactCheckRequest(BaseModel):
    claims: List[str]
    
class SaveFactCheckRequest(BaseModel):
    conversation_id: str
    node_name: str
    fact_check_data: List[AnswerFormat]
    
class GetFactCheckResponse(BaseModel):
    results: List[AnswerFormat]
    
# Function to chunk the text
def sliding_window_chunking(text: str, chunk_size: int = 10000, overlap: int = 2000) -> Dict[str, str]:
    assert chunk_size > overlap, "chunk_size must be greater than overlap!"

    words = text.split()
    chunks = {}
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_text = " ".join(words[start:end])
        chunks[str(uuid.uuid4())] = chunk_text
        start += chunk_size - overlap

    return chunks

def claude_llm_call(transcript: str, claude_prompt: str, start_text: str, temp: float = 0.6, retries: int = 5, backoff_base: float = 1.5):
    for attempt in range(retries):
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=20000,
                temperature=temp,
                system= claude_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": transcript
                                    }
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": start_text
                            }
                        ]
                    }
                ]
            )
            return message.content[0].text
            
        except json.JSONDecodeError as e:
            print(f"[INFO]: Invalid JSON: {e}")
            return None

        except anthropic.AuthenticationError:
            print("[INFO]: Authentication failed. Check your API key.")
            return None

        except anthropic.RateLimitError:
            print("[INFO]: Rate limit exceeded. Retrying...")  # ✅ Retryable

        except anthropic.APIError as e:
            print(f"[INFO]: API error occurred: {e}")
            if "overloaded" not in str(e).lower():
                return None

        except Exception as e:
            print(f"[INFO]: Unexpected error: {e}")
            return None

        # Exponential backoff before next retry
        sleep_time = backoff_base ** attempt + random.uniform(0, 1)
        time.sleep(sleep_time)

    return None

# Function to generate JSON using Claude
def generate_lct_json_claude(transcript: str, temp: float = 0.6, retries: int = 5, backoff_base: float = 1.5):
    generate_lct_prompt = """You are an advanced AI model that structures conversations into strictly JSON-formatted nodes. Each conversational shift should be captured as a new node with defined relationships, with primary emphasis on capturing rich contextual connections that demonstrate thematic coherence, conceptual evolution, and cross-conversational idea building.
**Formatting Rules:**

**Instructions:**

**Handling New JSON Creation**
Extract Key Nodes: Identify all topic shifts in the conversation. Each topic shift forms a new "node", even if the topic was discussed earlier.

**Strictly Generate JSON Output:**
[
  {
    "node_name": "Title of the conversational thread",
    "type": "conversational_thread" or "bookmark",
    "predecessor": "Previous node name temporally",
    "successor": "Next node name temporally",
    "contextual_relation": {
      "Related Node 1": "Detailed explanation of how this node connects thematically, shows conceptual evolution, and builds upon ideas from the current discussion",
      "Related Node 2": " Another comprehensive explanation that weaves together thematic connections with how concepts have developed",
      "...": "Additional related nodes with their respective explanations can be included as needed"
    },
    "linked_nodes": [
      "List of all nodes this node is either drawing context from or providing context to"
    ],
    "chunk_id": null,  // This field will be **ignored** for now and will be added externally.
    "is_bookmark": true or false,
    ""is_contextual_progress": true or false,
    "summary": "Detailed description of what was discussed in this node."
  }
]
**Enhanced Contextual Relations Approach:**
-	In "contextual_relation", provide integrated explanations that naturally weave together:
-	How nodes connect thematically (shared concepts, related ideas)
-	How concepts have evolved or been refined since previous mentions
-	How ideas build upon each other across different conversation segments
-	 Don't capture direct shifts in conversations as contextual_relation unless there is a relevant contextual relation only then capture it.
Create cohesive narratives that explain the full relationship context rather than treating these as separate analytical dimensions.

**Define Structure:**
"predecessor" → The direct previous node temporally (empty for first node only).
"successor" → The direct next node temporally.
"contextual_relation" → Use this to explain how past nodes contribute to the current discussion contextually.
•	Keys = node names that contribute context.
•	Values = a detailed explanation of how the multiple referenced nodes influence the current discussion.

"linked_nodes" → A comprehensive list of all nodes this node is either drawing context from or providing context to, this information of context providing will come from "contextual_relation", consolidating references into a single field.
"chunk_id" → This field will be ignored for now, as it will be added externally by the code.

**Handling Updates to Existing JSON**
If an existing JSON structure is provided along with the transcript, modify it as follows and strictly return only the nodes generated for the current input transcript:

- **Continuing a topic**: If the conversation continues an existing discussion, update the "successor" field of the last relevant node.
-	**New topic**: If a conversation introduces a new topic, create a new node and properly link it.
-	**Revisiting a Bookmark**: If "LLM wish bookmark open [name]" appears, find the existing bookmark node and update its "contextual_relation" and "linked_nodes". Do NOT create a new bookmark when revisited—update the existing one instead.
-	**Contextual Relation Updates**: Maintain connections that demonstrate how past discussions influence current ones through integrated thematic, evolutionary, and developmental relationships.

**Chronology, Contextual Referencing and Bookmarking**
If a topic is revisited, create a new node while ensuring proper linking to previous mentions through rich contextual relations. Ensure mutual linking between nodes that provide context to each other through comprehensive relationship explanations.

**Each node must include both "predecessor" and "successor" fields to maintain chronological flow, maintaining the flow of the conversation irrespective of how related the topics are and strictly based on temporal relationship. Don't have predecessor empty if it is not the first node ever.**


**Conversational Threads nodes (type: "conversational_thread"):**
- Every topic shift must be captured as a new node.
- "contextual_relation" must provide integrated explanations of how previous discussions contribute to the current conversation through thematic connections, conceptual evolution, and idea building.
- "linked_nodes" must track all nodes this node is either drawing context from or providing context to in a single list.
- For nodes with type="conversational_thread", always set "is_bookmark": false.
 **Handling Revisited Topics**
 If a conversation returns to a previously discussed topic, create a new node and ensure "contextual_relation" provides comprehensive explanations of how past discussions relate to current context.

**Bookmark nodes (type: "bookmark") must:**
- A bookmark node must be created when "LLM wish bookmark create" appears, capturing the contextually relevant topic.
- Do not create bookmark node unless "LLM wish bookmark create" is mentioned.
- "contextual_relation" must reference nodes with integrated explanations of relationships, ensuring contextual continuity.
- The summary should clearly describe the reason for creating the bookmark and what it aims to track.
- If "LLM wish bookmark open" appears, do not create a new bookmark—update the existing one.
- For nodes with type="bookmark", always set "is_bookmark": true.



**Contextual Progress Capture ("is_contextual_progress": true):**
-	Only If "LLM wish capture contextual progress" appears, update the existing node (either "conversational_thread" or "bookmark") to include:
o	"is_contextual_progress": true
-	Contextual progress capture is used to capture a potential insight that might be present in that conversational node. 
-	It represents part of the conversation that could potentially be an insight that could be useful. These "potential insights" are the directions provided by humans that can later be taken by AI, which then uses this to generate formalisms.
-	Do not create a new node for contextual progress capture. Instead, apply the flag to the relevant existing node where the potential insight was introduced or referenced.
-**Contextual Relation & Linked Nodes Updates:**
- "contextual_relation" must provide comprehensive, integrated explanations that demonstrate the full scope of how nodes relate through thematic coherence, conceptual development, and cross-conversational idea building as unified relationship narratives.
- Don't capture direct shifts in conversations as contextual_relation unless there is a relevant contextual relation only then capture it.
- "linked_nodes" must include all references in a single list, capturing all nodes this node draws from or informs.
- The structure of "predecessor", "successor", and "contextual_relation" must ensure logical and chronological consistency between past and present discussions.

**Example Input**
**Existing JSON:**

**Transcript:**
Sam: Hey Taylor, I've got the mock-ups and timeline draft for the budgeting app.
Taylor: Nice! That covers the MVP milestones?
Sam: Yeah—dashboard, sync API, and notification system.
Taylor: Perfect. But we still haven't locked down pricing strategy.
Sam: Right. Ads, subscriptions, or freemium—still up in the air.
Taylor: We can survey beta users next week.
Sam: LLM wish bookmark create Startup Planning.
Taylor: Speaking of habits—have you stuck to your morning workout routine?
Sam: Mostly. I'm trying to anchor it to my coffee—habit stacking like we discussed.
Taylor: That's the best way. Pairing it with your podcast time might help too.
Sam: Good idea. I could listen to product strategy episodes while lifting.
Taylor: LLM wish capture contextual progress Fitness Habit Loop.
Sam: Quick tangent—remember when we talked about launching that writing tool?
Taylor: You mean the AI-assisted outlining app? Yeah. That convo got buried under budgeting app chaos.
Sam: Exactly. I still think it's viable. We had notes on use cases from early users.
Taylor: Let's revive it. Might even share infrastructure with the budgeting app backend.
Sam: LLM wish bookmark create Outlining Tool Revival.
Taylor: Okay, circling back—what's our go-to API for the budgeting app?
Sam: Plaid is expensive but reliable. Yodlee's cheaper, but older.
Taylor: And SaltEdge?
Sam: Less US coverage. I'm leaning Plaid.
Taylor: Cool, let's roll with it for beta. Add it to Startup Planning.
Sam: Done.
Taylor: So how do we test the pricing options?
Sam: I could build an A/B test into onboarding flows.
Taylor: Perfect. One with a free tier, one with premium-only.
Sam: And track conversion vs. churn. I'll prototype it.
Sam: LLM wish capture contextual progress Monetization Strategy.
Taylor: Oh, forgot to tell you—I pulled our old Notion doc on the outlining tool.
Sam: The one from last summer?
Taylor: Yep. User feedback section is gold. Matches what you said last week.
Sam: Let's cross-link that to our new app discussions too—some onboarding overlap.
Taylor: LLM wish bookmark open Outlining Tool Revival.
Sam: By the way, I watched that cyber-noir series finale. Intense!
Taylor: Don't spoil! I'm one episode behind.
Sam: Fine, but the twist connects to what we said about nonlinear story arcs in tools.
Taylor: Good point. Our outlining app should support multi-threaded plotting.
Sam: Anyway, quick check—what are today's key Startup Planning items?
Taylor: 1. Confirm Plaid. 2. Draft onboarding split test. 3. Prep beta survey questions.
Sam: Got it. I'll document and sync.
Taylor: Hey, back to the outlining app—we should prototype a plot tree view.
Sam: Like a drag-and-drop node system?
Taylor: Yes. With contextual linking between subplots. Nonlinear story design baked in.
Sam: Just like we talked about for knowledge graphs in the budgeting app.
Taylor: Exactly.
Sam: LLM wish bookmark open Startup Planning.
Taylor: I'll update with today's changes and next steps: implement API, finalize A/B logic, send beta invites.
Sam: I love how both projects are feeding into each other—makes the architecture stronger.
Taylor: Yeah, and it's helping us think modular.

Example JSON Output:
[
  {
    "node_name": "Budgeting App MVP Planning",
    "type": "conversational_thread",
    "predecessor": null,
    "successor": "Startup Planning Bookmark",
    "contextual_relation": {},
    "linked_nodes": [],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Sam shares mock-ups and timeline for the budgeting app MVP including dashboard, sync API, and notification system. Taylor confirms coverage but notes pricing strategy (ads, subscriptions, or freemium) remains unresolved, planning beta user surveys for next week."
  },
  {
    "node_name": "Startup Planning Bookmark",
    "type": "bookmark",
    "predecessor": "Budgeting App MVP Planning",
    "successor": "Fitness and Product Strategy Integration",
    "contextual_relation": {
      "Budgeting App MVP Planning": "This bookmark captures the comprehensive startup planning elements including MVP milestones, unresolved pricing strategies, and the plan for beta user feedback gathering that will guide monetization decisions."
    },
    "linked_nodes": ["Budgeting App MVP Planning"],
    "chunk_id": null,
    "is_bookmark": true,
    "is_contextual_progress": false,
    "summary": "Sam creates a bookmark to track startup planning encompassing MVP development milestones and pricing strategy decisions for the budgeting app."
  },
  {
    "node_name": "Fitness and Product Strategy Integration",
    "type": "conversational_thread",
    "predecessor": "Startup Planning Bookmark",
    "successor": "Outlining Tool Revival",
    "contextual_relation": {},
    "linked_nodes": [],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": true,
    "summary": "Taylor and Sam discuss morning workout habits using habit stacking (anchoring workouts to coffee time) and suggest combining with product strategy podcast listening. Taylor captures this as contextual progress for Fitness Habit Loop."
  },
  {
    "node_name": "Outlining Tool Revival",
    "type": "conversational_thread",
    "predecessor": "Fitness and Product Strategy Integration",
    "successor": "Outlining Tool Revival Bookmark",
    "contextual_relation": {
      "Budgeting App MVP Planning": "The AI-assisted outlining app project was deprioritized due to budgeting app development but remains viable with existing user feedback. Taylor suggests potential infrastructure sharing between both apps' backends, creating development synergies."
    },
    "linked_nodes": ["Budgeting App MVP Planning"],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Sam recalls their previous AI-assisted outlining app project that got buried under budgeting app work. They still have valuable early user feedback and use cases, and Taylor suggests sharing infrastructure with the budgeting app backend."
  },
  {
    "node_name": "Outlining Tool Revival Bookmark",
    "type": "bookmark",
    "predecessor": "Outlining Tool Revival",
    "successor": "Technical Implementation Decisions",
    "contextual_relation": {
      "Outlining Tool Revival": "This bookmark captures the decision to revive the outlining app project, acknowledging its continued viability despite being overshadowed by budgeting app development, with potential for shared infrastructure benefits."
    },
    "linked_nodes": ["Outlining Tool Revival"],
    "chunk_id": null,
    "is_bookmark": true,
    "is_contextual_progress": false,
    "summary": "Sam creates a bookmark to track the revival of the AI-assisted outlining app project with its existing user feedback and potential infrastructure sharing opportunities."
  },
  {
    "node_name": "Technical Implementation Decisions",
    "type": "conversational_thread",
    "predecessor": "Outlining Tool Revival Bookmark",
    "successor": "Monetization Testing Strategy",
    "contextual_relation": {
      "Budgeting App MVP Planning": "The API selection (choosing Plaid over Yodlee and SaltEdge) directly implements the sync API component of the MVP. This technical decision balances cost versus reliability considerations critical to the startup's success.",
      "Startup Planning Bookmark": "The Plaid API decision represents a concrete technical commitment within the broader startup planning framework, affecting both development timeline and operational costs."
    },
    "linked_nodes": ["Budgeting App MVP Planning", "Startup Planning Bookmark"],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Taylor and Sam evaluate API options for the budgeting app - comparing Plaid (expensive but reliable), Yodlee (cheaper but older), and SaltEdge (limited US coverage). They decide on Plaid for beta and add it to Startup Planning."
  },
  {
    "node_name": "Monetization Testing Strategy",
    "type": "conversational_thread",
    "predecessor": "Technical Implementation Decisions",
    "successor": "Documentation and Story Structure",
    "contextual_relation": {
      "Outlining Tool Revival": "Taylor's discovery of the old Notion documentation validates the outlining tool's potential with concrete user feedback. The onboarding overlap with the budgeting app suggests shared UX patterns that could accelerate both projects.",
      "Outlining Tool Revival Bookmark": "Opening this bookmark to add the documentation findings and cross-linking opportunities strengthens the revival case with historical context and identified synergies."
    },
    "linked_nodes": ["Outlining Tool Revival", "Outlining Tool Revival Bookmark"],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": true,
    "summary": "Sam proposes building A/B tests into onboarding flows to test pricing options (free tier vs premium-only) while tracking conversion and churn metrics. Sam captures this as contextual progress for Monetization Strategy."
  },
  {
    "node_name": "Documentation and Story Structure",
    "type": "conversational_thread",
    "predecessor": "Monetization Testing Strategy",
    "successor": "Action Items and Feature Design",
    "contextual_relation": {
      "Outlining Tool Revival": "Taylor's discovery of the old Notion documentation validates the outlining tool's potential with concrete user feedback. The onboarding overlap with the budgeting app suggests shared UX patterns that could accelerate both projects.",
      "Outlining Tool Revival Bookmark": "Opening this bookmark to add the documentation findings and cross-linking opportunities strengthens the revival case with historical context and identified synergies."
    },
    "linked_nodes": ["Outlining Tool Revival", "Outlining Tool Revival Bookmark"],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Taylor retrieves old Notion documentation on the outlining tool with valuable user feedback, noting onboarding overlap with the budgeting app. They open the Outlining Tool Revival bookmark. Discussion shifts to a cyber-noir series, connecting nonlinear story arcs to the need for multi-threaded plotting support in their tools."
  },
  {
    "node_name": "Action Items and Feature Design",
    "type": "conversational_thread",
    "predecessor": "Documentation and Story Structure",
    "successor": "Project Synergy Reflection",
    "contextual_relation": {
      "Technical Implementation Decisions": "The action items consolidate technical decisions - confirming Plaid API represents commitment to the chosen infrastructure despite higher costs.",
      "Monetization Testing Strategy": "Drafting the onboarding split test and preparing beta survey questions directly implements the A/B testing strategy for pricing model validation.",
      "Documentation and Story Structure": "The plot tree feature design with drag-and-drop nodes and contextual linking directly addresses the multi-threaded plotting needs identified through the story structure discussion.",
      "Budgeting App MVP Planning": "Sam's observation about knowledge graphs reveals deep architectural synergies - both apps can share node-based data structures and visualization components, validating the modular approach."
    },
    "linked_nodes": ["Technical Implementation Decisions", "Monetization Testing Strategy", "Documentation and Story Structure", "Budgeting App MVP Planning"],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Sam reviews key Startup Planning items with Taylor: 1) Confirm Plaid, 2) Draft onboarding split test, 3) Prep beta survey questions. They then design a plot tree view feature for the outlining app with drag-and-drop nodes and contextual linking, connecting it to knowledge graph concepts in the budgeting app."
  },
  {
    "node_name": "Project Synergy Reflection",
    "type": "conversational_thread",
    "predecessor": "Action Items and Feature Design",
    "successor": null,
    "contextual_relation": {
      "Startup Planning Bookmark": "Sam reopens the bookmark to update it with concrete next steps: implement API, finalize A/B logic, and send beta invites, ensuring all planning elements remain actionable.",
      "Action Items and Feature Design": "The architectural synergies between projects validate the modular design approach, with shared components strengthening both applications.",
      "Outlining Tool Revival": "The mutual reinforcement between projects confirms the wisdom of reviving the outlining tool - it's not just independently viable but actively enhances the overall technical architecture."
    },
    "linked_nodes": ["Startup Planning Bookmark", "Action Items and Feature Design", "Outlining Tool Revival"],
    "chunk_id": null,
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Sam opens Startup Planning bookmark while Taylor updates it with next steps. Sam appreciates how both projects feed into each other, strengthening the architecture, with Taylor noting this promotes modular thinking."
  }
]
"""
    for attempt in range(retries):
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                # model="claude-3-7-sonnet-20250219", # claude 3.7 sonnet
                model="claude-3-5-haiku-20241022", # claude 3.5 haiku
                # max_tokens=20000,
                max_tokens= 8192,
                temperature=temp,
                system= generate_lct_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": transcript
                                    }
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "[\n{"
                            }
                        ]
                    }
                ]
            )
            json_text = "[\n{" + message.content[0].text
            
            return json.loads(json_text)  # Parse JSON response
            

        except json.JSONDecodeError as e:
            print(f"[INFO]: Invalid JSON: {e}")
            return None

        except anthropic.AuthenticationError:
            print("[INFO]: Authentication failed. Check your API key.")
            return None

        except anthropic.RateLimitError:
            print("[INFO]: Rate limit exceeded. Retrying...")  # Retryable

        except anthropic.APIError as e:
            print(f"[INFO]: API error occurred: {e}")
            if "overloaded" not in str(e).lower():
                return None

        except Exception as e:
            print(f"[INFO]: Unexpected error: {e}")
            return None

def generate_lct_json_gemini(
    transcript: str,
    retries: int = 5,
    backoff_base: float = 1.5
):
    
    client = genai.Client(api_key=GOOGLEAI_API_KEY)
    model = "gemini-2.5-flash-preview-05-20"

    generate_lct_prompt = """You are an advanced AI model that structures conversations into strictly JSON-formatted nodes. Each conversational shift should be captured as a new node with defined relationships, with primary emphasis on capturing rich contextual connections that demonstrate thematic coherence, conceptual evolution, and cross-conversational idea building.
**Formatting Rules:**

**Instructions:**

**Handling New JSON Creation**
Extract Key Nodes: Identify all topic shifts in the conversation. Each topic shift forms a new "node", even if the topic was discussed earlier.

**Strictly Generate JSON Output:**
[
  {
    "node_name": "Title of the conversational thread",
    "predecessor": "Previous node name",
    "successor": "Next node name",
    "contextual_relation": {
      "Related Node 1": "Detailed explanation of how this node connects thematically, shows conceptual evolution, and builds upon ideas from the current discussion",
      "Related Node 2": " Another comprehensive explanation that weaves together thematic connections with how concepts have developed",
      "...": "Additional related nodes with their respective explanations can be included as needed"
    },
    "chunk_id": null,  // This field will be **ignored** for now and will be added externally.
    "linked_nodes": [
      "List of all nodes this node is either drawing context from or providing context to"
    ],
    "is_bookmark": true or false,
    ""is_contextual_progress": true or false,
    "summary": "Detailed description of what was discussed in this node.",
    "claims": [                    // NEW-  may be empty
  "Fact-checkable claim made by a speaker in this node",
  "Another claim, if present"]
  }
]
**Enhanced Contextual Relations Approach:**
-	In "contextual_relation", provide integrated explanations that naturally weave together:
-	How nodes connect thematically (shared concepts, related ideas)
-	How concepts have evolved or been refined since previous mentions
-	How ideas build upon each other across different conversation segments
-	 Don’t capture direct shifts in conversations as contextual_relation unless there is a relevant contextual relation only then capture it.
- "linked_nodes" must track all nodes this node is either drawing context from or providing context to in a single list.
Create cohesive narratives that explain the full relationship context rather than treating these as separate analytical dimensions.

**Define Structure:**
"predecessor" → The direct previous node temporally.
"successor" → The direct next node temporally.
"contextual_relation" → Use this to explain how past nodes contribute to the current discussion contextually.
•	Keys = node names that contribute context.
•	Values = a detailed explanation of how the multiple referenced nodes influence the current discussion.
"chunk_id" → This field will be ignored for now, as it will be added externally by the code.

**Claims Field Detection and Handling**
"claims" must include only explicit, fact-checkable assertions made by a speaker.
A claim is considered fact-checkable if it states something that can be independently verified or falsified using objective data or authoritative sources.
If no valid claims exist in the node, leave "claims": [].
Do not include:
Opinions or subjective statements (“Plaid seems better”)
Suggestions, questions, or hypotheticals (“Should we go with Plaid?”)
Abstract or untestable beliefs (“I feel Plaid is more modern”)

Be strictly conservative:
If a statement feels uncertain, implied, subjective, speculative, or ambiguous, do not include it as a claim.
Only add when there is a clear, confident declaration that something is true or factual, regardless of actual correctness.
Claims may be true or false—this field captures assertions, not verified facts.
Additionally, claims must include enough context to be independently verified:
A valid claim must provide sufficient specificity (e.g., named entities, timeframes, data, measurable outcomes) to be fact-checked without relying on implicit assumptions.
Avoid fragmentary or vague claims that cannot be verified on their own.
Claims should be self-contained, meaning a reviewer unfamiliar with the full transcript should still understand what is being asserted.

Multiple factual claims may be listed when clearly present.

**Handling Updates to Existing JSON**
If an existing JSON structure is provided along with the transcript, modify it as follows and strictly return only the nodes generated for the current input transcript:

- **Continuing a topic**: If the conversation continues an existing discussion, update the "successor" field of the last relevant node.
-	**New topic**: If a conversation introduces a new topic, create a new node and properly link it.
-	**Revisiting a Bookmark**: If "LLM wish bookmark open [name]" appears, find the existing bookmark node and update its "contextual_relation". Do NOT create a new bookmark when revisited—update the existing one instead.
-	**Contextual Relation Updates**: Maintain connections that demonstrate how past discussions influence current ones through integrated thematic, evolutionary, and developmental relationships.

**Chronology, Contextual Referencing and Bookmarking**
If a topic is revisited, create a new node while ensuring proper linking to previous mentions through rich contextual relations. Ensure mutual linking between nodes that provide context to each other through comprehensive relationship explanations.

Each node must include both "predecessor" and "successor" fields to maintain chronological flow, maintaining the flow of the conversation irrespective of how related the topics are and strictly based on temporal relationship.

**VERY STRICTLY** only the first node should have predecessor as null and the last node should have successor as null

**Conversational Threads nodes(“is_bookmark”: false):**
- Every topic shift must be captured as a new node.
- "contextual_relation" must provide integrated explanations of how previous discussions contribute to the current conversation through thematic connections, conceptual evolution, and idea building.
- For non bookmark nodes, always set "is_bookmark": false.
 **Handling Revisited Topics**
 If a conversation returns to a previously discussed topic, create a new node and ensure "contextual_relation" provides comprehensive explanations of how past discussions relate to current context.

**Bookmark nodes (“is_bookmark”: true) must:**
- A bookmark node must be created when "LLM wish bookmark create" appears, capturing the contextually relevant topic.
- Do not create bookmark node unless "LLM wish bookmark create" is mentioned.
- "contextual_relation" must reference nodes with integrated explanations of relationships, ensuring contextual continuity.
- The summary should clearly describe the reason for creating the bookmark and what it aims to track.
- If "LLM wish bookmark open" appears, do not create a new bookmark—update the existing one.
- For bookmark nodes, always set "is_bookmark": true.



**Contextual Progress Capture ("is_contextual_progress": true):**
-	Only If "LLM wish capture contextual progress" appears, update the existing node (either "conversational_thread" or "bookmark") to include:
o	"is_contextual_progress": true
-	Contextual progress capture is used to capture a potential insight that might be present in that conversational node. 
-	It represents part of the conversation that could potentially be an insight that could be useful. These "potential insights" are the directions provided by humans that can later be taken by AI, which then uses this to generate formalisms.
-	Do not create a new node for contextual progress capture. Instead, apply the flag to the relevant existing node where the potential insight was introduced or referenced.
-**Contextual Relation & Linked Nodes Updates:**
- "contextual_relation" must provide comprehensive, integrated explanations that demonstrate the full scope of how nodes relate through thematic coherence, conceptual development, and cross-conversational idea building as unified relationship narratives.
- **VERY STRICTLY** Don’t capture direct shifts in conversations as contextual_relation unless there is a relevant contextual relation only then capture it. Direct transitions are “NOT” contextual_relation.
- "linked_nodes" must include all references in a single list, capturing all nodes this node draws from or informs.
- The structure of "predecessor", "successor", and "contextual_relation" must ensure logical and chronological consistency between past and present discussions.

**Example Input**
**Existing JSON:**

**Transcript:**
Alex: Did you see OpenAI's latest update on GPT-4o?
Jordan: Yeah—ChatGPT-4o supports a 128k context window and multimodal inputs natively now.
Alex: That’s a big jump. 3.5-turbo had 16k if I remember correctly.
Jordan: Correct. And the latency on 4o is down significantly—around 232ms in some of their benchmarks.
Alex: LLM wish bookmark create ChatGPT-4o Rollout
Jordan: I’ve been thinking we could integrate it into our knowledge assistant prototype.
Alex: Possibly. We’d need to check pricing. I believe 4o is cheaper than GPT-4, especially for input tokens.
Jordan: Last I checked, GPT-4o input tokens are $5 per million, output $15 per million. GPT-4 was more like $30 output.
Alex: That would drastically lower inference cost for our use case.
Jordan: LLM wish capture contextual progress Assistant Architecture Optimization
Alex: Shifting gears—Stripe is updating their pricing again starting July 1.
Jordan: Yeah, new fee is 3.15% + 25¢ per transaction in the U.S.
Alex: That’s up from 2.9% + 30¢, right?
Jordan: Correct. The impact on margin’s non-trivial—we should update our revenue model.
Alex: Definitely. I’ll flag it to finance.
Jordan: Also, AWS made Graviton3 processors generally available in us-east-1 last week.
Alex: Nice. We saved 18% on EC2 when we switched from x86 to Graviton2 last year.
Jordan: I imagine Graviton3 would be even better. It has 25% better performance-per-watt than Graviton2 according to AWS docs.
Alex: Worth benchmarking for sure.
Jordan: LLM wish capture contextual progress Cloud Cost Optimization Path
Alex: And the mobile web still loads in 3.9 seconds. That’s killing our bounce rate.
Jordan: We need to compress more assets—LCP is at 3.1s on average, above the recommended 2.5s.
Alex: Okay, let’s make it a priority for this sprint.
Jordan: Sounds good. I’ll document the ChatGPT, AWS, and Stripe updates in our shared infra log.


**Example JSON Output:**
 [{
    "node_name": "ChatGPT-4o Technical Specifications Discussion",
    "predecessor": null,
    "successor": "ChatGPT-4o Rollout Bookmark",
    "contextual_relation": {},
    "chunk_id": null,
    "linked_nodes": [],
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Alex and Jordan discuss OpenAI's latest GPT-4o update, covering technical specifications including the 128k context window, multimodal input capabilities, and significantly reduced latency of around 232ms compared to previous versions like GPT-3.5-turbo which had a 16k context window.",
    "claims": [
      "ChatGPT-4o supports a 128k context window and multimodal inputs natively",
      "GPT-3.5-turbo had a 16k context window",
      "GPT-4o latency is around 232ms in OpenAI's benchmarks"
    ]
  },
  {
    "node_name": "ChatGPT-4o Rollout Bookmark",
    "predecessor": "ChatGPT-4o Technical Specifications Discussion",
    "successor": "Integration and Pricing Considerations",
    "contextual_relation": {
      "ChatGPT-4o Technical Specifications Discussion": "This bookmark captures the significant technical advancement discussion about GPT-4o's capabilities, serving as a reference point for tracking the rollout and implementation considerations of this new model with its enhanced context window and reduced latency"
    },
    "chunk_id": null,
    "linked_nodes": ["ChatGPT-4o Technical Specifications Discussion"],
    "is_bookmark": true,
    "is_contextual_progress": false,
    "summary": "Bookmark created to track the ChatGPT-4o rollout discussion, focusing on the technical specifications and potential integration opportunities for their knowledge assistant prototype.",
    "claims": []
  },
  {
    "node_name": "Integration and Pricing Considerations",
    "predecessor": "ChatGPT-4o Rollout Bookmark",
    "successor": "Assistant Architecture Optimization Progress Capture",
    "contextual_relation": {
      "ChatGPT-4o Technical Specifications Discussion": "Building on the technical capabilities discussion, this explores the practical implementation aspects by evaluating cost-effectiveness and integration feasibility for their knowledge assistant prototype, connecting the technical advantages to business viability"
    },
    "chunk_id": null,
    "linked_nodes": ["ChatGPT-4o Technical Specifications Discussion"],
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Discussion of integrating GPT-4o into their knowledge assistant prototype, with focus on pricing analysis comparing GPT-4o costs ($5 per million input tokens, $15 per million output tokens) to GPT-4 ($30 per million output tokens), highlighting potential cost savings for their use case.",
    "claims": [
      "GPT-4o input tokens are $5 per million, output $15 per million",
      "GPT-4 output tokens cost $30 per million"
    ]
  },
  {
    "node_name": "Assistant Architecture Optimization Progress Capture",
    "predecessor": "Integration and Pricing Considerations",
    "successor": "Stripe Pricing Update Discussion",
    "contextual_relation": {
      "ChatGPT-4o Technical Specifications Discussion": "This progress capture synthesizes the technical capabilities discussion into actionable insights for optimizing their assistant architecture, identifying how GPT-4o's enhanced performance and cost structure can drive infrastructure improvements",
      "Integration and Pricing Considerations": "The contextual progress builds on the cost-benefit analysis by capturing the strategic opportunity to optimize their assistant architecture through GPT-4o integration, representing a potential pathway for significant cost reduction and performance enhancement"
    },
    "chunk_id": null,
    "linked_nodes": ["ChatGPT-4o Technical Specifications Discussion", "Integration and Pricing Considerations"],
    "is_bookmark": false,
    "is_contextual_progress": true,
    "summary": "Contextual progress captured regarding assistant architecture optimization opportunities, focusing on how GPT-4o's improved performance and reduced costs could significantly enhance their knowledge assistant prototype's efficiency and economic viability.",
    "claims": []
  },
  {
    "node_name": "Stripe Pricing Update Discussion",
    "predecessor": "Assistant Architecture Optimization Progress Capture",
    "successor": "AWS Graviton3 Processor Announcement",
    "contextual_relation": {},
    "chunk_id": null,
    "linked_nodes": [],
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Alex and Jordan discuss Stripe's pricing changes effective July 1, with new fees of 3.15% + 25¢ per transaction in the U.S., up from the previous 2.9% + 30¢ structure, and the need to update their revenue model to account for the margin impact.",
    "claims": [
      "Stripe is updating their pricing starting July 1",
      "New Stripe fee is 3.15% + 25¢ per transaction in the U.S.",
      "Previous Stripe fee was 2.9% + 30¢ per transaction"
    ]
  },
  {
    "node_name": "AWS Graviton3 Processor Announcement",
    "predecessor": "Stripe Pricing Update Discussion",
    "successor": "Cloud Cost Optimization Path Progress Capture",
    "contextual_relation": {},
    "chunk_id": null,
    "linked_nodes": [],
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Discussion of AWS making Graviton3 processors generally available in us-east-1, with context about their previous 18% cost savings from switching to Graviton2 and Graviton3's 25% better performance-per-watt compared to Graviton2.",
    "claims": [
      "AWS made Graviton3 processors generally available in us-east-1 last week",
      "They saved 18% on EC2 when switching from x86 to Graviton2 last year",
      "Graviton3 has 25% better performance-per-watt than Graviton2 according to AWS docs"
    ]
  },
  {
    "node_name": "Cloud Cost Optimization Path Progress Capture",
    "predecessor": "AWS Graviton3 Processor Announcement",
    "successor": "Mobile Web Performance Issues",
    "contextual_relation": {
      "AWS Graviton3 Processor Announcement": "This progress capture builds on the Graviton3 discussion by identifying a clear optimization pathway, connecting their proven success with Graviton2 cost savings to the potential for even greater efficiency gains with Graviton3's enhanced performance-per-watt ratio"
    },
    "chunk_id": null,
    "linked_nodes": ["AWS Graviton3 Processor Announcement"],
    "is_bookmark": false,
    "is_contextual_progress": true,
    "summary": "Contextual progress captured regarding cloud cost optimization opportunities, focusing on the potential for further EC2 cost reductions through Graviton3 adoption based on their successful Graviton2 migration experience.",
    "claims": []
  },
  {
    "node_name": "Mobile Web Performance Issues",
    "predecessor": "Cloud Cost Optimization Path Progress Capture",
    "successor": "Infrastructure Updates Documentation",
    "contextual_relation": {},
    "chunk_id": null,
    "linked_nodes": [],
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Alex and Jordan address mobile web performance problems, with load times of 3.9 seconds and Largest Contentful Paint (LCP) at 3.1 seconds, both above recommended thresholds and impacting bounce rates. They prioritize asset compression for the current sprint.",
    "claims": [
      "Mobile web loads in 3.9 seconds",
      "LCP is at 3.1s on average, above the recommended 2.5s"
    ]
  },
  {
    "node_name": "Infrastructure Updates Documentation",
    "predecessor": "Mobile Web Performance Issues",
    "successor": null,
    "contextual_relation": {
      "ChatGPT-4o Rollout Bookmark": "This documentation effort connects back to the ChatGPT-4o rollout tracking by ensuring all infrastructure changes, including the potential GPT-4o integration, are properly recorded for future reference and implementation planning",
      "Stripe Pricing Update Discussion": "The documentation captures the Stripe pricing changes that need to be integrated into their revenue model, ensuring financial planning considerations are preserved alongside technical infrastructure updates",
      "AWS Graviton3 Processor Announcement": "Documentation includes the AWS Graviton3 availability information, creating a comprehensive record of cloud optimization opportunities that can inform future infrastructure decisions"
    },
    "chunk_id": null,
    "linked_nodes": ["ChatGPT-4o Rollout Bookmark", "Stripe Pricing Update Discussion", "AWS Graviton3 Processor Announcement"],
    "is_bookmark": false,
    "is_contextual_progress": false,
    "summary": "Jordan commits to documenting all discussed infrastructure updates including ChatGPT-4o specifications, Stripe pricing changes, and AWS Graviton3 availability in their shared infrastructure log for future reference and planning.",
    "claims": []
  }
]
"""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=transcript)],
        )
    ]

    config = types.GenerateContentConfig(
        temperature=0.65,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        response_mime_type="application/json",
        system_instruction=[types.Part.from_text(text=generate_lct_prompt)],
    )

    for attempt in range(retries):
        full_response = ""  # reset each attempt
        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            ):
                if hasattr(chunk, "text"):
                    full_response += chunk.text

            try:
                parsed = json.loads(full_response)
                return parsed

            except json.JSONDecodeError as e:
                print(f"[INFO]: [Attempt {attempt+1}] JSON decoding failed: {e}")
                print(f"[INFO]: [Raw response]:\n{full_response}")

        except Exception as e:
            print(f"[INFO]: [Attempt {attempt+1}] Unexpected error: {e}")

        # Exponential backoff
        time.sleep(backoff_base ** attempt)

    # Final fallback after all retries fail
    print("[INFO]: [Final] All attempts failed. Returning empty node list.")
    return []
    # client = genai.Client(api_key=GOOGLEAI_API_KEY)
    # model = "gemini-2.5-flash-preview-05-20"

    # generate_lct_prompt = "You are an advanced AI model that structures conversations into strictly JSON-formatted nodes. Each conversational shift should be captured as a new node with defined relationships.\n\nFormatting Rules:\n\nInstructions:\n\nHandling New JSON Creation\nExtract Key Nodes: Identify all topic shifts in the conversation. Each topic shift forms a new \"node\", even if the topic was discussed earlier.\n\nStrictly Generate JSON Output:\n[\n  {\n    \"node_name\": \"Title of the conversational thread\",\n    \"type\": \"conversational_thread\" or \"bookmark\",\n    \"predecessor\": \"Previous node name\",\n    \"successor\": \"Next node name\",\n    \"contextual_relation\": {\n      \"Related Node 1\": \"Detailed explanation of how this node's context is used\",\n      \"Related Node 2\": \"Another detailed explanation\",\n      \"...\": \"Additional related nodes with their respective explanations can be included as needed\"\n    },\n    \"linked_nodes\": [\n      \"List of all nodes this node is either drawing context from or providing context to\"\n    ],\n    \"chunk_id\": None,  // This field will be **ignored** for now and will be added externally.\n    \"is_bookmark\": True or False,\n    \"\"is_contextual_progress\": True or False,\n    \"summary\": \"Detailed description of what was discussed in this node.\"\n  }\n]\n\nDefine Structure:\n\"predecessor\" → The direct previous node.\n\"successor\" → The direct next node.\n\"contextual_relation\" → Use this to explain how past nodes contribute to the current discussion contextually.\nKeys = node names that contribute context.\nValues = a detailed explanation of how the multiple referenced nodes influence the current discussion.\n\n\"linked_nodes\" → A comprehensive list of all nodes this node is either drawing context from or providing context to, this information of context providing will come from \"contextual_relation\", consolidating references into a single field.\n\"chunk_id\" → This field will be ignored for now, as it will be added externally by the code.\n\nHandling Updates to Existing JSON\nIf an existing JSON structure is provided along with the transcript , modify it as follows and Strictly return only the nodes generated for the current input transcript:\n\nContinuing a topic: If the conversation continues an existing discussion, update the \"successor\" field of the last relevant node.\nNew topic: If a conversation introduces a new topic, create a new node and properly link it.\nRevisiting a Bookmark:\nIf \"LLM wish bookmark open [name]\" appears, find the existing bookmark node and update its \"contextual_relation\" and \"linked_nodes\".\nDo NOT create a new bookmark when revisited—update the existing one instead.\nContextual Relation Updates:\nMaintain indirect connections (e.g., a previous conversation influencing the new one).\nEnsure logical flow between past and present discussions.\n\n\nChronology, Contextual Referencing and Bookmarking\nIf a topic is revisited, create a new node while ensuring proper linking to previous mentions.\nEnsure mutual linking between nodes that provide context to each other. If a node references a past discussion, ensure the past node also updates its \"linked_nodes\" to include the new node.\n\n\nConversational Threads nodes (type: \"conversational_thread\"):\nEvery topic shift must be captured as a new node.\nEach node must include both \"predecessor\" and \"successor\" fields to maintain chronological flow.\n\"contextual_relation\" must explain how previous discussions contribute to the current conversation.\n\"linked_nodes\" must track all nodes this node is either drawing context from or providing context to in a single list.\nFor nodes with type=\"conversational_thread\", always set \"is_bookmark\": False.\nHandling Revisited Topics:\nIf a conversation returns to a previously discussed topic, create a new node instead of merging with an existing one.\nEnsure \"contextual_relation\" references past discussions of the same topic, explaining their relevance in the current context.\nBookmark nodes (type: \"bookmark\") must:\nA bookmark node must be created when \"LLM wish bookmark create\" appears, capturing the contextually relevant topic.\nDo not create bookmark node unless the phrase \"LLM wish bookmark create\" is mentioned.\n\"contextual_relation\" must reference the exact nodes where the bookmark was created and opened, ensuring contextual continuity.\nThe summary should clearly describe the reason for creating the bookmark and what it aims to track.\nIf \"LLM wish bookmark open\" appears, do not create a new bookmark—update the existing one.\nModify \"contextual_relation\" to include the new node where the bookmark was accessed, ensuring that past discussions remain linked.\nProvide a clear explanation of how the revisited discussion builds on the previously stored context.\nFor nodes with type=\"bookmark\", always set \"is_bookmark\": True.\n\nContextual Progress Capture (\"is_contextual_progress\": True)\nOnly If  the whole phrase \"LLM wish capture contextual progress\" appears, update the existing node (either \"conversational_thread\" or \"bookmark\") to include:\n\"is_contextual_progress\": True\nContextual progress capture is used to capture a potential insight that might be present in that conversational node. \nIt represents part of the conversation that could potentially be an insight that could be useful. These \"potential insights\" are the directions provided by humans that can later be taken by AI, which then uses this to generate formalisms.\nDo not create a new node for contextual progress capture. Instead, apply the flag to the relevant existing node where the potential insight was introduced or referenced.\n\nContextual Relation & Linked Nodes Updates:\n\"contextual_relation\" must explain why past discussions are relevant, ensuring clarity in topic evolution.\n\"linked_nodes\" must include all references in a single list, capturing all nodes this node draws from or informs.\nThe structure of \"predecessor\", \"successor\", and \"contextual_relation\" must ensure logical and chronological consistency between past and present discussions.\n\nExample Input (Conversation with Bookmark Spells):\nExisting JSON:\n\nTranscript:\nAlex: Hey Jordan, summer's coming up. We should totally go on a road trip!\nJordan: That sounds awesome! But road trips can get expensive. Gas, food, places to stay… It all adds up.\nAlex: True, but we can budget it out. If we book some places early and plan food stops, we might save some cash.\nJordan: Yeah, maybe we can also stay at some cheap motels or even camp for a few nights.\nAlex: Exactly. I'll make a list of potential stops and places to sleep.\nAlex: LLM wish bookmark create Road Trip Planning.\nJordan: Speaking of planning, I've been trying to fix my sleep schedule. Finals completely messed it up.\nAlex: Oh yeah, I feel you. When people get stressed, they sleep less, which makes them even more stressed, and then they sleep even less.\nJordan: Yep, and then when you add caffeine into the mix, it just makes things worse. I was practically running on energy drinks.\nAlex: Not to mention, when you're sleep-deprived, you tend to eat worse, and bad eating can also make it harder to sleep. It's like everything is connected.\nJordan: So basically, when you're stressed, you don't sleep enough. Then because you don't sleep, you get more stressed, and things like caffeine and bad eating habits just make the whole situation even worse.\nAlex: Exactly. But the good news is that breaking just one part of the cycle—like cutting down on caffeine or trying to fix your sleep schedule—can help stop everything from spiraling out of control.\nJordan: Makes sense. I guess I need to start by drinking less caffeine.\nAlex: Yeah, and maybe try doing something relaxing before bed, like listening to music or reading instead of staring at your phone.\nJordan: LLM wish capture contextual progress Stress-Sleep Cycle.\nAlex: Anyway, did you hear about that new horror movie coming out next month?\nJordan: Oh, yeah! It looks terrifying. I love a good horror flick.\nAlex: We should totally watch it when it releases.\nJordan: Definitely. But no watching it late at night—I'll never get any sleep.\nAlex: Haha, fair enough.\nJordan: Oh, by the way, about that road trip—do you think we should rent a car or use mine?\nAlex: Good question. Your car is solid, but renting might save us some trouble if we're going really far.\nJordan: Yeah, plus, rentals come with insurance, which could be helpful.\nAlex: LLM wish bookmark open Road Trip Planning.\nJordan: Right, so we need to decide if we're driving your car or renting, and we should check gas prices along the way.\nAlex: Yep, and maybe look at rental deals. I'll compare some prices later.\nJordan: Sounds good. Let's lock in a plan soon!\n\n\nExample JSON Output:\n[\n  {\n    \"node_name\": \"Road Trip Planning\",\n    \"type\": \"bookmark\",\n    \"predecessor\": None,\n    \"successor\": \"Fixing Sleep Schedules and Stress\",\n    \"contextual_relation\": {},\n    \"linked_nodes\": [\n      \"Fixing Sleep Schedules and Stress\",\n      \"Road Trip Planning - Car Rental Discussion\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": True,\n    \"is_contextual_progress\": False,\n    \"summary\": \"Alex and Jordan discuss planning a summer road trip, acknowledging budget concerns. They decide to save money by booking accommodations early, staying at cheap motels, and camping. Alex plans to make a list of potential stops and sleeping arrangements.\"\n  },\n  {\n    \"node_name\": \"Fixing Sleep Schedules and Stress\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Road Trip Planning\",\n    \"successor\": \"Horror Movie Discussion\",\n    \"contextual_relation\": {\n      \"Road Trip Planning\": \"The transition from road trip planning to discussing sleep schedules happens naturally as Jordan mentions finals disrupting their sleep.\"\n    },\n    \"linked_nodes\": [\n      \"Road Trip Planning\",\n      \"Horror Movie Discussion\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": False,\n    \"is_contextual_progress\": True,\n    \"summary\": \"Jordan mentions their sleep schedule being disrupted due to finals, leading to a discussion on stress and sleep deprivation. They explore how stress, caffeine, and bad eating habits contribute to a negative cycle and discuss ways to break it, such as reducing caffeine intake and establishing a better nighttime routine.\"\n  },\n  {\n    \"node_name\": \"Horror Movie Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Fixing Sleep Schedules and Stress\",\n    \"successor\": \"Road Trip Planning - Car Rental Discussion\",\n    \"contextual_relation\": {\n      \"Fixing Sleep Schedules and Stress\": \"The discussion transitions from sleep issues to horror movies, as Jordan jokes about avoiding horror films at night to prevent sleep loss.\"\n    },\n    \"linked_nodes\": [\n      \"Fixing Sleep Schedules and Stress\",\n      \"Road Trip Planning - Car Rental Discussion\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": False,\n    \"is_contextual_progress\": False,\n    \"summary\": \"Alex and Jordan discuss an upcoming horror movie. Jordan expresses excitement but jokes about avoiding late-night viewing to prevent sleep issues.\"\n  },\n  {\n    \"node_name\": \"Road Trip Planning - Car Rental Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Horror Movie Discussion\",\n    \"successor\": None,\n    \"contextual_relation\": {\n      \"Road Trip Planning\": \"The conversation returns to road trip planning as Jordan revisits the topic, prompting discussions about using a personal car versus renting one.\",\n      \"Horror Movie Discussion\": \"The transition occurs naturally as Alex and Jordan shift from casual movie talk back to logistics for their trip.\"\n    },\n    \"linked_nodes\": [\n      \"Road Trip Planning\",\n      \"Horror Movie Discussion\",\n      \"Fixing Sleep Schedules and Stress\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": False,\n    \"is_contextual_progress\": False,\n    \"summary\": \"Jordan brings the conversation back to the road trip, specifically whether to rent a car or use a personal vehicle. They consider factors like gas prices and rental insurance before agreeing to compare rental deals.\"\n  }\n]\n"

    # contents = [
    #     types.Content(
    #         role="user",
    #         parts=[types.Part.from_text(text=transcript)],
    #     )
    # ]

    # config = types.GenerateContentConfig(
    #     temperature=0.65,
    #     thinking_config=types.ThinkingConfig(thinking_budget=0),
    #     response_mime_type="application/json",
    #     system_instruction=[types.Part.from_text(text=generate_lct_prompt)],
    # )

    # for attempt in range(retries):
    #     try:
    #         full_response = ""
    #         for chunk in client.models.generate_content_stream(
    #             model=model,
    #             contents=contents,
    #             config=config,
    #         ):
    #             if hasattr(chunk, "text"):
    #                 full_response += chunk.text

    #         return json.loads(full_response)

    #     except json.JSONDecodeError as e:
    #         print(f"[Attempt {attempt+1}] JSON decoding failed: {e}")
    #         print("failed json :",full_response)

    #     except Exception as e:
    #         print(f"[Attempt {attempt+1}] Unexpected error: {e}")
    #         return None 

    #     # Exponential backoff before retrying
    #     time.sleep(backoff_base ** attempt)

    # return None

def genai_accumulate_text_json(
    input_text: str,
    retries: int = 3,
    backoff_base: float = 1.5
):
    model_name = "gemini-2.5-flash-preview-05-20"

    system_prompt = """You are an expert conversation analyst and advanced AI reasoning assistant. I will provide you with a block of accumulated transcript text. Your task is to determine whether this text contains at least one complete and self-contained conversational thread, and if so, return all complete threads while leaving any incomplete ones for future accumulation.
Definition:
A conversational thread is a contiguous portion of a conversation that:
– Focuses on a coherent sub-topic or goal,
– Is interpretable on its own, without requiring future context,
– Demonstrates clear semantic structure: an initiation, development, and closure.
The input may contain zero, one, or multiple complete conversational threads. It will appear as unstructured text, with no speaker labels, so you must infer structure using topic continuity, transitions, and semantic signals.
Output Specification:
Return a JSON object containing:
"Decision":
– "continue_accumulating" if no complete thread can be identified.
– "stop_accumulating" if at least one complete and self-contained conversational thread exists.
"Completed_segment":
If "stop_accumulating", return the portion of the input that contains one or more completed conversational threads.
"Incomplete_segment":
The remaining text that is incomplete, off-topic, or still developing.
"detected_threads":
Return a list of short, descriptive names for each complete conversational thread detected in completed_segment.
Evaluation Notes:
– Be conservative: If in doubt, continue accumulating.
– Use semantic structure and topic closure to determine completeness — not superficial transitions.
– It is valid to return more than one thread in completed_segment, but each must be complete and independently meaningful.
– Do not rearrange the order of the text. Preserve original sequencing when splitting.
"""

    for attempt in range(retries):
        full_response = ""
        try:
            client = genai.Client(api_key=GOOGLEAI_API_KEY)

            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=input_text)],
                ),
            ]

            config = types.GenerateContentConfig(
                temperature=0.65,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                response_mime_type="application/json",
                response_schema=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    properties={
                        "decision": genai.types.Schema(type=genai.types.Type.STRING),
                        "Completed_segment": genai.types.Schema(type=genai.types.Type.STRING),
                        "Incomplete_segment": genai.types.Schema(type=genai.types.Type.STRING),
                        "detected_threads": genai.types.Schema(
                            type=genai.types.Type.ARRAY,
                            items=genai.types.Schema(type=genai.types.Type.STRING),
                        ),
                    },
                ),
                system_instruction=[types.Part.from_text(text=system_prompt)],
            )

            for chunk in client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config,
            ):
                if hasattr(chunk, "text"):
                    full_response += str(chunk.text)

            # Try to decode
            try:
                return json.loads(full_response)
            except json.JSONDecodeError as e:
                print(f"[INFO]: [Attempt {attempt+1}] JSON decoding failed: {e}")
                print(f"[INFO]: [Raw Gemini output]:\n{full_response}")

        except Exception as e:
            print(f"[INFO]: [Attempt {attempt+1}] Unexpected error: {e}")

        time.sleep(backoff_base ** attempt)

    # Final fallback
    print("[INFO]: [Final] All decoding attempts failed — using conservative fallback.")
    return {
        "decision": "continue_accumulating",
        "Completed_segment": "",
        "Incomplete_segment": input_text,
        "detected_threads": [],
    }
#     model_name = "gemini-2.5-flash-preview-05-20"

#     system_prompt = """You are an expert conversation analyst and advanced AI reasoning assistant. I will provide you with a block of accumulated transcript text. Your task is to determine whether this text contains at least one complete and self-contained conversational thread, and if so, return all complete threads while leaving any incomplete ones for future accumulation.
# Definition:
# A conversational thread is a contiguous portion of a conversation that:
# – Focuses on a coherent sub-topic or goal,
# – Is interpretable on its own, without requiring future context,
# – Demonstrates clear semantic structure: an initiation, development, and closure.
# The input may contain zero, one, or multiple complete conversational threads. It will appear as unstructured text, with no speaker labels, so you must infer structure using topic continuity, transitions, and semantic signals.
# Output Specification:
# Return a JSON object containing:
# "Decision":
# – "continue_accumulating" if no complete thread can be identified.
# – "stop_accumulating" if at least one complete and self-contained conversational thread exists.
# "Completed_segment":
# If "stop_accumulating", return the portion of the input that contains one or more completed conversational threads.
# "Incomplete_segment":
# The remaining text that is incomplete, off-topic, or still developing.
# "detected_threads":
# Return a list of short, descriptive names for each complete conversational thread detected in completed_segment.
# Evaluation Notes:
# – Be conservative: If in doubt, continue accumulating.
# – Use semantic structure and topic closure to determine completeness — not superficial transitions.
# – It is valid to return more than one thread in completed_segment, but each must be complete and independently meaningful.
# – Do not rearrange the order of the text. Preserve original sequencing when splitting.
# """

#     for attempt in range(retries):
#         try:
#             client = genai.Client(api_key=GOOGLEAI_API_KEY)

#             contents = [
#                 types.Content(
#                     role="user",
#                     parts=[
#                         types.Part.from_text(text=input_text)
#                     ],
#                 ),
#             ]

#             config = types.GenerateContentConfig(
#                 temperature=0.65,
#                 thinking_config=types.ThinkingConfig(thinking_budget=0),
#                 response_mime_type="application/json",
#                 response_schema=genai.types.Schema(
#                     type=genai.types.Type.OBJECT,
#                     properties={
#                         "decision": genai.types.Schema(type=genai.types.Type.STRING),
#                         "Completed_segment": genai.types.Schema(type=genai.types.Type.STRING),
#                         "Incomplete_segment": genai.types.Schema(type=genai.types.Type.STRING),
#                         "detected_threads": genai.types.Schema(
#                             type=genai.types.Type.ARRAY,
#                             items=genai.types.Schema(type=genai.types.Type.STRING),
#                         ),
#                     },
#                 ),
#                 system_instruction=[types.Part.from_text(text=system_prompt)],
#             )

#             full_response = ""
#             for chunk in client.models.generate_content_stream(
#                 model=model_name,
#                 contents=contents,
#                 config=config,
#             ):
#                 if hasattr(chunk, "text"):
#                     full_response += str(chunk.text)
#             return json.loads(full_response)

#         except json.JSONDecodeError as e:
#             print(f"[Attempt {attempt+1}] JSON decoding failed: {e}")
            

#         except Exception as e:
#             print(f"[Attempt {attempt+1}] Unexpected error: {e}")
#             return None 

#         # Exponential backoff before retrying
#         time.sleep(backoff_base ** attempt)

#     return None  # If all attempts fail

def generate_individual_formalism(formalism_input: str, temp: float = 0.7, retries: int = 5, backoff_base: float = 1.5):
    generate_formalism_prompt ="You are an advanced AI model tasked with transforming structured conversational data and raw text into a concise causal loop diagram (CLD) represented as a dictionary with LOOPY-compatible structure. Your goal is to dynamically infer the relationships between topics discussed in the conversation and convert them into a causal loop diagram, with special focus on extracting formalism in the contextual progress of the conversation.\n\nYou will be provided with three inputs:\n1. conversation_data\n2. raw_text\n3. user_research_background - A description of the user's research interests and background\n\nAnalyze the conversation_data and raw_text to identify causal relationships and create a comprehensive causal loop diagram that aligns with the user's research background.\n\nOutput Format:\nYou must strictly return a dictionary in the following format:\n[\n  [\n    [id, x, y, init, label, color] # this is for nodes,\n    ...\n  ],\n  [\n    [from, to,arc,strength, _] # this is for the edges,\n    ...\n  ],\n  [\n    [x, y, text] # this is for the labels,\n    ...\n  ],\n  meta # this is the meta an integer\n]\n\ntypes of the about output format:\nnode = id - int, x - int, y -int, init - float(always 1), color- int.\nedges= from - int, to - int, arc - int, strength - float, _ = 0.\nlabels= x - int, y - int, text- str.\nmeta - int.\nWhere:\n- meta is the total number of nodes + labels + 2 (for edges).\n- Node id is a unique integer starting from 0.\n- Edges: Each edge refers to valid id values for from and to.\n- Assign random integers to color for different nodes but the integers assigned should be less than total number of nodes divided by 1.5.\n\nIMPORTANT: Only create nodes that have at least one causal relationship (edge) with another node. Do not include isolated nodes without any connecting edges.\n\nCRITICAL: Ensure that your diagram contains at least one complete causal loop where nodes are connected in a cycle (A→B→C→A or similar). The edges in these loops must form a complete circuit so that changes in any node propagate through the entire loop and affect the originating node. These must be genuine loops with actual causal connections, not just visually arranged in a circle.\n\nPRIMARY FOCUS: Prioritize identifying and extracting formalism in the contextual progress of the conversation. Examine how concepts, theories, methods, or structured approaches develop and influence each other throughout the conversation. Only include other nodes if they directly relate to this formalism development.\n\nRESEARCH CONTEXT ALIGNMENT: Frame all node labels, relationships, and concepts using terminology and perspectives relevant to the user's research background. The variables and causal connections should reflect the user's domain of expertise and research interests, making the diagram immediately relevant and intuitive to their field of study.\n\nLoop Detection and Construction:\nActively search for and construct complete causal loops in the conversation:\n- Reinforcing loops: Create cycles where changes amplify around the loop (e.g., A increases B, B increases C, C increases A).\n- Balancing loops: Create cycles that tend to stabilize (e.g., A increases B, B increases C, C decreases A).\n- Make sure every loop is complete with no breaks in the causal chain.\n- Test each loop by mentally tracing the effects: if one node increases, trace the effects through each connection to verify the loop completes and affects the original node.\n\nCausal Relation Detection:\nIdentify and infer causal relationships implicitly from the conversational context, summaries, and shifts between topics. Look for the following:\n1. Causal Direction: Recognize when one concept influences another (e.g., \"this leads to,\" \"this causes,\" \"results in,\" \"this influences\").\n2. Contextual Transitions: When the conversation shifts topics, infer the causal influence or dependency between these topics.\n3. Behavioral and Cognitive Feedback: Consider feedback loops and how certain topics may influence others based on previous discussions.\n\nVariable Naming Conventions:\n1. Use nouns or noun phrases for variable names that align with the user's research field terminology.\n2. Ensure variable names have a clear sense of direction (can be larger or smaller).\n3. Choose variables whose normal sense of direction is positive.\n4. Avoid using variable names containing prefixes indicating negation (non, un, etc.).\n5. Frame concepts using domain-specific language from the user's research background.\n\nEdge Strength Determination:\nDetermine edge strength based on the following scale:\n- Positive Influence → +1.0\n- Negative Influence → -1.0\n\nStep-by-step instructions for creating the CLD:\n1. Review the user's research background to understand their domain, terminology, and conceptual framework.\n2. Analyze the conversation_data and raw_text to identify key topics and concepts, focusing on formalism in the contextual progress.\n3. Create a list of variables (nodes) based on the identified topics, following the variable naming conventions and using terminology relevant to the user's research field.\n4. Determine causal relationships between variables using the causal relation detection guidelines.\n5. Explicitly identify or create at least one complete causal loop where a sequence of nodes connects back to the starting node.\n6. Verify each loop is functional by tracing the effect of increasing one node through the entire loop to confirm it eventually affects itself.\n7. Assign edge strengths based on the provided scale.\n8. Position nodes across a coordinate range (0-800 for x, 0-600 for y) to create a well-distributed visualization with adequate spacing.\n9. Arrange nodes that form loops in positions that clearly show the cyclical nature of their relationships.\n10. Create edges between related nodes, specifying the from and to node ids, and the strength of the relationship. Use appropriate arc values to make loop connections clear.\n11. Add one label to describe the causal loop diagram, positioning it at least 50 coordinate units away from any node to avoid overlap.\n12. Calculate the meta value by summing the total number of nodes, labels, and adding 2 for edges.\n\nFinal Output Formatting:\nConstruct the List with the following lists: \"nodes\", \"edges\", \"labels\", and \"meta\". Ensure that all required fields are included for each node, edge, and label. Double-check that the meta value is correctly calculated and that all node ids and edge references are valid.\n\nPresent your final output as a single list without any additional explanation or commentary."
    for attempt in range(retries):
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=20000,
                temperature=temp,
                system= generate_formalism_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": formalism_input
                            }
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "{"
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "You need to convert whatever you compute above to loopy url"

                                    "the url is"
                                    "https://ncase.me/loopy/v1.1"

                                    "here, the json made previously is a data parameter for this url, so we should urlencode this into data=<urlencoded json structure>"
                                    "you do not need to convert the parentheses and the commas look at the example below."
                                    "example link: https://ncase.me/loopy/v1.1/?data=[[[1,549,438,0.66,%22rabbits%22,0],[2,985,439,0.66,%22foxes%22,1]],[[2,1,153,-1,0],[1,2,160,1,0]],[[764,451,%22A%2520basic%2520ecological%250Afeedback%2520loop.%250A%250ATry%2520adding%2520extra%250Acreatures%2520to%2520this%250Aecosystem!%22],[764,244,%22more%2520rabbits%2520means%2520MORE%2520foxes%253A%250Ait%27s%2520a%2520positive%2520(%252B)%2520relationship%22],[773,648,%22more%2520foxes%2520means%2520FEWER%2520rabbits%253A%250Ait%27s%2520a%2520negative%2520(%25E2%2580%2593)%2520relationship%22],[1076,590,%22*%2520P.S%253A%2520this%2520is%2520NOT%2520the%2520%250ALotka-Volterra%2520model.%250AIt%27s%2520just%2520an%2520oscillator.%250Aclose%2520enough!%22]],2%5D"
                                    # "Now, based on the intermediate representation provided below, "
                                    # "convert it into a Loopy URL. The data should be in the following format:\n"
                                    # "1. Each node should be represented by its coordinates (x, y), initial value (init), label, and color.\n"
                                    # "2. Each edge should represent the relationship between nodes with the strength of the connection.\n"
                                    # "3. If the relationship is negative (inhibitory), encode the edge with a negative strength. \n"
                                    # "4. Format the output as a valid Loopy URL, like:\n"
                                    # "https://ncase.me/loopy/v1.1/?data=[[[1,549,438,0.66,%22rabbits%22,0],[2,985,439,0.66,%22foxes%22,1]],[[2,1,153,-1,0],[1,2,160,1,0]],[[764,451,%22A%2520basic%2520ecological%250Afeedback%2520loop.%250A%250ATry%2520adding%2520extra%250Acreatures%2520to%2520this%250Aecosystem!%22],[764,244,%22more%2520rabbits%2520means%2520MORE%2520foxes%253A%250Ait%27s%2520a%2520positive%2520(%252B)%2520relationship%22],[773,648,%22more%2520foxes%2520means%2520FEWER%2520rabbits%253A%250Ait%27s%2520a%2520negative%2520(%25E2%2580%2593)%2520relationship%22],[1076,590,%22*%2520P.S%253A%2520this%2520is%2520NOT%2520the%2520%250ALotka-Volterra%2520model.%250AIt%27s%2520just%2520an%2520oscillator.%250Aclose%2520enough!%22]],2%5D"
                                    # "Your task is to create a Loopy URL with the data provided, and return the final URL directly, with no additional text."
                                )
                            }
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "https://ncase.me/loopy/v1.1/?data="
                            }
                        ]
                    }
                ]
            )
            loopy_url = "https://ncase.me/loopy/v1.1/?data="+message.content[0].text
            return loopy_url
            # json_text = "{" + message.content[0].text
            
            # return json.loads(json_text)  # Parse JSON response
            

        except json.JSONDecodeError as e:
            print(f"[INFO]: Invalid JSON: {e}")
            return None

        except anthropic.AuthenticationError:
            print("[INFO]: Authentication failed. Check your API key.")
            return None

        except anthropic.RateLimitError:
            print("[INFO]: Rate limit exceeded. Retrying...")  # Retryable

        except anthropic.APIError as e:
            print(f"[INFO]: API error occurred: {e}")
            if "overloaded" not in str(e).lower():
                return None

        except Exception as e:
            print(f"[INFO]: Unexpected error: {e}")
            return None

        # Exponential backoff before next retry
        sleep_time = backoff_base ** attempt + random.uniform(0, 1)
        time.sleep(sleep_time)

    return None


def generate_fact_check_json_perplexity(claims: List[str], temp: float = 0.6, retries: int = 3, backoff_base: float = 1.5):
    user_prompt = (
        "Fact-check the following claims:\n\n"
        + "\n".join(f"- {c}" for c in claims) +
        "\n\nFor each claim, return:\n"
        "- claim: the original claim text\n"
        "- verdict: one of 'True', 'False', or 'Unverified'\n"
        "- explanation: short justification (1–2 sentences)\n"
        "- citations: list of up to 2 authoritative sources (title + url)\n\n"
        "Only cite trusted sources such as AWS documentation or reputable tech media.\n"
        "Do not include speculative content, forums, or community-edited sites.\n"
        "Normalize any vague dates (e.g., 'last week') into specific ones.\n"
        "Respond using the exact schema provided."
    )

    url = PERPLEXITY_API_URL
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}"}
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"schema": ClaimsResponse.model_json_schema()},
        },
        "temperature": temp,
    }

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            json_text = data["choices"][0]["message"]["content"]
            return json.loads(json_text)

        except json.JSONDecodeError as e:
            print(f"[INFO]: Invalid JSON: {e}")
            return None

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("[INFO]: Authentication failed. Check your API key.")
                return None
            elif response.status_code == 429:
                print("[INFO]: Rate limit exceeded. Retrying...")
            else:
                print(f"[INFO]: HTTP error occurred: {e}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[INFO]: Unexpected network error: {e}")
            return None

        except Exception as e:
            print(f"[INFO]: Unexpected error: {e}")
            return None

        # Retry with exponential backoff
        wait_time = backoff_base ** attempt
        print(f"[INFO]: Retrying in {wait_time:.1f} seconds...")
        time.sleep(wait_time)

    return None


# Streaming Generator Function
def stream_generate_context_json(chunks: Dict[str, str]) -> Generator[str, None, None]:
    if not isinstance(chunks, dict):
        raise TypeError("The chunks must be a dictionary.")
    
    existing_json = []
    
    for chunk_id, chunk_text in chunks.items():
        mod_input = f'Existing JSON : \n {repr(existing_json)} \n\n Transcript Input: \n {chunk_text}'
        output_json = generate_lct_json_gemini(mod_input)
        # output_json = generate_lct_json_claude(mod_input)

        if output_json is None:
            yield json.dumps(existing_json)  # Send whatever we have so far
            continue

        for item in output_json:
            item["chunk_id"] = chunk_id  # Attach chunk ID

        existing_json.extend(output_json)
        yield json.dumps(existing_json)
        time.sleep(0.5)

# saving the JSON file
# def save_json(file_name: str, chunks: dict, graph_data: dict, conversation_id: str) -> dict:
#     """
#     Saves JSON data with a UUID filename but retains the original file name for display.

#     Parameters:
#     - file_name (str): The original file name entered by the user.
#     - chunks (dict): Transcript chunks.
#     - graph_data (dict): Graph representation.

#     Returns:
#     - dict: Contains 'file_id' (UUID) and the 'file_name'.
#     """
#     try:
#         os.makedirs(SAVE_DIRECTORY, exist_ok=True)
#         if conversation_id:
#             file_id = conversation_id
#         else:
#             file_id = str(uuid.uuid4())  # Generate a UUID
#         file_path = os.path.join(SAVE_DIRECTORY, f"{file_id}.json")

#         # Save JSON data including original file_name
#         data_to_save = {
#             "file_name": file_name,  # Preserve the original file name
#             "conversation_id": conversation_id,
#             "chunks": chunks,
#             "graph_data": graph_data
#         }


#         with open(file_path, "w", encoding="utf-8") as f:
#             json.dump(data_to_save, f, indent=4)

#         return {
#             "file_id": file_id,
#             "file_name": file_name,
#             "message": f"File '{file_name}' saved successfully!"
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving JSON: {str(e)}")
    
# def save_json_to_gcs(file_name: str, chunks: dict, graph_data: list, conversation_id: str) -> dict:
#     try:
#         client = storage.Client()
#         bucket = client.bucket(GCS_BUCKET_NAME)

#         file_id = conversation_id or str(uuid.uuid4())
#         blob = bucket.blob(f"{GCS_FOLDER}/{file_id}.json")

#         data = {
#             "file_name": file_name,
#             "conversation_id": file_id,
#             "chunks": chunks,
#             "graph_data": graph_data
#         }

#         blob.upload_from_string(json.dumps(data, indent=4), content_type="application/json")

#         return {
#             "file_id": file_id,
#             "file_name": file_name,
#             "message": "Saved to GCS successfully"
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"GCS Error: {str(e)}")
    
def save_json_to_gcs(
    file_name: str,
    chunks: dict,
    graph_data: list,
    conversation_id: str = None
) -> dict:
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)

        file_id = conversation_id or str(uuid.uuid4())
        object_path = f"{GCS_FOLDER}/{file_id}.json"
        blob = bucket.blob(object_path)

        data = {
            "file_name": file_name,
            "conversation_id": file_id,
            "chunks": chunks,
            "graph_data": graph_data
        }

        blob.upload_from_string(json.dumps(data, indent=4), content_type="application/json")

        return {
            "file_id": file_id,
            "file_name": file_name,
            "message": "Saved to GCS successfully",
            "gcs_path": f"{object_path}"  # path for DB
        }

    except Exception as e:
        print(f"[FATAL] Failed to save JSON to GCS: {e}")
        raise
    
def load_conversation_from_gcs(gcs_path: str) -> dict:
    try:
        # Split GCS path into bucket and object path
        if "/" not in gcs_path:
            raise ValueError("Invalid GCS path. Must be in format 'bucket/path/to/file.json'")

        bucket_name = GCS_BUCKET_NAME
        object_path = gcs_path

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_path)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="Conversation file not found in GCS.")
        data = json.loads(blob.download_as_string())
        graph_data = data.get("graph_data")
        chunk_dict = data.get("chunks")

        if graph_data is None or chunk_dict is None:
            raise HTTPException(status_code=422, detail="Invalid conversation file structure.")

        return {
            "graph_data": graph_data,
            "chunk_dict": chunk_dict,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FATAL] GCS error loading path '{gcs_path}': {e}")
        raise HTTPException(status_code=500, detail=f"GCS error: {str(e)}")

def get_node_by_name(graph_data, node_name):
    for node in graph_data:
        if node.get("node_name") == node_name:
            return node
    return None


def convert_to_embedded(loopy_link, width=1000, height=600):

    iframe = f'<iframe width="800" height="600" frameborder="0" ' \
             f'src="{loopy_link}"></iframe>'
    try:
        return iframe
    except Exception as e:
        raise ValueError(f"Failed to convert to Loopy URL: {str(e)}")


def generate_formalism(chunks: dict, graph_data: dict, user_pref: str) -> List:
    
    formalism_list = []
    for node in graph_data[0]:
        contextual_node =''
        related_nodes = ''
        raw_text = ''
        loopy_url = None
        if 'is_contextual_progress' in node and node['is_contextual_progress']:
            contextual_node = str(node)
            for n in node['linked_nodes']:
                related_nodes += "\n" + str(get_node_by_name(graph_data[0], n))
            chunk_id = node['chunk_id']
            raw_text = chunks[chunk_id]
            
            formalism_input = f"conversation_data: \n contextual node : \n {contextual_node} \n related nodes : \n {related_nodes} \n user_research_background \n {user_pref} \n raw_text : \n {raw_text}"
            loopy_url = generate_individual_formalism(formalism_input=formalism_input)
            if loopy_url:
                # iframe_loopy_url = convert_to_embedded(loopy_url)
                formalism_list.append({
                    'formalism_node' : node['node_name'],
                    'formalism_graph_url' : loopy_url
                })
    return formalism_list

# all conversations
@lct_app.get("/conversations/", response_model=List[SaveJsonResponseExtended])
async def list_saved_conversations():
    try:
        # rows = await get_all_conversations()
        rows = get_all_conversations()
        conversations = []

        for row in rows:
            conversations.append({
                "file_id": str(row["id"]),
                "file_name": row["file_name"],
                "message": "Loaded from database",
                "no_of_nodes": row["no_of_nodes"],
                "created_at": row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else row["created_at"]
            })

        print(f"[INFO] Loaded {len(conversations)} conversations from DB")
        return conversations

    except Exception as e:
        print(f"[FATAL] Error fetching from DB: {e}")
        raise HTTPException(status_code=500, detail=f"Database access error: {str(e)}")
# def list_saved_conversations():
#     try:
#         print("[INFO] Initializing GCS client...")
#         client = storage.Client()
#         bucket = client.bucket(GCS_BUCKET_NAME)
#         print(f"[INFO] Accessing bucket: {GCS_BUCKET_NAME}")

#         blobs = bucket.list_blobs(prefix=GCS_FOLDER + "/")
#         saved_files = []
#         print(f"[INFO] Listing blobs with prefix '{GCS_FOLDER}/'")

#         for blob in blobs:
#             print(f"[DEBUG] Found blob: {blob.name}")
#             if not blob.name.endswith(".json"):
#                 print(f"[SKIP] Skipping non-JSON file: {blob.name}")
#                 continue

#             try:
#                 print(f"[INFO] Downloading blob: {blob.name}")
#                 content = blob.download_as_string()
#                 data = json.loads(content)

#                 conversation_id = data.get("conversation_id")
#                 file_name = data.get("file_name")
#                 graph_data = data.get("graph_data", [])

#                 no_of_nodes = len(graph_data[0]) if graph_data and isinstance(graph_data[0], list) else 0

#                 if not conversation_id or not file_name:
#                     raise ValueError("Missing required fields in JSON file.")
                
#                 created_at = blob.time_created.isoformat() if blob.time_created else None

#                 saved_files.append({
#                     "file_id": conversation_id,
#                     "file_name": file_name,
#                     "message": "Loaded from GCS",
#                     "no_of_nodes": no_of_nodes,
#                     "created_at": created_at
#                 })
#                 print(f"[SUCCESS] Loaded conversation: {conversation_id} - {file_name}")

#             except Exception as file_error:
#                 print(f"[ERROR] Error reading {blob.name}: {file_error}")
#                 continue

#         print(f"[INFO] Total conversations loaded: {len(saved_files)}")
#         return saved_files

#     except Exception as e:
#         print(f"[FATAL] Unexpected error in /conversations/: {e}")
#         raise HTTPException(status_code=500, detail=f"GCS access error: {str(e)}")
  
# get individual conversations 
@lct_app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    try:
        # gcs_path = await get_conversation_gcs_path(conversation_id)
        gcs_path = get_conversation_gcs_path(conversation_id)
        if not gcs_path:
            raise HTTPException(status_code=404, detail="Conversation metadata not found in DB.")

        return load_conversation_from_gcs(gcs_path)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FATAL] Error loading conversation '{conversation_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") 
# @lct_app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
# def get_conversation(conversation_id: str):
#     try:
#         client = storage.Client()
#         bucket = client.bucket(GCS_BUCKET_NAME)
#         blob_path = f"{GCS_FOLDER}/{conversation_id}.json"
#         print(f"bucket: {bucket}, blob: {blob_path}")
#         blob = bucket.blob(blob_path)

#         if not blob.exists():
#             raise HTTPException(status_code=404, detail="Conversation not found in GCS.")

#         data = json.loads(blob.download_as_string())

#         graph_data = data.get("graph_data")
#         chunk_dict = data.get("chunks")

#         if graph_data is None or chunk_dict is None:
#             raise HTTPException(status_code=422, detail="Invalid conversation file structure.")

#         return {
#             "graph_data": graph_data,
#             "chunk_dict": chunk_dict,
#         }

#     except HTTPException:
#         raise

#     except Exception as e:
#         print(f"[FATAL] Error fetching {conversation_id} from GCS: {e}")
#         raise HTTPException(status_code=500, detail=f"GCS error: {str(e)}")
    
    
# Endpoint to get transcript chunks
@lct_app.post("/get_chunks/", response_model=ChunkedTranscript)
async def get_chunks(request: TranscriptRequest):
    try:
        transcript = request.transcript

        if not transcript:
            raise HTTPException(status_code=400, detail="Transcript must be a non-empty string.")

        chunks = sliding_window_chunking(transcript)

        if not chunks:
            raise HTTPException(status_code=500, detail="Chunking failed. No chunks were generated.")

        return ChunkedTranscript(chunks=chunks)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Streaming Endpoint for JSON generation
@lct_app.post("/generate-context-stream/")
async def generate_context_stream(request: ChunkedRequest):
    try:
        chunks = request.chunks

        if not chunks or not isinstance(chunks, dict):
            raise HTTPException(status_code=400, detail="Chunks must be a non-empty dictionary.")

        return StreamingResponse(stream_generate_context_json(chunks), media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@lct_app.post("/save_json/", response_model=SaveJsonResponse)
async def save_json_call(request: SaveJsonRequest):
    """
    FastAPI route to save JSON data and insert metadata into the DB.
    """
    try:
        # Validate input
        if not request.file_name.strip():
            raise HTTPException(status_code=400, detail="File name cannot be empty.")

        if not isinstance(request.chunks, dict) or not isinstance(request.graph_data, list):
            raise HTTPException(status_code=400, detail="Chunks must be a valid dictionary and Graph Data must be a valid list.")

        try:
            result = save_json_to_gcs(
                request.file_name,
                request.chunks,
                request.graph_data,
                request.conversation_id
            )
        except Exception as file_error:
            raise HTTPException(status_code=500, detail=f"File saving error: {str(file_error)}")

        # Insert metadata into DB
        number_of_nodes = len(request.graph_data[0]) if request.graph_data and isinstance(request.graph_data[0], list) else 0
        print("graph data check: ", request.graph_data)
        print("number of nodes: ", len(request.graph_data[0]) if request.graph_data and isinstance(request.graph_data[0], list) else 0)
        metadata = {
            "id": result["file_id"],
            "file_name": result["file_name"],
            "no_of_nodes": number_of_nodes,
            "gcs_path": result["gcs_path"],
            "created_at": datetime.utcnow()
        }

        # await insert_conversation_metadata(metadata)
        insert_conversation_metadata(metadata)

        return result

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
# @lct_app.post("/save_json/", response_model=SaveJsonResponse)
# async def save_json_call(request: SaveJsonRequest):
#     """
#     FastAPI route to save JSON data using an external function.
#     """
#     try:
#         # Validate input data
#         if not request.file_name.strip():
#             raise HTTPException(status_code=400, detail="File name cannot be empty.")

#         if not isinstance(request.chunks, dict) or not isinstance(request.graph_data, List):
#             raise HTTPException(status_code=400, detail="Chunks must be a valid dictionary and Graph Data must be a valid list.")
#         try:
#             # result = save_json(request.file_name, request.chunks, request.graph_data, request.conversation_id) # save json function
#             result = save_json_to_gcs(request.file_name, request.chunks, request.graph_data, request.conversation_id) # save json function
#         except Exception as file_error:
#             raise HTTPException(status_code=500, detail=f"File saving error: {str(file_error)}")

#         return result

#     except HTTPException as http_err:
#         raise http_err  # Re-raise HTTP exceptions as they are

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@lct_app.post("/generate_formalism/", response_model=generateFormalismResponse)
async def generate_formalism_call(request: generateFormalismRequest):
    try:
        # Validate input data
        if not isinstance(request.chunks, dict) or not isinstance(request.graph_data, List):
            raise HTTPException(status_code=400, detail="Chunks must be a valid dictionary and Graph Data must be a valid list.")
        try:
            result = generate_formalism(request.chunks, request.graph_data, request.user_pref) # save json function
        except Exception as formalism_error:
            print(f"[INFO]: Formalism Generation error: {formalism_error}")
            raise HTTPException(status_code=500, detail=f"Formalism Generation error: {str(formalism_error)}")

        return {"formalism_data": result}

    except HTTPException as http_err:
        raise http_err  # Re-raise HTTP exceptions as they are

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@lct_app.websocket("/ws/audio")
async def websocket_audio_endpoint(client_websocket: WebSocket):

    shared_state = {
                    "accumulator": [],
                    "existing_json": [],
                    "chunk_dict": {},
                }
    
    async def should_continue_processing(text_batch, stop_accumulating_flag= False):
        # Replace with your actual decision logic or API call
        input_text = ' '.join(text_batch)
        # contextually complete chunk
        accumulated_output = genai_accumulate_text_json(input_text)
        if not accumulated_output:
            print("[INFO]: Failed to accumulate; defaulting to continue accumulating.")
            return True, ' '.join(text_batch)  # return as if still incomplete

        if not stop_accumulating_flag:
            segmented_input_chunk = accumulated_output.get('Completed_segment', '')
            incomplete_seg = accumulated_output.get('Incomplete_segment', '')

        # print(f'accumulated output: {accumulated_output}')
            
        decision_flag = accumulated_output.get("decision", "continue_accumulating")
        if decision_flag == 'continue_accumulating':
            decision = True
        elif decision_flag == 'stop_accumulating':
            decision = False
        else:
            print(f"[INFO]: Unexpected decision_flag: {decision_flag}")
            decision = True
            
        if stop_accumulating_flag:
            decision = False
            segmented_input_chunk = ' '.join(text_batch)
            incomplete_seg= ''
        
        print(f"[INFO]: segmented input: {segmented_input_chunk}")
        print(f"[INFO]: detected threads: {accumulated_output['detected_threads']}")
        
        #sending graph stuff to front end
        if segmented_input_chunk.strip():
            mod_input = f'Existing JSON : \n {repr(shared_state["existing_json"])} \n\n Transcript Input: \n {segmented_input_chunk}'
            output_json = generate_lct_json_gemini(mod_input)
            # output_json = generate_lct_json_claude(mod_input)

            if output_json:
                chunk_id = str(uuid.uuid4())
                shared_state["chunk_dict"][chunk_id] = segmented_input_chunk
                for item in output_json:
                    item["chunk_id"] = chunk_id

                shared_state["existing_json"].extend(output_json)

                # 🔁 Send it to frontend live
                await client_websocket.send_text(json.dumps({
                    "type": "existing_json",
                    "data": [shared_state["existing_json"]]
                }))
                print("[CLIENT WS] Sent message to client: type=existing_json")
                
                await asyncio.sleep(0.02)  # 20ms pause
                
                await client_websocket.send_text(json.dumps({
                    "type": "chunk_dict",
                    "data": shared_state["chunk_dict"]
                }))
                print("[CLIENT WS] Sent message to client: type=chunk_dict")

        print(f"[INFO]: Evaluated batch of {len(text_batch)} transcripts...")
        return decision, incomplete_seg
        
    async def receive_from_client(client_websocket, aai_ws, shared_state):
        while True:
            try:
                message = await client_websocket.receive()

                if "bytes" in message:
                    print("[CLIENT WS] Receiving audio...")
                    # This is binary audio data
                    print("[AAI WS] Sending audio to AssemblyAI...")
                    pcm_data = message["bytes"]
                    await aai_ws.send(pcm_data)

                elif "text" in message:
                    print("[CLIENT WS] Received control message:", message["text"])
                    # This is a JSON control message
                    try:
                        msg = json.loads(message["text"])
                        
                        #client log
                        if msg.get("type") == "client_log":
                            print(f"[INFO]: [Client Log] {msg['message']}")
                            
                        # if msg.get("type") == "ping":
                        #     print("recieved ping")
                            # return 
        
                        # final flush
                        if msg.get("final_flush"):
                            print("[INFO]: Final flush requested by client.")
                            if shared_state["accumulator"]:
                                try:
                                    await should_continue_processing(shared_state["accumulator"], stop_accumulating_flag=True)
                                    shared_state["accumulator"].clear()
                                except Exception as e:
                                    print(f"[INFO]: Error during final flush: {e}")
                                    await client_websocket.send_text(json.dumps({
                                        "type": "error",
                                        "detail": f"Flush failed: {str(e)}"
                                    }))

                            await client_websocket.send_text(json.dumps({ "type": "flush_ack" }))
                            print("[INFO]: Flush ack sent, sleeping briefly...")
                            await asyncio.sleep(0.5)
                            print("[INFO]: Closing websocket now.")
                            await client_websocket.close(code=1000)
                            return
                    except Exception as e:
                        print(f"[INFO]: Invalid JSON message from client: {e}")

            except WebSocketDisconnect:
                print("[INFO]: WebSocket client disconnected.")
                break
            
            except Exception as e:
                print(f"[INFO]: Error receiving from client: {e}")
                raise
        
    async def receive_from_assemblyai(aai_ws, client_websocket, shared_state):
        batch_size = BATCH_SIZE
        continue_accumulating = True
        while True:
            try:
                msg = await aai_ws.recv()
                msg = json.loads(msg)
                msg_type = msg.get("message_type")

                if msg_type == "SessionBegins":
                    print("[INFO]: AssemblyAI session started:", msg.get("session_id"))

                # elif msg_type == "PartialTranscript":
                #     print(msg.get("text", ""), end="\r")

                elif msg_type == "FinalTranscript":
                    final_text = msg.get("text", "")
                    # print(final_text)

                    if final_text:
                        shared_state['accumulator'].append(final_text)

                    if len(shared_state['accumulator']) >= batch_size and continue_accumulating:
                        # Evaluate current batch
                        continue_accumulating, incomplete_seg = await should_continue_processing(shared_state['accumulator'])

                        if continue_accumulating:
                            if batch_size >= MAX_BATCH_SIZE:
                                print("[INFO]: Batch size limit reached. Forcing segmentation.")
                                continue_accumulating, incomplete_seg = await should_continue_processing(shared_state['accumulator'], stop_accumulating_flag=True)
                                
                                shared_state['accumulator'] = [] # Reset accumulator
                                batch_size = BATCH_SIZE  # Reset batch size
                                continue_accumulating = True  # Restart accumulation
                                # print(f"shared_state accumulator  {shared_state['accumulator']}")
                            else:
                                batch_size += BATCH_SIZE 
                        else:
                            # Send batch and reset
                            # print(f"Batch sent and accumulator reset: {shared_state['accumulator']}")
                            if incomplete_seg:
                                shared_state['accumulator'] = [incomplete_seg]
                            else:
                                shared_state['accumulator'] = []
                            batch_size = BATCH_SIZE  # Reset batch size
                            continue_accumulating = True  # Restart accumulation

                elif msg_type == "error":
                    error_msg = msg.get("error", "Unknown error")
                    print("[INFO]: AssemblyAI error:", error_msg)
                    await client_websocket.send_text(json.dumps({
                        "type": "error",
                        "detail": f"AssemblyAI error: {error_msg}"
                    }))
                    return 
            # except ConnectionClosedError:
            #     print("AssemblyAI WebSocket closed.")
            #     break
            except Exception as e:
                print(f"[INFO]: Error receiving from AssemblyAI: {e}")
                raise


    try:
        await client_websocket.accept()
        print("[CLIENT WS] WebSocket connection accepted")
        
        for attempt in range(3):
            print(f"[AAI WS] Attempt {attempt + 1}/3: Connecting to AssemblyAI...")
            try:
                async with websockets.connect(
                    ASSEMBLYAI_WS_URL,
                    additional_headers={"Authorization": ASSEMBLYAI_API_KEY}
                ) as aai_ws:
                    print("[AAI WS] Connected to AssemblyAI")
                    
                    

                    tasks = [
                        asyncio.create_task(receive_from_client(client_websocket, aai_ws, shared_state)),
                        asyncio.create_task(receive_from_assemblyai(aai_ws, client_websocket, shared_state))
                    ]

                    try:
                        await asyncio.gather(*tasks)
                    except asyncio.CancelledError:
                        print("[CLIENT WS] WebSocket tasks cancelled due to session shutdown")
                        raise
                    finally:
                        for task in tasks:
                            task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                        print("[CLIENT WS] All tasks cleaned up")

            except ConnectionClosedError as aai_err:
                print(f"[AAI WS] Connection closed unexpectedly: {aai_err}")
            except Exception as aai_err:
                print(f"[AAI WS] Error during setup: {aai_err}")
                await asyncio.sleep(1)
        
        else:
            await client_websocket.send_text(json.dumps({
                "type": "error",
                "detail": "Could not connect to transcription service"
            }))
            await asyncio.sleep(0.5)
            await client_websocket.close(code=1011)
            print("[CLIENT WS] Max retries reached. Closing client socket.")

    except asyncio.CancelledError:
        print("[CLIENT WS] WebSocket handler cancelled during shutdown")
    except Exception as e:
        print(f"[CLIENT WS] Unexpected error in WebSocket handler: {e}")
        
@lct_app.post("/fact_check_claims/", response_model=ClaimsResponse)
async def fact_check_claims_call(request: FactCheckRequest):
    try:
        if not request.claims:
            raise HTTPException(status_code=400, detail="No claims provided.")

        result = generate_fact_check_json_perplexity(request.claims)
        if result is None:
            raise HTTPException(status_code=500, detail="Fact-checking service failed.")
        
        return result

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Serve index.html at root
# @lct_app.get("/")
# def read_root():
#     return FileResponse("frontend_dist/index.html")

# # Serve favicon or other top-level static files
# @lct_app.get("/favicon.ico")
# def favicon():
#     file_path = "frontend_dist/favicon.ico"
#     if os.path.exists(file_path):
#         return FileResponse(file_path)
#     return {}

# # Catch-all for SPA routes (NOT static files)
# @lct_app.get("/{full_path:path}")
# async def spa_router(full_path: str):
#     file_path = f"frontend_dist/{full_path}"
#     if os.path.exists(file_path):
#         return FileResponse(file_path)
#     return FileResponse("frontend_dist/index.html")


# @lct_app.post("/save_fact_check/")
# async def save_fact_check_call(request: SaveFactCheckRequest):
#     try:
#         # Serialize the fact_check_data to a JSON string
#         results_json = json.dumps([r.dict() for r in request.fact_check_data])
        
#         await save_fact_check_results(request.conversation_id, request.node_name, results_json)
        
#         return {"message": "Fact-check results saved successfully."}
    
#     except Exception as e:
#         print(f"[FATAL] Error saving fact-check data: {e}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# @lct_app.get("/get_fact_check/{conversation_id}/{node_name}", response_model=GetFactCheckResponse)
# async def get_fact_check_call(conversation_id: str, node_name: str):
#     try:
#         results_data = await get_fact_check_results(conversation_id, node_name)
        
#         if results_data is not None:
#             return {"results": results_data}
        
#         # If no record is found, return an empty list of results
#         return {"results": []}

#     except Exception as e:
#         print(f"[FATAL] Error fetching fact-check data: {e}")
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")