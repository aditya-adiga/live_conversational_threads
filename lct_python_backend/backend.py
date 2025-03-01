import anthropic
import os
import json
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time

lct_app = FastAPI()

# Request Model
class TranscriptRequest(BaseModel):
    transcript: str


def sliding_window_chunking(text, chunk_size=2000, overlap=500):
    """
    Splits text into overlapping chunks to maintain context.

    Parameters:
    - text (str): The input text.
    - chunk_size (int): The max token size per chunk.
    - overlap (int): The number of overlapping tokens between chunks.

    Returns:
    - List of text chunks.
    """
    assert chunk_size > overlap, "chunk_size must be greater than overlap!"

    words = text.split()  # Simple tokenization (word-based)
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap  # Move window with overlap

    return chunks

def generate_lct_json(transcript, temp = 0.6):
    """
    Generates a JSON output from a given transcript using the Claude API.

    This function sends the provided transcript to Claude-3 and requests a JSON-formatted response.
    It handles authentication, API errors, and ensures the output is valid JSON.

    Parameters:
    - transcript (str): The input text to be processed by Claude.
    - temp (float, optional): The temperature parameter for response randomness (default is 0.6).

    Returns:
    - dict or None: A parsed JSON object if successful, otherwise None.

    Raises:
    - anthropic.AuthenticationError: If API key authentication fails.
    - anthropic.RateLimitError: If the API rate limit is exceeded.
    - anthropic.APIError: If an API-related error occurs.
    - json.JSONDecodeError: If the returned response is not valid JSON.
    - Exception: For any unexpected errors.
    """
    try:
        client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

        message = client.messages.create(
        # model="claude-3-5-haiku-20241022", 
        model="claude-3-7-sonnet-20250219",
        max_tokens=8192,
        temperature=temp,
        system="You are an advanced AI model that structures conversations into strictly JSON-formatted nodes. Each conversational shift should be captured as a new node with defined relationships.\n\nFormatting Rules:\n\nInstructions:\n\nHandling New JSON Creation\n\nExtract Key Nodes: Identify all topic shifts in the conversation. Each topic shift forms a new \"node\", even if the topic was discussed earlier.\nStrictly Generate JSON Output:\n[\n  {\n    \"node_name\": \"Title of the conversational thread\",\n    \"type\": \"conversational_thread\" or \"bookmark\",\n    \"predecessor\": \"Previous node name\",\n    \"successor\": \"Next node name\",\n    \"contextual_relation\": {\n      \"Related Node 1\": \"Detailed explanation of how this node's context is used\",\n      \"Related Node 2\": \"Another detailed explanation\",\n      \"...\": \"Additional related nodes with their respective explanations can be included as needed\"\n    },\n    \"is_bookmark\": true or false,\n    \"summary\": \"Brief description of what was discussed in this node.\"\n  }\n]\nDefine Structure:\n\"predecessor\" → The direct previous node.\n\"successor\" → The direct next node.\n\"contextual_relation\" → Use this to explain how past nodes contribute to the current discussion.\nKeys = node names that contribute context.\nValues = a detailed explanation of how the multiple referenced nodes influence the current discussion.\n\nHandling Updates to Existing JSON\nIf an existing JSON structure is provided along with the transcript , modify it as follows and Strictly return only the nodes generated for the current input transcript:\n\nContinuing a topic: If the conversation continues an existing discussion, update the successor field of the last relevant node.\nNew topic: If a conversation introduces a new topic, create a new node and properly link it.\nRevisiting a Bookmark:\nIf \"lingardium bookmarkium open [name]\" appears, find the existing bookmark node and update contextual_relation to include the new conversation node.\nDo NOT create a new bookmark when revisited—update the existing one instead.\nContextual Relation Updates:\nMaintain indirect connections (e.g., a previous conversation influencing the new one).\nEnsure logical flow between past and present discussions.\n\n\nChronology, Contextual Referencing and Bookmarking:\nIf a conversation returns to a previous topic, create a new node instead of merging and capture the context of the previous conversation in “contextual_relation”.\nEnsure \"contextual_relation\" captures past references accurately, explaining why they are relevant in the current discussion.\n\nConversational threads (type: \"conversational_thread\") must:\nCapture every topic shift as a new node.\nInclude both \"predecessor\" and \"successor\" nodes for proper flow.\nList contextual relations with previous nodes in \" contextual_relation \".\nFor nodes with type= “conversational_thread”, always have \"is_bookmark\": false.\n\nBookmark nodes (type: \"bookmark\") must:\nBe created when the phrase \"lingardium bookmarkium create\" appears, using the contextually relevant topic.\nOnly reference the conversational nodes where they were created and opened in \"contextual_relation\", do capture the context behind creating the bookmark.\n\nWhen the phrase \"lingardium bookmarkium open\" appears, The corresponding bookmark must be updated to include the new node in \"contextual_relation\" along with the context being drawn from the bookmark.\nDo not create a new bookmark when it is revisited.\nFor nodes with type= “bookmark”, add \"is_bookmark\": true and update the \"contextual_relation\" when revisited.\n\n\nExample Input (Conversation with Bookmark Spells):\nExisting JSON:\n\nTranscript:\nAlice: Hey, have you watched the latest episode of that sci-fi show?  \nBob: Oh yeah! It was amazing. The twist at the end was mind-blowing.  \nAlice: I know, right? I didn’t expect that character to betray them.  \nBob: Yeah, though I feel like they hinted at it earlier.  \nAlice: True. But now I’m wondering what’s going to happen next. The stakes are so high.  \nBob: Right? I think they might set up a bigger conflict between the factions.  \nAlice: That makes sense. Oh, by the way, did you finish your report for work?  \nBob: Not yet, I got caught up with the show.  \nAlice: Haha, same here. I really need to focus tonight.  \nBob: Me too. I also have to prepare for that meeting tomorrow.  \nAlice: Oh yeah, the client presentation. Are you feeling ready?  \nBob: Kind of. I still need to finalize a few slides.  \nAlice: Let me know if you need help. I can review them later.  \nBob: That’d be great. Thanks!  \nAlice: **Lingardium bookmarkium create Client Presentation Notes**  \nBob: No problem. Speaking of work, did you hear about the company’s new policy on remote work?  \nAlice: Yeah, I read the email. They’re making it more flexible.  \nBob: I think it’s a good move. It gives people more balance.  \nAlice: Agreed. But I wonder how it'll affect team collaboration.  \nBob: That’s true. Maybe we should bring it up in tomorrow’s meeting.  \nAlice: Good idea. Let’s see what the others think.  \nAlice: **Lingardium bookmarkium open Client Presentation Notes**  \nBob: Oh right, I still need to finalize a few slides!  \nAlice: Exactly. Let me know if you want me to review them before the meeting.  \nBob: Will do, thanks!  \nAlice: Oh, speaking of work-life balance, I also read an article about how flexible hours improve productivity.  \nBob: That’s interesting! That ties into the remote work discussion.  \nAlice: Definitely. But hey, do you think that sci-fi show could be hinting at something bigger? Maybe it’s about work-life balance in the future?  \nBob: Oh, maybe! That would be an interesting twist. Kind of like balancing between a sci-fi world and our real-life work expectations.  \nAlice: Exactly, kind of like how people juggle multiple responsibilities. It's kind of like remote work, isn’t it?  \nBob: Haha, true. Maybe they’ll feature a character who has to balance a high-pressure job with their personal life. That’d be fun to watch!  \nAlice: Yeah, I’d love that. Alright, back to work for me!  \n\nExample JSON Output:\n[\n  {\n    \"node_name\": \"Sci-Fi Show Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": null,\n    \"successor\": \"Work and Productivity\",\n    \"contextual_relation\": {},\n    \"is_bookmark\": False,\n    \"summary\": \"Discussion about the latest sci-fi show, plot twists, and character betrayals.\"\n  },\n  {\n    \"node_name\": \"Work and Productivity\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Sci-Fi Show Discussion\",\n    \"successor\": \"Client Presentation Discussion\",\n    \"contextual_relation\": {\n      \"Sci-Fi Show Discussion\": \"Indirectly related: Conversation shifted from entertainment to productivity, showing a contrast between distraction and focus.\"\n    },\n    \"is_bookmark\": false,\n    \"summary\": \"Discussion about work tasks, reports, and upcoming meetings.\"\n  },\n  {\n    \"node_name\": \"Client Presentation Discussion\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Work and Productivity\",\n    \"successor\": \"Remote Work Policy\",\n    \"contextual_relation\": {\n      \"Work and Productivity\": \"Directly related: The client presentation is part of work productivity concerns.\"\n    },\n    \"is_bookmark\": false,\n    \"summary\": \"Talked about preparing for the client presentation, finalizing slides, and offering help.\"\n  },\n  {\n    \"node_name\": \"Bookmark - Client Presentation Notes\",\n    \"type\": \"bookmark\",\n    \"predecessor\": \"Client Presentation Discussion\",\n    \"successor\": \"Remote Work Policy\",\n    \"contextual_relation\": {\n      \"Client Presentation Discussion\": \"Directly related: Bookmark created for tracking discussion about the client presentation.\",\n      \"Work and Productivity\": \"Indirectly related: General productivity concerns influenced this discussion.\"\n    },\n    \"is_bookmark\": true,\n    \"summary\": \"A bookmark created to track notes and discussions about the client presentation.\"\n  },\n  {\n    \"node_name\": \"Remote Work Policy\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Client Presentation Discussion\",\n    \"successor\": \"Revisiting Client Presentation Notes\",\n    \"contextual_relation\": {\n      \"Work and Productivity\": \"Directly related: The remote work discussion affects productivity.\",\n      \"Client Presentation Discussion\": \"Indirectly related: Virtual presentations may be influenced by remote work policies.\"\n    },\n    \"is_bookmark\": false,\n    \"summary\": \"Discussion about company’s new remote work policy and its effects on team collaboration.\"\n  },\n  {\n    \"node_name\": \"Revisiting Client Presentation Notes\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Remote Work Policy\",\n    \"successor\": \"Work-Life Balance and Sci-Fi\",\n    \"contextual_relation\": {\n      \"Bookmark - Client Presentation Notes\": \"Directly related: The bookmark was opened to revisit previous notes on the client presentation.\",\n      \"Remote Work Policy\": \"Indirectly related: Remote work policies may impact how presentations are structured.\"\n    },\n    \"is_bookmark\": false,\n    \"summary\": \"Reopened bookmark to continue discussion on finalizing slides for the client presentation.\"\n  },\n  {\n    \"node_name\": \"Work-Life Balance and Sci-Fi\",\n    \"type\": \"conversational_thread\",\n    \"predecessor\": \"Revisiting Client Presentation Notes\",\n    \"successor\": null,\n    \"contextual_relation\": {\n      \"Remote Work Policy\": \"Directly related: Work-life balance discussion emerged from remote work policies.\",\n      \"Sci-Fi Show Discussion\": \"Indirectly related: The sci-fi show discussion influenced how work-life balance was framed in the conversation.\"\n    },\n    \"is_bookmark\": false,\n    \"summary\": \"Conversation shifted to work-life balance, connecting remote work policies with themes in sci-fi.\"\n  }\n]\n",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": transcript,
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
        try:
            json_data = json.loads(json_text)  
            return json_data
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
        return None
        
    except anthropic.AuthenticationError:
        print("Authentication failed. Check your API key.")
    except anthropic.RateLimitError:
        print("Rate limit exceeded. Try again later.")
    except anthropic.APIError as e:
        print(f"API error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

def generate_context_json(transcript):
    """
    Generates a JSON output by processing a transcript in chunks.

    This function:
    1. Splits the transcript into overlapping chunks using `sliding_window_chunking`.
    2. Iteratively processes each chunk using `generate_lct_json`, while passing previously generated JSON data for context.
    3. Aggregates the JSON responses into a final list.

    Parameters:
    - transcript (str): The input text that needs to be processed.

    Returns:
    - list: A list of JSON objects combining all processed chunks.

    Raises:
    - TypeError: If the transcript is not a string.
    - ValueError: If `generate_lct_json` returns invalid JSON data.
    - Exception: For any unexpected errors.
    """

    # Ensure the transcript is a valid string
    if not isinstance(transcript, str):
        raise TypeError("The transcript must be a string.")

    chunks = sliding_window_chunking(transcript)
    existing_json = []

    for i, chunk in enumerate(chunks):
        mod_input = f'Existing JSON : \n {repr(existing_json)} \n\n Transcript Input: \n {chunk}'
        output_json = generate_lct_json(mod_input)

        if output_json is None:
            raise ValueError(f"Chunk {i+1} returned invalid JSON.")

        existing_json.extend(output_json)
        
    return existing_json

def stream_generate_context_json(transcript):
    """
    Generator function that processes transcript chunks and streams the updated JSON after each iteration.
    """
    if not isinstance(transcript, str):
        raise TypeError("The transcript must be a string.")

    chunks = sliding_window_chunking(transcript)
    existing_json = []

    for i, chunk in enumerate(chunks):
        mod_input = f'Existing JSON : \n {repr(existing_json)} \n\n Transcript Input: \n {chunk}'
        output_json = generate_lct_json(mod_input)

        if output_json is None:
            yield json.dumps({
                "chunk": i + 1,
                "error": f"Chunk {i+1} returned invalid JSON.",
                "existing_json": existing_json  # Send whatever we have so far
            }) + "\n"
            continue  # Skip this chunk

        existing_json.extend(output_json)

        # Yield full updated JSON after each iteration
        yield json.dumps({
            "chunk": i + 1,
            "existing_json": existing_json
        }) + "\n"

        time.sleep(0.5)

# FastAPI Streaming Endpoint
@lct_app.post("/generate-context-stream")
async def generate_context_stream(
    transcript: str = Form(None), 
    file: UploadFile = File(None)
):
    """
    API endpoint to process a transcript in chunks and stream the full updated JSON.
    Accepts either:
    - A raw text string (form input)
    - A text file upload
    """
    if file:
        content = await file.read()
        transcript = content.decode("utf-8")  # Read file content as string

    if not transcript:
        return {"error": "No valid transcript input provided."}

    return StreamingResponse(stream_generate_context_json(transcript), media_type="application/json")