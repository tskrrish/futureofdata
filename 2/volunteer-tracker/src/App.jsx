import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import confetti from 'canvas-confetti';
import { playCheer, playDrumroll, playFanfare, playAmbientTone, playCardFlip, playMagicalSparkle } from './utils/audio.js';
import Badge from './components/Badge.jsx';
import CelebrationOverlay from './components/CelebrationOverlay.jsx';
import LanguageSelector from './components/LanguageSelector.jsx';
import { getTierForHours, MILESTONES } from './constants.js';

function App() {
  const { t, i18n } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [volunteerData, setVolunteerData] = useState(null);
  const [error, setError] = useState('');
  const firedRef = useRef(false);
  const [showOverlay, setShowOverlay] = useState(false);
  const [hideSearchBar, setHideSearchBar] = useState(false);

  useEffect(() => {
    const savedLanguage = localStorage.getItem('preferredLanguage');
    if (savedLanguage && savedLanguage !== i18n.language) {
      i18n.changeLanguage(savedLanguage);
    }
  }, [i18n]);

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
      setError(t('search.enterName'));
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
      } else {
        setError(t('search.notFound'));
      }
    } catch (e) {
      setError(t('search.serverError'));
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
            <div className="welcome-title">{t('welcome.title')}</div>
            <div className="welcome-subtitle">
              <strong>{t('welcome.subtitle')}</strong> – {t('welcome.subtitleEmphasis')}
            </div>
            <div className="welcome-story">
              {t('welcome.story')}
            </div>
            <div className="milestone-preview">
              {MILESTONES.map((milestone, index) => {
                const icons = ['🥉', '⭐', '🏆', '👕', '⭐']
                const rewards = ['', '', '', ` ${t('milestones.tshirt')}`, ` ${t('milestones.glassStar')}`]
                return (
                  <div key={milestone.label} className="milestone-tier">
                    {icons[index]} {milestone.threshold}+ {t('milestones.hours')} → {milestone.label}{rewards[index]}
                  </div>
                )
              })}
            </div>
            <div className="search-hint">{t('welcome.searchHint')}</div>
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
              placeholder={t('search.placeholder')}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="search-button" onClick={handleSearch}>
              <span>{t('search.button')}</span>
            </button>
          </div>
          {error && <div className="search-error">{error}</div>}
          <div className="language-selector-container">
            <LanguageSelector />
          </div>
        </div>
      </div>

      <CelebrationOverlay 
        show={showOverlay} 
        seed={volunteerData ? `${volunteerData.first_name}${volunteerData.last_name}` : ''} 
        tier={volunteerData ? getTierForHours(Number(volunteerData.hours_total)) : 'basic'} 
      />
    </div>
  );
}

export default App;