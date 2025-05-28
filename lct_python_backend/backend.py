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
import random

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

class SaveJsonRequest(BaseModel):
    file_name: str
    chunks: dict
    graph_data: List

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
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
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
            
        except anthropic.AuthenticationError:
            print("Authentication failed. Check your API key.")
            break  # Auth errors are not recoverable
        except anthropic.RateLimitError:
            print("Rate limit exceeded. Retrying...")
        except anthropic.APIError as e:
            print(f"API error occurred: {e}")
            if "overloaded" not in str(e).lower():
                break  # Only retry if it's overload-related
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        # Exponential backoff before next retry
        sleep_time = backoff_base ** attempt + random.uniform(0, 1)
        time.sleep(sleep_time)

    return None

# Function to generate JSON using Claude
def generate_lct_json(transcript: str, temp: float = 0.6, retries: int = 5, backoff_base: float = 1.5):
    generate_lct_prompt = "You are an advanced AI model that structures conversations into strictly JSON-formatted nodes. Each conversational shift should be captured as a new node with defined relationships.\n\nFormatting Rules:\n\nInstructions:\n\nHandling New JSON Creation\nExtract Key Nodes: Identify all topic shifts in the conversation. Each topic shift forms a new \"node\", even if the topic was discussed earlier.\n\nStrictly Generate JSON Output:\n[\n  {\n    \"node_name\": \"Title of the conversational thread\",\n    \"type\": \"conversational_thread\" or \"bookmark\",\n    \"predecessor\": \"Previous node name\",\n    \"successor\": \"Next node name\",\n    \"contextual_relation\": {\n      \"Related Node 1\": \"Detailed explanation of how this node's context is used\",\n      \"Related Node 2\": \"Another detailed explanation\",\n      \"...\": \"Additional related nodes with their respective explanations can be included as needed\"\n    },\n    \"linked_nodes\": [\n      \"List of all nodes this node is either drawing context from or providing context to\"\n    ],\n    \"chunk_id\": None,  // This field will be **ignored** for now and will be added externally.\n    \"is_bookmark\": True or False,\n    \"\"is_contextual_progress\": True or False,\n    \"summary\": \"Detailed description of what was discussed in this node.\"\n  }\n]\n\nDefine Structure:\n\"predecessor\" → The direct previous node.\n\"successor\" → The direct next node.\n\"contextual_relation\" → Use this to explain how past nodes contribute to the current discussion contextually.\nKeys = node names that contribute context.\nValues = a detailed explanation of how the multiple referenced nodes influence the current discussion.\n\n\"linked_nodes\" → A comprehensive list of all nodes this node is either drawing context from or providing context to, this information of context providing will come from “contextual_relation”, consolidating references into a single field.\n\"chunk_id\" → This field will be ignored for now, as it will be added externally by the code.\n\nHandling Updates to Existing JSON\nIf an existing JSON structure is provided along with the transcript , modify it as follows and Strictly return only the nodes generated for the current input transcript:\n\nContinuing a topic: If the conversation continues an existing discussion, update the “successor” field of the last relevant node.\nNew topic: If a conversation introduces a new topic, create a new node and properly link it.\nRevisiting a Bookmark:\nIf \"LLM wish bookmark open [name]\" appears, find the existing bookmark node and update its \"contextual_relation\" and \"linked_nodes\".\nDo NOT create a new bookmark when revisited—update the existing one instead.\nContextual Relation Updates:\nMaintain indirect connections (e.g., a previous conversation influencing the new one).\nEnsure logical flow between past and present discussions.\n\n\nChronology, Contextual Referencing and Bookmarking\nIf a topic is revisited, create a new node while ensuring proper linking to previous mentions.\nEnsure mutual linking between nodes that provide context to each other. If a node references a past discussion, ensure the past node also updates its \"linked_nodes\" to include the new node.\n\n\nConversational Threads nodes (type: \"conversational_thread\"):\nEvery topic shift must be captured as a new node.\nEach node must include both \"predecessor\" and \"successor\" fields to maintain chronological flow.\n\"contextual_relation\" must explain how previous discussions contribute to the current conversation.\n\"linked_nodes\" must track all nodes this node is either drawing context from or providing context to in a single list.\nFor nodes with type=\"conversational_thread\", always set \"is_bookmark\": False.\nHandling Revisited Topics:\nIf a conversation returns to a previously discussed topic, create a new node instead of merging with an existing one.\nEnsure \"contextual_relation\" references past discussions of the same topic, explaining their relevance in the current context.\nBookmark nodes (type: \"bookmark\") must:\nA bookmark node must be created when \"LLM wish bookmark create\" appears, capturing the contextually relevant topic.\nDo not create bookmark node unless the phrase “LLM wish bookmark create” is mentioned.\n\"contextual_relation\" must reference the exact nodes where the bookmark was created and opened, ensuring contextual continuity.\nThe summary should clearly describe the reason for creating the bookmark and what it aims to track.\nIf \"LLM wish bookmark open\" appears, do not create a new bookmark—update the existing one.\nModify \"contextual_relation\" to include the new node where the bookmark was accessed, ensuring that past discussions remain linked.\nProvide a clear explanation of how the revisited discussion builds on the previously stored context.\nFor nodes with type=\"bookmark\", always set \"is_bookmark\": True.\n\nContextual Progress Capture (\"is_contextual_progress\": True)\nOnly If  the whole phrase \"LLM wish capture contextual progress\" appears, update the existing node (either \"conversational_thread\" or \"bookmark\") to include:\n\"is_contextual_progress\": True\nContextual progress capture is used to capture a potential insight that might be present in that conversational node. \nIt represents part of the conversation that could potentially be an insight that could be useful. These \"potential insights\" are the directions provided by humans that can later be taken by AI, which then uses this to generate formalisms.\nDo not create a new node for contextual progress capture. Instead, apply the flag to the relevant existing node where the potential insight was introduced or referenced.\n\nContextual Relation & Linked Nodes Updates:\n\"contextual_relation\" must explain why past discussions are relevant, ensuring clarity in topic evolution.\n\"linked_nodes\" must include all references in a single list, capturing all nodes this node draws from or informs.\nThe structure of \"predecessor\", \"successor\", and \"contextual_relation\" must ensure logical and chronological consistency between past and present discussions.\n\nExample Input (Conversation with Bookmark Spells):\nExisting JSON:\n\nTranscript:\nAlex: Hey Jordan, summer’s coming up. We should totally go on a road trip!\nJordan: That sounds awesome! But road trips can get expensive. Gas, food, places to stay… It all adds up.\nAlex: True, but we can budget it out. If we book some places early and plan food stops, we might save some cash.\nJordan: Yeah, maybe we can also stay at some cheap motels or even camp for a few nights.\nAlex: Exactly. I’ll make a list of potential stops and places to sleep.\nAlex: LLM wish bookmark create Road Trip Planning.\nJordan: Speaking of planning, I’ve been trying to fix my sleep schedule. Finals completely messed it up.\nAlex: Oh yeah, I feel you. When people get stressed, they sleep less, which makes them even more stressed, and then they sleep even less.\nJordan: Yep, and then when you add caffeine into the mix, it just makes things worse. I was practically running on energy drinks.\nAlex: Not to mention, when you’re sleep-deprived, you tend to eat worse, and bad eating can also make it harder to sleep. It’s like everything is connected.\nJordan: So basically, when you’re stressed, you don’t sleep enough. Then because you don’t sleep, you get more stressed, and things like caffeine and bad eating habits just make the whole situation even worse.\nAlex: Exactly. But the good news is that breaking just one part of the cycle—like cutting down on caffeine or trying to fix your sleep schedule—can help stop everything from spiraling out of control.\nJordan: Makes sense. I guess I need to start by drinking less caffeine.\nAlex: Yeah, and maybe try doing something relaxing before bed, like listening to music or reading instead of staring at your phone.\nJordan: LLM wish capture contextual progress Stress-Sleep Cycle.\nAlex: Anyway, did you hear about that new horror movie coming out next month?\nJordan: Oh, yeah! It looks terrifying. I love a good horror flick.\nAlex: We should totally watch it when it releases.\nJordan: Definitely. But no watching it late at night—I’ll never get any sleep.\nAlex: Haha, fair enough.\nJordan: Oh, by the way, about that road trip—do you think we should rent a car or use mine?\nAlex: Good question. Your car is solid, but renting might save us some trouble if we’re going really far.\nJordan: Yeah, plus, rentals come with insurance, which could be helpful.\nAlex: LLM wish bookmark open Road Trip Planning.\nJordan: Right, so we need to decide if we’re driving your car or renting, and we should check gas prices along the way.\nAlex: Yep, and maybe look at rental deals. I’ll compare some prices later.\nJordan: Sounds good. Let’s lock in a plan soon!\n\n\nExample JSON Output:\n[\n  {\n    \"node_name\": \"Road Trip Planning\",\n    \"type\": \"bookmark\",\n    \"predecessor\": None,\n    \"successor\": \"Fixing Sleep Schedules and Stress\",\n    \"contextual_relation\": {},\n    \"linked_nodes\": [\n      \"Fixing Sleep Schedules and Stress\",\n      \"Road Trip Planning - Car Rental Discussion\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": True,\n    \"is_contextual_progress\": False,\n    \"summary\": \"Alex and Jordan discuss planning a summer road trip, acknowledging budget concerns. They decide to save money by booking accommodations early, staying at cheap motels, and camping. Alex plans to make a list of potential stops and sleeping arrangements.\"\n  },\n  {\n    \"node_name\": \"Fixing Sleep Schedules and Stress\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Road Trip Planning\",\n    \"successor\": \"Horror Movie Discussion\",\n    \"contextual_relation\": {\n      \"Road Trip Planning\": \"The transition from road trip planning to discussing sleep schedules happens naturally as Jordan mentions finals disrupting their sleep.\"\n    },\n    \"linked_nodes\": [\n      \"Road Trip Planning\",\n      \"Horror Movie Discussion\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": False,\n    \"is_contextual_progress\": True,\n    \"summary\": \"Jordan mentions their sleep schedule being disrupted due to finals, leading to a discussion on stress and sleep deprivation. They explore how stress, caffeine, and bad eating habits contribute to a negative cycle and discuss ways to break it, such as reducing caffeine intake and establishing a better nighttime routine.\"\n  },\n  {\n    \"node_name\": \"Horror Movie Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Fixing Sleep Schedules and Stress\",\n    \"successor\": \"Road Trip Planning - Car Rental Discussion\",\n    \"contextual_relation\": {\n      \"Fixing Sleep Schedules and Stress\": \"The discussion transitions from sleep issues to horror movies, as Jordan jokes about avoiding horror films at night to prevent sleep loss.\"\n    },\n    \"linked_nodes\": [\n      \"Fixing Sleep Schedules and Stress\",\n      \"Road Trip Planning - Car Rental Discussion\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": False,\n    \"is_contextual_progress\": False,\n    \"summary\": \"Alex and Jordan discuss an upcoming horror movie. Jordan expresses excitement but jokes about avoiding late-night viewing to prevent sleep issues.\"\n  },\n  {\n    \"node_name\": \"Road Trip Planning - Car Rental Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Horror Movie Discussion\",\n    \"successor\": None,\n    \"contextual_relation\": {\n      \"Road Trip Planning\": \"The conversation returns to road trip planning as Jordan revisits the topic, prompting discussions about using a personal car versus renting one.\",\n      \"Horror Movie Discussion\": \"The transition occurs naturally as Alex and Jordan shift from casual movie talk back to logistics for their trip.\"\n    },\n    \"linked_nodes\": [\n      \"Road Trip Planning\",\n      \"Horror Movie Discussion\",\n      \"Fixing Sleep Schedules and Stress\"\n    ],\n    \"chunk_id\": None,\n    \"is_bookmark\": False,\n    \"is_contextual_progress\": False,\n    \"summary\": \"Jordan brings the conversation back to the road trip, specifically whether to rent a car or use a personal vehicle. They consider factors like gas prices and rental insurance before agreeing to compare rental deals.\"\n  }\n]\n"    
    for attempt in range(retries):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=20000,
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
            print(f"Invalid JSON: {e}")     
        except anthropic.AuthenticationError:
            print("Authentication failed. Check your API key.")
            break  # Auth errors are not recoverable
        except anthropic.RateLimitError:
            print("Rate limit exceeded. Retrying...")
        except anthropic.APIError as e:
            print(f"API error occurred: {e}")
            if "overloaded" not in str(e).lower():
                break  # Only retry if it's overload-related
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

