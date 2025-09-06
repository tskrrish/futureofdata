import React, { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { makeRng } from '../utils/seeded.js'
import { getTierData, getStoryworldChipClass, MILESTONES } from '../constants.js'

function hashStringToNumber(input) {
  let hash = 0
  for (let i = 0; i < input.length; i++) {
    hash = (hash << 5) - hash + input.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}



export default function Badge({ volunteer }) {
  const fullName = `${volunteer.first_name} ${volunteer.last_name}`
  const seed = hashStringToNumber(fullName)
  const rng = useMemo(() => makeRng(seed), [seed])
  const accentColors = ['#111111', '#1D4ED8', '#047857', '#B45309', '#7C3AED', '#BE123C', '#0F766E']
  const accent = accentColors[seed % accentColors.length]
  const icons = ['⭐️', '❤️', '🏀', '🏊', '🎨', '🎵', '📚', '🌿', '⚽', '🐾', '🏅', '🧩', '🧭', '🧡', '🎯']
  const a = icons[seed % icons.length]
  const b = icons[(seed + 3) % icons.length]
  const c = icons[(seed + 7) % icons.length]
  const hours = Number(volunteer.hours_total) || 0
  const tierData = getTierData(hours)
  const currentYear = new Date().getFullYear()
  const startYear = volunteer.first_activity ? new Date(volunteer.first_activity).getFullYear() : currentYear
  const yearsActive = Math.max(1, currentYear - startYear + 1)

  const [counter, setCounter] = useState(0)

  useEffect(() => {
    const target = Number(volunteer.hours_total) || 0
    const durationMs = 1000 + rng() * 800
    const start = performance.now()
    let frameId
    const step = (t) => {
      const p = Math.min(1, (t - start) / durationMs)
      setCounter(Math.round(p * target))
      if (p < 1) frameId = requestAnimationFrame(step)
    }
    frameId = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frameId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [volunteer.hours_total])

  return (
    <motion.div 
      className={`fut-card fut-card-${tierData.bgPattern} ${tierData.rarity}`}
      role="img" 
      aria-label="Volunteer card"
      initial={{ 
        scale: 0.8, 
        opacity: 0,
        y: 50
      }}
      animate={{ 
        scale: 1, 
        opacity: 1,
        y: 0
      }}
      transition={{ 
        duration: 1,
        type: 'spring', 
        stiffness: 100, 
        damping: 15
      }}
      style={{ transformStyle: 'preserve-3d' }}
      whileHover={{ 
        scale: 1.05,
        rotateY: 5,
        rotateX: -5,
        transition: { duration: 0.3 }
      }}
    >
      {/* Card Background Effects */}
      <div className="card-bg-effects">
        <div className="bg-pattern" />
        <div className="shine-overlay" />
        {tierData.rarity === 'legendary' && <div className="legendary-particles" />}
        {tierData.rarity === 'special' && <div className="special-glow" />}
      </div>

      {/* Card Header */}
      <div className="card-header">
        <div className="rating" style={{ color: tierData.color }}>{tierData.rating}</div>
        <div className="tier-badge" style={{ backgroundColor: tierData.color }}>{tierData.name}</div>
        <div className="year-badge">SINCE '{String(startYear).slice(-2)}</div>
      </div>

      {/* Volunteer Photo Area */}
      <div className="photo-area">
        <div className="volunteer-avatar" style={{ backgroundColor: accent }}>
          <span className="avatar-icon">{fullName.split(' ').map(n => n[0]).join('')}</span>
        </div>
        <div className="rarity-glow" style={{ backgroundColor: tierData.color }} />
      </div>

      {/* Card Body */}
      <div className="card-body card-two-col">
        <div className="left-col">
          <div className="volunteer-name">{fullName}</div>
          <div className="position">VOLUNTEER</div>

          {/* Stats */}
          <div className="stats-grid">
          <div className="stat">
            <div className="stat-value">
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                {counter}
              </motion.span>
            </div>
            <div className="stat-label">HRS</div>
          </div>
          <div className="stat">
            <div className="stat-value">{volunteer.assignments_count || 0}</div>
            <div className="stat-label">ACT</div>
          </div>
          <div className="stat">
            <div className="stat-value">{yearsActive}</div>
            <div className="stat-label">YRS</div>
          </div>
          </div>

          {/* Custom Stamps */}
          <div className="stamps-row">
            {MILESTONES.map(milestone => 
              renderStamp(milestone.label, hours >= milestone.threshold)
            )}
          </div>
        </div>

        {/* Right Side Story Panel */}
        <div className="right-col">
          <div className="story-title">Your Storyworlds</div>
          <div className="storyworld-chips">
            {(volunteer.storyworlds || []).map((sw, i) => (
              <div key={i} className={`story-chip ${getStoryworldChipClass(sw)}`}>{sw}</div>
            ))}
          </div>
          <div className="story-subtitle">Projects</div>
          <div className="projects-list">
            {(volunteer.projects || []).slice(0, 5).map((p, i) => (
              <div key={i} className="project-item">{p}</div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="card-footer">
          <div className="club">YMCA of Greater Cincinnati</div>
          <div className="league">BELONGING BY DESIGN</div>
        </div>
      </div>
    </motion.div>
  )
}


function renderStamp(label, achieved) {
  return (
    <div className={`stamp-card ${achieved ? 'achieved' : ''}`}>
      <div className="stamp-seal" />
      <div className="stamp-label">{label}</div>
    </div>
  )
}


