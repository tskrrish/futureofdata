class VoiceAssistant {
  constructor() {
    this.isListening = false;
    this.recognition = null;
    this.speechSynthesis = null;
    this.currentVoice = null;
    this.onResultCallback = null;
    this.onStateChangeCallback = null;
    
    this.initializeSpeechRecognition();
    this.initializeSpeechSynthesis();
  }

  initializeSpeechRecognition() {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';
      
      this.recognition.onstart = () => {
        this.isListening = true;
        if (this.onStateChangeCallback) {
          this.onStateChangeCallback('listening');
        }
      };
      
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (this.onResultCallback) {
          this.onResultCallback(transcript);
        }
      };
      
      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        this.isListening = false;
        if (this.onStateChangeCallback) {
          this.onStateChangeCallback('error', event.error);
        }
      };
      
      this.recognition.onend = () => {
        this.isListening = false;
        if (this.onStateChangeCallback) {
          this.onStateChangeCallback('idle');
        }
      };
    }
  }

  initializeSpeechSynthesis() {
    if ('speechSynthesis' in window) {
      this.speechSynthesis = window.speechSynthesis;
      
      // Wait for voices to be loaded
      const setVoice = () => {
        const voices = this.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
          voice.lang.includes('en-US') && voice.name.includes('Female')
        ) || voices.find(voice => voice.lang.includes('en-US')) || voices[0];
        
        this.currentVoice = preferredVoice;
      };
      
      if (this.speechSynthesis.getVoices().length > 0) {
        setVoice();
      } else {
        this.speechSynthesis.addEventListener('voiceschanged', setVoice);
      }
    }
  }

  startListening() {
    if (this.recognition && !this.isListening) {
      this.recognition.start();
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }

  speak(text, options = {}) {
    if (!this.speechSynthesis) return;

    // Stop any current speech
    this.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = this.currentVoice;
    utterance.rate = options.rate || 0.9;
    utterance.pitch = options.pitch || 1.0;
    utterance.volume = options.volume || 1.0;

    if (options.onStart) utterance.onstart = options.onStart;
    if (options.onEnd) utterance.onend = options.onEnd;
    if (options.onError) utterance.onerror = options.onError;

    this.speechSynthesis.speak(utterance);
  }

  stopSpeaking() {
    if (this.speechSynthesis) {
      this.speechSynthesis.cancel();
    }
  }

  onResult(callback) {
    this.onResultCallback = callback;
  }

  onStateChange(callback) {
    this.onStateChangeCallback = callback;
  }

  isSupported() {
    return Boolean(
      ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) &&
      'speechSynthesis' in window
    );
  }
}

export default VoiceAssistant;