def generate_individual_formalism(formalism_input: str, temp: float = 0.7, retries: int = 5, backoff_base: float = 1.5):
    generate_formalism_prompt ="You are an advanced AI model tasked with transforming structured conversational data and raw text into a concise causal loop diagram (CLD) represented as a dictionary with LOOPY-compatible structure. Your goal is to dynamically infer the relationships between topics discussed in the conversation and convert them into a causal loop diagram, with special focus on extracting formalism in the contextual progress of the conversation.\n\nYou will be provided with three inputs:\n1. conversation_data\n2. raw_text\n3. user_research_background - A description of the user's research interests and background\n\nAnalyze the conversation_data and raw_text to identify causal relationships and create a comprehensive causal loop diagram that aligns with the user's research background.\n\nOutput Format:\nYou must strictly return a dictionary in the following format:\n[\n  [\n    [id, x, y, init, label, color] # this is for nodes,\n    ...\n  ],\n  [\n    [from, to,arc,strength, _] # this is for the edges,\n    ...\n  ],\n  [\n    [x, y, text] # this is for the labels,\n    ...\n  ],\n  meta # this is the meta an integer\n]\n\ntypes of the about output format:\nnode = id - int, x - int, y -int, init - float(always 1), color- int.\nedges= from - int, to - int, arc - int, strength - float, _ = 0.\nlabels= x - int, y - int, text- str.\nmeta - int.\nWhere:\n- meta is the total number of nodes + labels + 2 (for edges).\n- Node id is a unique integer starting from 0.\n- Edges: Each edge refers to valid id values for from and to.\n- Assign random integers to color for different nodes but the integers assigned should be less than total number of nodes divided by 1.5.\n\nIMPORTANT: Only create nodes that have at least one causal relationship (edge) with another node. Do not include isolated nodes without any connecting edges.\n\nCRITICAL: Ensure that your diagram contains at least one complete causal loop where nodes are connected in a cycle (A→B→C→A or similar). The edges in these loops must form a complete circuit so that changes in any node propagate through the entire loop and affect the originating node. These must be genuine loops with actual causal connections, not just visually arranged in a circle.\n\nPRIMARY FOCUS: Prioritize identifying and extracting formalism in the contextual progress of the conversation. Examine how concepts, theories, methods, or structured approaches develop and influence each other throughout the conversation. Only include other nodes if they directly relate to this formalism development.\n\nRESEARCH CONTEXT ALIGNMENT: Frame all node labels, relationships, and concepts using terminology and perspectives relevant to the user's research background. The variables and causal connections should reflect the user's domain of expertise and research interests, making the diagram immediately relevant and intuitive to their field of study.\n\nLoop Detection and Construction:\nActively search for and construct complete causal loops in the conversation:\n- Reinforcing loops: Create cycles where changes amplify around the loop (e.g., A increases B, B increases C, C increases A).\n- Balancing loops: Create cycles that tend to stabilize (e.g., A increases B, B increases C, C decreases A).\n- Make sure every loop is complete with no breaks in the causal chain.\n- Test each loop by mentally tracing the effects: if one node increases, trace the effects through each connection to verify the loop completes and affects the original node.\n\nCausal Relation Detection:\nIdentify and infer causal relationships implicitly from the conversational context, summaries, and shifts between topics. Look for the following:\n1. Causal Direction: Recognize when one concept influences another (e.g., \"this leads to,\" \"this causes,\" \"results in,\" \"this influences\").\n2. Contextual Transitions: When the conversation shifts topics, infer the causal influence or dependency between these topics.\n3. Behavioral and Cognitive Feedback: Consider feedback loops and how certain topics may influence others based on previous discussions.\n\nVariable Naming Conventions:\n1. Use nouns or noun phrases for variable names that align with the user's research field terminology.\n2. Ensure variable names have a clear sense of direction (can be larger or smaller).\n3. Choose variables whose normal sense of direction is positive.\n4. Avoid using variable names containing prefixes indicating negation (non, un, etc.).\n5. Frame concepts using domain-specific language from the user's research background.\n\nEdge Strength Determination:\nDetermine edge strength based on the following scale:\n- Positive Influence → +1.0\n- Negative Influence → -1.0\n\nStep-by-step instructions for creating the CLD:\n1. Review the user's research background to understand their domain, terminology, and conceptual framework.\n2. Analyze the conversation_data and raw_text to identify key topics and concepts, focusing on formalism in the contextual progress.\n3. Create a list of variables (nodes) based on the identified topics, following the variable naming conventions and using terminology relevant to the user's research field.\n4. Determine causal relationships between variables using the causal relation detection guidelines.\n5. Explicitly identify or create at least one complete causal loop where a sequence of nodes connects back to the starting node.\n6. Verify each loop is functional by tracing the effect of increasing one node through the entire loop to confirm it eventually affects itself.\n7. Assign edge strengths based on the provided scale.\n8. Position nodes across a coordinate range (0-800 for x, 0-600 for y) to create a well-distributed visualization with adequate spacing.\n9. Arrange nodes that form loops in positions that clearly show the cyclical nature of their relationships.\n10. Create edges between related nodes, specifying the from and to node ids, and the strength of the relationship. Use appropriate arc values to make loop connections clear.\n11. Add one label to describe the causal loop diagram, positioning it at least 50 coordinate units away from any node to avoid overlap.\n12. Calculate the meta value by summing the total number of nodes, labels, and adding 2 for edges.\n\nFinal Output Formatting:\nConstruct the List with the following lists: \"nodes\", \"edges\", \"labels\", and \"meta\". Ensure that all required fields are included for each node, edge, and label. Double-check that the meta value is correctly calculated and that all node ids and edge references are valid.\n\nPresent your final output as a single list without any additional explanation or commentary."
    for attempt in range(retries):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
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
            print(loopy_url)
            return loopy_url
            # json_text = "{" + message.content[0].text
            
            # return json.loads(json_text)  # Parse JSON response
            

        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")     
        except anthropic.AuthenticationError:
            print("Authentication failed. Check your API key.")
            break  # Auth errors are not recoverable
        except anthropic.RateLimitError:
            print("Rate limit exceeded. Retrying...")
        except anthropic.APIError as e:
            print(f"API error occurred: {e}")
            if "overloaded" not in str(e).lower():
                break  # Only retry if it's overload-related
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        # Exponential backoff before next retry
        sleep_time = backoff_base ** attempt + random.uniform(0, 1)
        time.sleep(sleep_time)

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
def save_json(file_name: str, chunks: dict, graph_data: dict) -> dict:
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
    FastAPI route to save JSON data using an external function.
    """
    try:
        # Validate input data
        if not request.file_name.strip():
            raise HTTPException(status_code=400, detail="File name cannot be empty.")

        if not isinstance(request.chunks, dict) or not isinstance(request.graph_data, List):
            raise HTTPException(status_code=400, detail="Chunks must be a valid dictionary and Graph Data must be a valid list.")
        try:
            result = save_json(request.file_name, request.chunks, request.graph_data) # save json function
        except Exception as file_error:
            raise HTTPException(status_code=500, detail=f"File saving error: {str(file_error)}")

        return result

    except HTTPException as http_err:
        raise http_err  # Re-raise HTTP exceptions as they are

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@lct_app.post("/generate_formalism/", response_model=generateFormalismResponse)
async def generate_formalism_call(request: generateFormalismRequest):
    try:
        # Validate input data
        if not isinstance(request.chunks, dict) or not isinstance(request.graph_data, List):
            raise HTTPException(status_code=400, detail="Chunks must be a valid dictionary and Graph Data must be a valid list.")
        try:
            result = generate_formalism(request.chunks, request.graph_data, request.user_pref) # save json function
        except Exception as formalism_error:
            raise HTTPException(status_code=500, detail=f"Formalism Generation error: {str(formalism_error)}")

        return {"formalism_data": result}

    except HTTPException as http_err:
        raise http_err  # Re-raise HTTP exceptions as they are

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")