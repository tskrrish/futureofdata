import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, MessageCircle, X, History } from 'lucide-react';
import VoiceAssistantService from '../services/voiceAssistant.js';
import VoiceQueryProcessor from '../services/voiceQueryProcessor.js';
import { useVoiceCommands } from '../hooks/useVoiceCommands.js';

const VoiceAssistant = ({ volunteerData, onDataUpdate }) => {
  const [isListening, setIsListening] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [assistantState, setAssistantState] = useState('idle'); // idle, listening, processing, speaking, error
  
  const voiceAssistant = useRef(null);
  const queryProcessor = useRef(null);
  const conversationEndRef = useRef(null);
  
  const { executeCommand, commandHistory, clearHistory } = useVoiceCommands(
    volunteerData,
    onDataUpdate
  );

  useEffect(() => {
    // Initialize voice assistant
    voiceAssistant.current = new VoiceAssistantService();
    queryProcessor.current = new VoiceQueryProcessor(volunteerData);

    if (!voiceAssistant.current.isSupported()) {
      setAssistantState('error');
      addMessage('assistant', "Sorry, your browser doesn't support voice features. Please use a modern browser like Chrome or Edge.");
      return;
    }

    // Set up voice assistant callbacks
    voiceAssistant.current.onResult((transcript) => {
      setCurrentTranscript(transcript);
      handleVoiceCommand(transcript);
    });

    voiceAssistant.current.onStateChange((state, error) => {
      setIsListening(state === 'listening');
      if (state === 'error') {
        setAssistantState('error');
        addMessage('assistant', `Voice recognition error: ${error}. Please try again.`);
      } else {
        setAssistantState(state);
      }
    });

    // Welcome message
    setTimeout(() => {
      addMessage('assistant', "Hello! I'm your voice assistant for volunteer data. Click the microphone to ask me questions like 'Show me total hours' or 'Who worked at Blue Ash?'");
    }, 1000);

    return () => {
      if (voiceAssistant.current) {
        voiceAssistant.current.stopListening();
        voiceAssistant.current.stopSpeaking();
      }
    };
  }, []);

  useEffect(() => {
    // Update query processor when volunteer data changes
    if (queryProcessor.current && volunteerData) {
      queryProcessor.current.updateData(volunteerData);
    }
  }, [volunteerData]);

  useEffect(() => {
    // Auto-scroll to bottom of conversation
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversationHistory]);

  const addMessage = (sender, message, data = null) => {
    const newMessage = {
      id: Date.now(),
      sender,
      message,
      data,
      timestamp: new Date().toLocaleTimeString()
    };
    setConversationHistory(prev => [...prev, newMessage]);
  };

  const handleVoiceCommand = async (transcript) => {
    addMessage('user', transcript);
    setAssistantState('processing');
    
    try {
      // Process the voice query
      const query = queryProcessor.current.processQuery(transcript);
      
      // Use the enhanced command execution
      const result = executeCommand(query.intent, query.entity, transcript);
      
      // Add assistant response
      addMessage('assistant', result.message, result.data);
      
      // Add suggestions if available
      if (result.suggestions && result.suggestions.length > 0) {
        const suggestionMessage = `Try: ${result.suggestions.join(', ')}`;
        addMessage('assistant', suggestionMessage);
      }
      
      // Speak the response
      if (result.success) {
        setIsSpeaking(true);
        voiceAssistant.current.speak(result.message, {
          onEnd: () => {
            setIsSpeaking(false);
            setAssistantState('idle');
          }
        });
      } else {
        setAssistantState('idle');
        setIsSpeaking(true);
        voiceAssistant.current.speak(result.message, {
          onEnd: () => {
            setIsSpeaking(false);
            setAssistantState('idle');
          }
        });
      }
      
      // Update parent component if data changed
      if (result.data && onDataUpdate) {
        onDataUpdate(result.data);
      }
      
    } catch (error) {
      console.error('Voice command processing error:', error);
      const errorMessage = "Sorry, I encountered an error processing your request.";
      addMessage('assistant', errorMessage);
      voiceAssistant.current.speak(errorMessage);
      setAssistantState('error');
    }
  };

  const toggleListening = () => {
    if (isListening) {
      voiceAssistant.current.stopListening();
    } else {
      voiceAssistant.current.startListening();
    }
  };

  const toggleSpeaking = () => {
    if (isSpeaking) {
      voiceAssistant.current.stopSpeaking();
      setIsSpeaking(false);
      setAssistantState('idle');
    }
  };

  const clearConversation = () => {
    setConversationHistory([]);
    clearHistory();
    addMessage('assistant', "Conversation cleared. How can I help you?");
  };

  const getStateColor = () => {
    switch (assistantState) {
      case 'listening': return 'text-blue-600 bg-blue-100';
      case 'processing': return 'text-yellow-600 bg-yellow-100';
      case 'speaking': return 'text-green-600 bg-green-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStateText = () => {
    switch (assistantState) {
      case 'listening': return 'Listening...';
      case 'processing': return 'Processing...';
      case 'speaking': return 'Speaking...';
      case 'error': return 'Error';
      default: return 'Ready';
    }
  };

  if (!isExpanded) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsExpanded(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-200 transform hover:scale-105"
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-white rounded-lg shadow-xl border z-50">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 rounded-t-lg flex justify-between items-center">
        <div>
          <h3 className="font-semibold">Voice Assistant</h3>
          <div className={`text-sm px-2 py-1 rounded-full ${getStateColor()}`}>
            {getStateText()}
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(false)}
          className="text-white hover:text-gray-200"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Conversation History */}
      <div className="h-64 overflow-y-auto p-4 bg-gray-50">
        {conversationHistory.map((message) => (
          <div
            key={message.id}
            className={`mb-3 ${
              message.sender === 'user' ? 'text-right' : 'text-left'
            }`}
          >
            <div
              className={`inline-block p-2 rounded-lg max-w-xs ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border'
              }`}
            >
              <div className="text-sm">{message.message}</div>
              <div className="text-xs opacity-70 mt-1">{message.timestamp}</div>
            </div>
          </div>
        ))}
        <div ref={conversationEndRef} />
      </div>

      {/* Current Transcript */}
      {currentTranscript && (
        <div className="px-4 py-2 bg-gray-100 border-t">
          <div className="text-sm text-gray-600">
            <span className="font-semibold">Hearing: </span>
            {currentTranscript}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="p-4 border-t bg-white rounded-b-lg">
        <div className="flex justify-center space-x-4">
          <button
            onClick={toggleListening}
            disabled={assistantState === 'error'}
            className={`p-3 rounded-full transition-all duration-200 ${
              isListening
                ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
            } ${assistantState === 'error' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
          
          <button
            onClick={toggleSpeaking}
            className={`p-3 rounded-full transition-all duration-200 ${
              isSpeaking
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
            }`}
          >
            {isSpeaking ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
          </button>
          
          <button
            onClick={clearConversation}
            className="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-full transition-all duration-200"
          >
            Clear
          </button>
        </div>
        
        <div className="mt-3 text-center">
          <p className="text-xs text-gray-500 mb-1">
            Try these voice commands:
          </p>
          <div className="text-xs text-gray-400 space-y-1">
            <div>"Show me total hours" • "Who worked at Blue Ash?"</div>
            <div>"Get top volunteers" • "List all branches"</div>
            <div>"Jane Smith's projects" • "Recent activity"</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistant;