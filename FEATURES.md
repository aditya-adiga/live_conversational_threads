# Live Conversational Threads - Features Documentation

## Backend Features

### 1. Transcript Processing
- **Chunking System**: 
  - Implements a sliding window chunking mechanism to break down large transcripts into manageable pieces
  - Uses a configurable chunk size (default 10,000 words) to ensure optimal processing
  - Automatically splits conversations into smaller segments while maintaining context

- **Smart Chunking**: 
  - Uses overlap between chunks (default 2,000 words) to maintain context continuity
  - Prevents context loss at chunk boundaries
  - Ensures smooth transitions between processed segments

- **UUID-based Chunk Management**: 
  - Each chunk is assigned a unique identifier for tracking
  - Enables precise reference to specific conversation segments
  - Facilitates easy retrieval and updating of chunks

### 2. Conversation Analysis
- **Thread Detection**: 
  - Automatically identifies and structures conversational threads
  - Detects topic shifts and new discussion branches
  - Maintains chronological order of conversations
  - Identifies related discussion points across the conversation

- **Context Tracking**: 
  - Maintains relationships between different parts of the conversation
  - Tracks how topics evolve and connect
  - Preserves conversation history and context
  - Enables understanding of topic dependencies

- **Bookmark System**: 
  - Create bookmarks for important discussion points
    - Allows users to mark significant moments in conversations
    - Enables quick navigation to key discussion points
    - Preserves important context for future reference
  - Reopen and update existing bookmarks
    - Supports revisiting and expanding on bookmarked topics
    - Maintains history of bookmark interactions
  - Track contextual progress within bookmarked discussions
    - Monitors evolution of bookmarked topics
    - Records insights and developments

### 3. JSON Generation
- **Structured Output**: Generates JSON-formatted conversation nodes with:
  - Node names and types
    - Unique identifiers for each conversation segment
    - Classification of nodes (conversational_thread, bookmark)
  - Predecessor and successor relationships
    - Tracks conversation flow
    - Maintains chronological order
  - Contextual relations between nodes
    - Maps how topics influence each other
    - Records dependencies between discussions
    - Maintains conversation context
  - Linked nodes tracking
    - Records all related discussion points
    - Enables cross-reference between topics
    - Supports comprehensive topic analysis
  - Bookmark status
    - Tracks which nodes are bookmarked
    - Records bookmark creation and updates
    - Maintains bookmark history
  - Contextual progress indicators
    - Marks significant developments
    - Tracks topic evolution
    - Highlights key insights
  - Detailed summaries
    - Provides concise overview of each node
    - Captures key points and developments

### 4. Formalism Generation
- **Causal Loop Diagrams**: 
  - Creates dynamic causal loop diagrams from conversation data
  - Visualizes relationships between concepts
  - Shows feedback loops and dependencies

- **Research Context Integration**: 
  - Aligns formalism with user's research background
  - Uses domain-specific terminology
  - Maintains academic rigor

- **Loop Detection**: 
  - Identifies and constructs complete causal loops
  - Detects reinforcing and balancing loops
  - Validates causal relationships

- **Variable Management**: 
  - Domain-specific variable naming
    - Uses terminology from user's field
    - Ensures clarity and precision
    - Maintains academic standards
  - Clear directional relationships
    - Shows cause and effect
    - Indicates influence direction
    - Maintains logical flow
  - Strength-based edge connections
    - Quantifies relationship strength
    - Shows influence magnitude
    - Supports analysis of impact

### 5. API Endpoints
- `/get_chunks/`: 
  - Processes and chunks transcript input
  - Returns structured chunk data
  - Supports large transcript handling

- `/generate-context-stream/`: 
  - Streams context generation results
  - Provides real-time updates
  - Supports progressive loading

- `/save_json/`: 
  - Saves conversation structure and graph data
  - Supports file naming and organization
  - Facilitates data sharing

- `/generate_formalism/`: 
  - Generates formalism based on conversation data
  - Creates causal loop diagrams
  - Supports research context

