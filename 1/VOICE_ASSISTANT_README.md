# Voice Assistant for Event Lead Updates

A hands-free voice assistant feature that allows users to query and manage volunteer/event lead data using natural language voice commands.

## Features

### Voice Recognition & Synthesis
- **Speech-to-Text**: Uses Web Speech API for real-time voice recognition
- **Text-to-Speech**: Provides audio responses for a truly hands-free experience
- **Browser Compatibility**: Works with modern browsers (Chrome, Edge, Safari, Firefox)

### Natural Language Processing
- **Intent Recognition**: Understands various ways to ask the same question
- **Entity Extraction**: Identifies specific volunteers, branches, projects in queries
- **Command Patterns**: Supports flexible natural language patterns

### Supported Voice Commands

#### Volunteer Information
- "Show me hours for [volunteer name]"
- "How many hours did [volunteer name] work?"
- "[Volunteer name] projects"
- "What projects did [volunteer name] work on?"

#### Branch Analytics  
- "Who worked at [branch name]?"
- "Show me [branch name] volunteers"
- "Volunteers at [branch name]"

#### General Statistics
- "Total hours"
- "How many volunteers?"
- "Active volunteer count" 
- "Top volunteers"
- "Get leaderboard"

#### Project Information
- "List all branches"
- "Show branches"
- "Project stats for [project name]"
- "Recent activity"

#### Data Filtering
- "Filter by [term]"
- "Search for [term]"
- "Show only [term]"

### User Interface

#### Floating Assistant
- Minimized: Blue circular button in bottom-right corner
- Expanded: Full chat interface with conversation history

#### Interactive Elements
- **Microphone Button**: Start/stop voice recognition (blue when listening)
- **Speaker Button**: Stop current speech output
- **Clear Button**: Reset conversation history
- **State Indicator**: Shows current assistant status (Idle, Listening, Processing, Speaking)

#### Visual Feedback
- Real-time transcript display while speaking
- Conversation history with timestamps
- Color-coded status indicators
- Animated microphone when listening

## Technical Implementation

### Architecture
```
VoiceAssistant Component
├── VoiceAssistantService (Speech Recognition/Synthesis)
├── VoiceQueryProcessor (Natural Language Processing)
└── useVoiceCommands Hook (Command Execution)
```

### Core Services

#### VoiceAssistantService (`/src/services/voiceAssistant.js`)
- Initializes Web Speech API
- Handles speech recognition events
- Manages text-to-speech synthesis
- Provides browser compatibility checks

#### VoiceQueryProcessor (`/src/services/voiceQueryProcessor.js`)
- Pattern matching for command recognition
- Intent classification and entity extraction
- Confidence scoring for matches

#### useVoiceCommands Hook (`/src/hooks/useVoiceCommands.js`)
- Command execution logic
- Data analysis and calculations
- Integration with existing volunteer data
- Smart suggestions for failed matches

### Integration Points

#### Main Application
- Integrated into `App.jsx` as floating component
- Receives live volunteer data updates
- Can trigger data filtering and searches

#### Data Management
- Works with existing `useVolunteerData` hook
- Updates dashboard filters based on voice commands
- Maintains conversation context and history

## Usage Examples

### Getting Started
1. Click the blue microphone icon in bottom-right corner
2. Wait for "Ready" status indicator
3. Click microphone button to start listening
4. Speak your command clearly
5. Listen to the response or read in chat history

### Example Conversations

**User**: "Show me total hours"
**Assistant**: "Total volunteer hours: 142.0 hours from 11 active volunteers across 12 projects, averaging 12.9 hours per volunteer."

**User**: "Who worked at Blue Ash?"
**Assistant**: "Blue Ash branch has 3 volunteers who worked 56.0 hours total, averaging 18.7 hours per volunteer. Top contributor is Jane Smith with 42.5 hours."

**User**: "Jane Smith projects"
**Assistant**: "Jane Smith has worked on 2 projects across 2 categories, totaling 46.0 hours. Projects include: Summer Basketball Camp, After School Program."

### Error Handling
- Provides helpful suggestions for unrecognized commands
- Handles speech recognition errors gracefully  
- Offers alternative phrasings for failed queries
- Maintains conversation context during errors

## Browser Support

### Required Features
- Web Speech API (SpeechRecognition)
- Speech Synthesis API
- Modern JavaScript (ES6+)

### Supported Browsers
- ✅ Chrome 25+ (Best support)
- ✅ Edge 79+
- ✅ Safari 14+ (iOS/macOS)
- ✅ Firefox 49+ (Limited support)

### Fallback Behavior
- Displays error message for unsupported browsers
- Gracefully disables voice features
- Maintains text-based chat interface

## Privacy & Security

### Local Processing
- All speech recognition happens locally in browser
- No audio data sent to external servers
- Conversation history stored only in session

### Data Access
- Only accesses volunteer data already loaded in application
- No sensitive information exposed in voice responses
- Follows same data privacy rules as main application

## Future Enhancements

### Planned Features
- Voice-activated data updates/edits
- Multi-language support  
- Custom wake words ("Hey YMCA")
- Voice shortcuts for common operations
- Integration with external YMCA systems

### Performance Improvements
- Voice command caching
- Faster speech synthesis
- Reduced JavaScript bundle size
- Progressive web app (PWA) support

## Troubleshooting

### Common Issues

**Voice not recognized**
- Ensure microphone permissions granted
- Speak clearly and not too fast
- Reduce background noise
- Try shorter, simpler commands

**No audio response** 
- Check browser audio settings
- Verify system volume levels
- Try different voice synthesis settings

**Commands not working**
- Check supported command list
- Try alternative phrasings
- Use exact volunteer/branch names as they appear in data

### Debug Mode
Enable browser developer console to see:
- Voice recognition events
- Command processing details  
- Error messages and stack traces
- Performance metrics

---

*Voice Assistant built for YMCA Cincinnati Volunteer Management System - Hackathon: Platform for Belonging*