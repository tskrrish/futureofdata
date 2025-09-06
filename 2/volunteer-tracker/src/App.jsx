import { useEffect, useRef, useState } from 'react';
import confetti from 'canvas-confetti';
import { playCheer, playDrumroll, playFanfare, playAmbientTone, playCardFlip, playMagicalSparkle } from './utils/audio.js';
import Badge from './components/Badge.jsx';
import CelebrationOverlay from './components/CelebrationOverlay.jsx';
import MicroCelebration from './components/MicroCelebration.jsx';
import EnhancedConfetti from './components/EnhancedConfetti.jsx';
import { getTierForHours, MILESTONES } from './constants.js';
import { microAchievementTracker } from './utils/microAchievements.js';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [volunteerData, setVolunteerData] = useState(null);
  const [error, setError] = useState('');
  const firedRef = useRef(false);
  const [showOverlay, setShowOverlay] = useState(false);
  const [hideSearchBar, setHideSearchBar] = useState(false);
  
  // Micro-celebration states
  const [microTrigger, setMicroTrigger] = useState(null);
  const [microAchievement, setMicroAchievement] = useState(null);
  const [enhancedConfettiTrigger, setEnhancedConfettiTrigger] = useState(0);

  function runFullScreenConfetti(hours) {
    const duration = Math.min(9000, 4000 + hours * 40);
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 45, spread: 360, ticks: 240, gravity: 1, zIndex: 50, scalar: 1 };

    function random(min, max) { return Math.random() * (max - min) + min }

    const interval = setInterval(function() {
      const timeLeft = animationEnd - Date.now();
      if (timeLeft <= 0) {
        clearInterval(interval);
        return;
      }
      const particleCount = Math.round(60 * (timeLeft / duration));
      confetti(Object.assign({}, defaults, { particleCount, origin: { x: random(0, 1), y: random(0, 1) } }));
      confetti(Object.assign({}, defaults, { particleCount: Math.round(particleCount / 2), angle: 60, origin: { x: 0 } }));
      confetti(Object.assign({}, defaults, { particleCount: Math.round(particleCount / 2), angle: 120, origin: { x: 1 } }));
    }, 120);
  }

  const handleSearch = async () => {
    setError('');
    setVolunteerData(null);

    if (!searchTerm.trim()) {
      setError('Please enter a name');
      return;
    }

    try {
      const response = await fetch('http://localhost:8080/volunteers?start=2024-01-01');
      if (!response.ok) throw new Error('Server error');
      
      const volunteers = await response.json();
      const searchLower = searchTerm.toLowerCase().trim();
      
      const found = volunteers.find(v => {
        const fullName = `${v.first_name} ${v.last_name}`.toLowerCase();
        return fullName.includes(searchLower) || 
               v.first_name.toLowerCase().includes(searchLower) ||
               v.last_name.toLowerCase().includes(searchLower);
      });

      if (found) {
        setVolunteerData(found);
        
        // Track the search and check for micro-achievements
        const achievements = microAchievementTracker.trackSearch(found);
        
        // Handle micro-achievements
        achievements.forEach(achievement => {
          const config = microAchievementTracker.getCelebrationConfig(achievement);
          
          if (achievement.priority === 'high' || achievement.priority === 'epic') {
            // Trigger micro-celebration popup
            setMicroAchievement(achievement);
            setMicroTrigger(achievement.type);
            
            // Enhanced confetti
            setEnhancedConfettiTrigger(prev => prev + 1);
            
            // Reset micro trigger after delay
            setTimeout(() => {
              setMicroTrigger(null);
              setMicroAchievement(null);
            }, config.duration || 3000);
          }
        });
      } else {
        setError('Volunteer not found. Try "Richard Bowman" or "Christina Burke"');
      }
    } catch (e) {
      setError('Server error - make sure backend is running on port 8080');
    }
  };

  useEffect(() => {
    if (volunteerData && !firedRef.current) {
      firedRef.current = true;
      const hours = Number(volunteerData.hours_total) || 0;
      
      // Get tier for musical theming
      const tier = getTierForHours(hours);
      
      // Hide search bar for 10 seconds
      setHideSearchBar(true);
      setTimeout(() => setHideSearchBar(false), 10000);
      
      // Check for special achievements during main celebration
      const specialAchievements = microAchievementTracker.checkAchievements(volunteerData, { 
        action: 'main_celebration' 
      });
      
      // Add delayed micro-celebrations during the main sequence
      specialAchievements.forEach((achievement, index) => {
        if (achievement.type === 'hours_milestone' || achievement.type === 'community_impact') {
          setTimeout(() => {
            setMicroAchievement(achievement);
            setMicroTrigger(achievement.type);
            setEnhancedConfettiTrigger(prev => prev + 1);
            
            const config = microAchievementTracker.getCelebrationConfig(achievement);
            setTimeout(() => {
              setMicroTrigger(null);
              setMicroAchievement(null);
            }, config.duration);
          }, 3000 + (index * 1500)); // Stagger celebrations
        }
      });
      
      // Musical sequence
      playDrumroll(600);
      setTimeout(() => playCardFlip(), 200);
      setTimeout(() => playFanfare(tier), 800);
      setTimeout(() => playAmbientTone(tier, 8000), 1200);
      if (tier === 'legendary' || tier === 'special') {
        setTimeout(() => playMagicalSparkle(), 1500);
        setTimeout(() => playMagicalSparkle(), 2000);
      }
      setTimeout(() => playCheer(700), 2500);
      
      // Visual effects
      runFullScreenConfetti(hours);
      if (hours >= 25) setShowOverlay(true);
      setTimeout(() => setShowOverlay(false), Math.min(5000, 2200 + hours * 20));
    }
    if (!volunteerData) firedRef.current = false;
  }, [volunteerData]);

  return (
    <div className="immersive-viewport">
      {/* Ambient Background */}
      <div className="ambient-bg">
        <div className="floating-particles" />
        <div className="gradient-orbs" />
      </div>

      {/* Main Card Display Area */}
      <div className="card-stage">
        {volunteerData ? (
          <div className="full-card-display">
            <Badge volunteer={volunteerData} />
          </div>
        ) : (
          <div className="welcome-state">
            <div className="welcome-title">YMCA Volunteer Recognition</div>
            <div className="welcome-subtitle">
              <strong>Belonging by Design</strong> – Building the Platform for Community
            </div>
            <div className="welcome-story">
              Powered by volunteers who strengthen intergenerational ties, improve mental health, and create employment pipelines. 
              Belonging is a public health issue – loneliness equals smoking 15 cigarettes a day. 
              Together, we're tracking belonging and impact at scale.
            </div>
            <div className="milestone-preview">
              {MILESTONES.map((milestone, index) => {
                const icons = ['🥉', '⭐', '🏆', '👕', '⭐']
                const rewards = ['', '', '', ' (T-Shirt)', ' (Glass Star)']
                return (
                  <div key={milestone.label} className="milestone-tier">
                    {icons[index]} {milestone.threshold}+ Hours → {milestone.label}{rewards[index]}
                  </div>
                )
              })}
            </div>
            <div className="search-hint">↓ Search for a volunteer below ↓</div>
          </div>
        )}
      </div>

      {/* Bottom Search Bar */}
      <div className={`bottom-search ${hideSearchBar ? 'hidden' : ''}`}>
        <div className="search-container">
          <div className="search-row">
            <input
              className="search-input"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Type volunteer name to reveal their card..."
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="search-button" onClick={handleSearch}>
              <span>🔍</span>
            </button>
          </div>
          {error && <div className="search-error">{error}</div>}
        </div>
      </div>

      <CelebrationOverlay 
        show={showOverlay} 
        seed={volunteerData ? `${volunteerData.first_name}${volunteerData.last_name}` : ''} 
        tier={volunteerData ? getTierForHours(Number(volunteerData.hours_total)) : 'basic'} 
      />

      {/* New Micro-Celebration Components */}
      <MicroCelebration 
        trigger={microTrigger}
        volunteerData={volunteerData}
        achievementType={microAchievement}
      />
      
      <EnhancedConfetti 
        trigger={enhancedConfettiTrigger}
        volunteerData={volunteerData}
        achievementType={microAchievement?.type || 'progress_celebration'}
        duration={microAchievement ? microAchievementTracker.getCelebrationConfig(microAchievement).duration : 3000}
      />
    </div>
  );
}

export default App;