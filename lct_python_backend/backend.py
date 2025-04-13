import anthropic
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
from typing import Dict, Generator, List
import uuid

# Directory to save JSON files
SAVE_DIRECTORY = "../saved_json"

# fastapi app
lct_app = FastAPI()

# Configure CORS
lct_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow requests from Vite frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

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

class StreamedResponse(BaseModel):
    data: List[ProcessedChunk]

class SaveJsonRequest(BaseModel):
    file_name: str
    chunks: dict
    graph_data: List

class SaveJsonResponse(BaseModel):
    message: str
    file_id: str  # UUID of the saved file
    file_name: str  # Original file name provided by the user

# Function to chunk the text
def sliding_window_chunking(text: str, chunk_size: int = 2000, overlap: int = 400) -> Dict[str, str]:
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

# Function to generate JSON using Claude
def generate_lct_json(transcript: str, temp: float = 0.6):
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=8192,
            temperature=temp,
            system="You are an advanced AI model that structures conversations into strictly JSON-formatted nodes. Each conversational shift should be captured as a new node with defined relationships.\n\nFormatting Rules:\n\nInstructions:\n\nHandling New JSON Creation\nExtract Key Nodes: Identify all topic shifts in the conversation. Each topic shift forms a new \"node\", even if the topic was discussed earlier.\n\nStrictly Generate JSON Output:\n[\n  {\n    \"node_name\": \"Title of the conversational thread\",\n    \"type\": \"conversational_thread\" or \"bookmark\",\n    \"predecessor\": \"Previous node name\",\n    \"successor\": \"Next node name\",\n    \"contextual_relation\": {\n      \"Related Node 1\": \"Detailed explanation of how this node's context is used\",\n      \"Related Node 2\": \"Another detailed explanation\",\n      \"...\": \"Additional related nodes with their respective explanations can be included as needed\"\n    },\n    \"linked_nodes\": [\n      \"List of all nodes this node is either drawing context from or providing context to\"\n    ],\n    \"chunk_id\": null,  // This field will be **ignored** for now and will be added externally.\n    \"is_bookmark\": true or false,\n    \"is_formalism\": true or false,\n    \"summary\": \"Detailed description of what was discussed in this node.\"\n  }\n]\n\nDefine Structure:\n\"predecessor\" → The direct previous node.\n\"successor\" → The direct next node.\n\"contextual_relation\" → Use this to explain how past nodes contribute to the current discussion.\nKeys = node names that contribute context.\nValues = a detailed explanation of how the multiple referenced nodes influence the current discussion.\n\n\"linked_nodes\" → A comprehensive list of all nodes this node is either drawing context from or providing context to, this information of context providing will come from “contextual_relation”, consolidating references into a single field.\n\"chunk_id\" → This field will be ignored for now, as it will be added externally by the code.\n\nHandling Updates to Existing JSON\nIf an existing JSON structure is provided along with the transcript , modify it as follows and Strictly return only the nodes generated for the current input transcript:\n\nContinuing a topic: If the conversation continues an existing discussion, update the “successor” field of the last relevant node.\nNew topic: If a conversation introduces a new topic, create a new node and properly link it.\nRevisiting a Bookmark:\nIf \"LLM wish bookmark open [name]\" appears, find the existing bookmark node and update its \"contextual_relation\" and \"linked_nodes\".\nDo NOT create a new bookmark when revisited—update the existing one instead.\nContextual Relation Updates:\nMaintain indirect connections (e.g., a previous conversation influencing the new one).\nEnsure logical flow between past and present discussions.\n\n\nChronology, Contextual Referencing and Bookmarking\nIf a topic is revisited, create a new node while ensuring proper linking to previous mentions.\nEnsure mutual linking between nodes that provide context to each other. If a node references a past discussion, ensure the past node also updates its \"linked_nodes\" to include the new node.\n\n\nConversational Threads nodes (type: \"conversational_thread\"):\nEvery topic shift must be captured as a new node.\nEach node must include both \"predecessor\" and \"successor\" fields to maintain chronological flow.\n\"contextual_relation\" must explain how previous discussions contribute to the current conversation.\n\"linked_nodes\" must track all nodes this node is either drawing context from or providing context to in a single list.\nFor nodes with type=\"conversational_thread\", always set \"is_bookmark\": false.\nHandling Revisited Topics:\nIf a conversation returns to a previously discussed topic, create a new node instead of merging with an existing one.\nEnsure \"contextual_relation\" references past discussions of the same topic, explaining their relevance in the current context.\nBookmark nodes (type: \"bookmark\") must:\nA bookmark node must be created when \"LLM wish bookmark create\" appears, capturing the contextually relevant topic.\n\"contextual_relation\" must reference the exact nodes where the bookmark was created and opened, ensuring contextual continuity.\nThe summary should clearly describe the reason for creating the bookmark and what it aims to track.\nIf \"LLM wish bookmark open\" appears, do not create a new bookmark—update the existing one.\nModify \"contextual_relation\" to include the new node where the bookmark was accessed, ensuring that past discussions remain linked.\nProvide a clear explanation of how the revisited discussion builds on the previously stored context.\nFor nodes with type=\"bookmark\", always set \"is_bookmark\": true.\nFormalism Capture (\"is_formalism\": true)\nIf \"LLM wish capture formalism\" appears, update the existing node (either \"conversational_thread\" or \"bookmark\") to include:\n\"is_formalism\": true\"\nFormalism capture is used when the conversation contains a structured reasoning approach, causal diagrams description, or informal discussions that construct a conceptual model.\nDo not create a new node for formalism capture. Instead, apply the flag to the relevant existing node where the formal concept was introduced or referenced.\n\nContextual Relation & Linked Nodes Updates:\n\"contextual_relation\" must explain why past discussions are relevant, ensuring clarity in topic evolution.\n\"linked_nodes\" must include all references in a single list, capturing all nodes this node draws from or informs.\nThe structure of \"predecessor\", \"successor\", and \"contextual_relation\" must ensure logical and chronological consistency between past and present discussions.\n\nExample Input (Conversation with Bookmark Spells):\nExisting JSON:\n\nTranscript:\nAlex: Hey Jordan, summer’s coming up. We should totally go on a road trip!\nJordan: That sounds awesome! But road trips can get expensive. Gas, food, places to stay… It all adds up.\nAlex: True, but we can budget it out. If we book some places early and plan food stops, we might save some cash.\nJordan: Yeah, maybe we can also stay at some cheap motels or even camp for a few nights.\nAlex: Exactly. I’ll make a list of potential stops and places to sleep.\nAlex: LLM wish bookmark create Road Trip Planning.\nJordan: Speaking of planning, I’ve been trying to fix my sleep schedule. Finals completely messed it up.\nAlex: Oh yeah, I feel you. When people get stressed, they sleep less, which makes them even more stressed, and then they sleep even less.\nJordan: Yep, and then when you add caffeine into the mix, it just makes things worse. I was practically running on energy drinks.\nAlex: Not to mention, when you’re sleep-deprived, you tend to eat worse, and bad eating can also make it harder to sleep. It’s like everything is connected.\nJordan: So basically, when you’re stressed, you don’t sleep enough. Then because you don’t sleep, you get more stressed, and things like caffeine and bad eating habits just make the whole situation even worse.\nAlex: Exactly. But the good news is that breaking just one part of the cycle—like cutting down on caffeine or trying to fix your sleep schedule—can help stop everything from spiraling out of control.\nJordan: Makes sense. I guess I need to start by drinking less caffeine.\nAlex: Yeah, and maybe try doing something relaxing before bed, like listening to music or reading instead of staring at your phone.\nJordan: LLM wish capture formalism Stress-Sleep Cycle.\nAlex: Anyway, did you hear about that new horror movie coming out next month?\nJordan: Oh, yeah! It looks terrifying. I love a good horror flick.\nAlex: We should totally watch it when it releases.\nJordan: Definitely. But no watching it late at night—I’ll never get any sleep.\nAlex: Haha, fair enough.\nJordan: Oh, by the way, about that road trip—do you think we should rent a car or use mine?\nAlex: Good question. Your car is solid, but renting might save us some trouble if we’re going really far.\nJordan: Yeah, plus, rentals come with insurance, which could be helpful.\nAlex: LLM wish bookmark open Road Trip Planning.\nJordan: Right, so we need to decide if we’re driving your car or renting, and we should check gas prices along the way.\nAlex: Yep, and maybe look at rental deals. I’ll compare some prices later.\nJordan: Sounds good. Let’s lock in a plan soon!\n\n\nExample JSON Output:\n[\n  {\n    \"node_name\": \"Road Trip Planning\",\n    \"type\": \"bookmark\",\n    \"predecessor\": null,\n    \"successor\": \"Fixing Sleep Schedules and Stress\",\n    \"contextual_relation\": {},\n    \"linked_nodes\": [\n      \"Fixing Sleep Schedules and Stress\",\n      \"Road Trip Planning - Car Rental Discussion\"\n    ],\n    \"chunk_id\": null,\n    \"is_bookmark\": true,\n    \"is_formalism\": false,\n    \"summary\": \"Alex and Jordan discuss planning a summer road trip, acknowledging budget concerns. They decide to save money by booking accommodations early, staying at cheap motels, and camping. Alex plans to make a list of potential stops and sleeping arrangements.\"\n  },\n  {\n    \"node_name\": \"Fixing Sleep Schedules and Stress\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Road Trip Planning\",\n    \"successor\": \"Horror Movie Discussion\",\n    \"contextual_relation\": {\n      \"Road Trip Planning\": \"The transition from road trip planning to discussing sleep schedules happens naturally as Jordan mentions finals disrupting their sleep.\"\n    },\n    \"linked_nodes\": [\n      \"Road Trip Planning\",\n      \"Horror Movie Discussion\"\n    ],\n    \"chunk_id\": null,\n    \"is_bookmark\": false,\n    \"is_formalism\": true,\n    \"summary\": \"Jordan mentions their sleep schedule being disrupted due to finals, leading to a discussion on stress and sleep deprivation. They explore how stress, caffeine, and bad eating habits contribute to a negative cycle and discuss ways to break it, such as reducing caffeine intake and establishing a better nighttime routine.\"\n  },\n  {\n    \"node_name\": \"Horror Movie Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Fixing Sleep Schedules and Stress\",\n    \"successor\": \"Road Trip Planning - Car Rental Discussion\",\n    \"contextual_relation\": {\n      \"Fixing Sleep Schedules and Stress\": \"The discussion transitions from sleep issues to horror movies, as Jordan jokes about avoiding horror films at night to prevent sleep loss.\"\n    },\n    \"linked_nodes\": [\n      \"Fixing Sleep Schedules and Stress\",\n      \"Road Trip Planning - Car Rental Discussion\"\n    ],\n    \"chunk_id\": null,\n    \"is_bookmark\": false,\n    \"is_formalism\": false,\n    \"summary\": \"Alex and Jordan discuss an upcoming horror movie. Jordan expresses excitement but jokes about avoiding late-night viewing to prevent sleep issues.\"\n  },\n  {\n    \"node_name\": \"Road Trip Planning - Car Rental Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Horror Movie Discussion\",\n    \"successor\": null,\n    \"contextual_relation\": {\n      \"Road Trip Planning\": \"The conversation returns to road trip planning as Jordan revisits the topic, prompting discussions about using a personal car versus renting one.\",\n      \"Horror Movie Discussion\": \"The transition occurs naturally as Alex and Jordan shift from casual movie talk back to logistics for their trip.\"\n    },\n    \"linked_nodes\": [\n      \"Road Trip Planning\",\n      \"Horror Movie Discussion\",\n      \"Fixing Sleep Schedules and Stress\"\n    ],\n    \"chunk_id\": null,\n    \"is_bookmark\": false,\n    \"is_formalism\": false,\n    \"summary\": \"Jordan brings the conversation back to the road trip, specifically whether to rent a car or use a personal vehicle. They consider factors like gas prices and rental insurance before agreeing to compare rental deals.\"\n  }\n]\n",
            messages=[
                {"role": "user", "content": [{"type": "text", "text": transcript}]},
                {"role": "assistant", "content": [{"type": "text", "text": "[\n{"}]}
            ]
        )

        json_text = "[\n{" + message.content[0].text
        return json.loads(json_text)  # Parse JSON response

    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
    except anthropic.AuthenticationError:
        print("Authentication failed. Check your API key.")
    except anthropic.RateLimitError:
        print("Rate limit exceeded. Try again later.")
    except anthropic.APIError as e:
        print(f"API error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None

# Streaming Generator Function
def stream_generate_context_json(chunks: Dict[str, str]) -> Generator[str, None, None]:
    if not isinstance(chunks, dict):
        raise TypeError("The chunks must be a dictionary.")
    
    existing_json = []
    
    for chunk_id, chunk_text in chunks.items():
        mod_input = f'Existing JSON : \n {repr(existing_json)} \n\n Transcript Input: \n {chunk_text}'
        output_json = generate_lct_json(mod_input)

        if output_json is None:
            yield json.dumps(existing_json)  # Send whatever we have so far
            continue

        for item in output_json:
            item["chunk_id"] = chunk_id  # Attach chunk ID

        existing_json.extend(output_json)
        yield json.dumps(existing_json)
        time.sleep(0.5)

# saving the JSON file
def save_json_to_file(file_name: str, chunks: dict, graph_data: dict) -> dict:
    """
    Saves JSON data with a UUID filename but retains the original file name for display.

    Parameters:
    - file_name (str): The original file name entered by the user.
    - chunks (dict): Transcript chunks.
    - graph_data (dict): Graph representation.

    Returns:
    - dict: Contains 'file_id' (UUID) and the 'file_name'.
    """
    try:
        os.makedirs(SAVE_DIRECTORY, exist_ok=True)
        
        file_id = str(uuid.uuid4())  # Generate a UUID
        file_path = os.path.join(SAVE_DIRECTORY, f"{file_id}.json")

        # Save JSON data including original file_name
        data_to_save = {
            "file_name": file_name,  # Preserve the original file name
            "chunks": chunks,
            "graph_data": graph_data
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)

        return {
            "file_id": file_id,
            "file_name": file_name,
            "message": f"File '{file_name}' saved successfully!"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving JSON: {str(e)}")

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
async def save_json(request: SaveJsonRequest):
    """
    FastAPI route to save JSON data using an external function.
    """
    try:
        # Validate input data
        if not request.file_name.strip():
            raise HTTPException(status_code=400, detail="File name cannot be empty.")

        if not isinstance(request.chunks, dict) or not isinstance(request.graph_data, List):
            raise HTTPException(status_code=400, detail="Chunks must be a valid dictionary and Graph Data must be a valid list.")
        try:
            result = save_json_to_file(request.file_name, request.chunks, request.graph_data) # save json function
        except Exception as file_error:
            raise HTTPException(status_code=500, detail=f"File saving error: {str(file_error)}")

        return result

    except HTTPException as http_err:
        raise http_err  # Re-raise HTTP exceptions as they are

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")