## Frontend Features

### 1. Input Management
- **Transcript Input**: 
  - Dedicated component for entering conversation transcripts
  - Supports large text input
  - Provides formatting options

- **User Preferences**: 
  - Interface for setting research background and preferences
  - Customizes formalism generation
  - Supports user-specific needs

- **Input Validation**: 
  - Ensures proper formatting and content
  - Prevents processing errors
  - Provides user feedback

### 2. Visualization Components
- **Contextual Graph**: 
  - Interactive visualization of conversation threads
    - Shows conversation structure
    - Enables navigation
    - Supports exploration
  - Node relationship display
    - Shows connections between topics
    - Indicates dependencies
    - Supports analysis
  - Bookmark highlighting
    - Marks important points
    - Enables quick access
    - Supports focus
  - Context progress indicators
    - Shows topic development
    - Tracks evolution
    - Highlights insights

- **Structural Graph**:
  - Displays formal structure of conversations
    - Shows organization
    - Enables understanding
    - Supports analysis
  - Shows causal relationships
    - Indicates influences
    - Shows dependencies
    - Supports system thinking
  - Interactive node exploration
    - Enables detailed viewing
    - Supports investigation
    - Facilitates understanding

### 3. Formalism Interface
- **Formalism Generation**: 
  - Interface for creating causal loop diagrams
  - Supports customization
  - Enables analysis

- **Formalism List**: 
  - Displays and manages generated formalisms
  - Supports organization
  - Enables comparison

- **Visual Customization**: 
  - Options for adjusting diagram appearance
  - Supports personalization
  - Enables clarity
  - Facilitates presentation

### 4. Data Management
- **Save Functionality**: 
  - Save conversation structures
    - Preserves work
    - Enables sharing
    - Supports collaboration
  - Export graph data
    - Enables portability
    - Supports analysis
    - Facilitates sharing
  - File naming and organization
    - Maintains order
    - Enables retrieval
    - Supports management

- **JSON Management**: 
  - Load existing structures
    - Enables continuation
    - Supports modification
    - Facilitates sharing
  - Update and modify saved data
    - Supports evolution
    - Enables improvement
    - Facilitates development
  - Export capabilities
    - Enables portability
    - Supports sharing
    - Facilitates collaboration

### 5. UI Components
- **Legend**: 
  - Visual guide for graph elements and relationships
  - Supports understanding
  - Enables navigation

- **Interactive Controls**: 
  - Zoom and pan capabilities
    - Enables detailed viewing
    - Supports exploration
  - Node selection
    - Enables focus
    - Supports analysis
  - Relationship highlighting
    - Shows connections
    - Supports analysis

- **Responsive Design**: 
  - Adapts to different screen sizes and devices
  - Ensures accessibility
  - Supports usability

## Integration Features

### 1. Real-time Processing
- **Streaming Updates**: 
  - Real-time updates of conversation analysis
  - Provides immediate feedback
  - Supports interaction

- **Progressive Loading**: 
  - Efficient handling of large transcripts
  - Prevents overload
  - Supports performance
  - Enables scalability

- **Background Processing**: 
  - Non-blocking operations for better UX
  - Maintains responsiveness
  - Supports efficiency

### 2. Error Handling
- **Graceful Failure**: 
  - Robust error handling and recovery
  - Prevents data loss
  - Supports reliability

- **User Feedback**: 
  - Clear error messages and status updates
  - Supports understanding
  - Enables resolution

- **Retry Mechanisms**: 
  - Automatic retry for failed operations
  - Ensures completion
  - Supports reliability

### 3. Security
- **API Key Management**: 
  - Secure handling of API credentials
  - Prevents unauthorized access
  - Supports privacy

- **CORS Configuration**: 
  - Proper cross-origin resource sharing setup
  - Ensures security
  - Supports integration

- **Input Validation**: 
  - Security measures for user input
  - Prevents attacks
  - Supports safety