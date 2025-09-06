import { AUDIO_CONFIG } from '../constants.js'

let ctx
function getCtx() {
  if (ctx) return ctx
  const AudioContext = window.AudioContext || window.webkitAudioContext
  ctx = new AudioContext()
  return ctx
}

export function playCheer(durationMs = 700) {
  const c = getCtx()
  const bufferSize = c.sampleRate * (durationMs / 1000)
  const buffer = c.createBuffer(1, bufferSize, c.sampleRate)
  const data = buffer.getChannelData(0)
  for (let i = 0; i < buffer.length; i++) data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (buffer.length / 2))
  const noise = c.createBufferSource()
  noise.buffer = buffer
  const gain = c.createGain()
  gain.gain.value = 0.3
  noise.connect(gain).connect(c.destination)
  noise.start()
}

export function playDrumroll(durationMs = 800) {
  const c = getCtx()
  const osc = c.createOscillator()
  const gain = c.createGain()
  osc.type = 'triangle'
  osc.frequency.setValueAtTime(120, c.currentTime)
  osc.frequency.exponentialRampToValueAtTime(40, c.currentTime + durationMs / 1000)
  gain.gain.value = 0.0001
  gain.gain.exponentialRampToValueAtTime(0.2, c.currentTime + 0.1)
  gain.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + durationMs / 1000)
  osc.connect(gain).connect(c.destination)
  osc.start()
  osc.stop(c.currentTime + durationMs / 1000)
}

export function playFanfare(tier = 'basic') {
  const c = getCtx()
  const now = c.currentTime
  
  const notes = AUDIO_CONFIG.fanfare[tier] || AUDIO_CONFIG.fanfare.basic
  const duration = tier === 'legendary' ? 2.5 : tier === 'special' ? 2 : 1.5
  
  notes.forEach((freq, i) => {
    const osc = c.createOscillator()
    const gain = c.createGain()
    
    osc.type = tier === 'legendary' ? 'sawtooth' : tier === 'special' ? 'square' : 'sine'
    osc.frequency.setValueAtTime(freq, now + i * 0.15)
    
    gain.gain.setValueAtTime(0, now + i * 0.15)
    gain.gain.linearRampToValueAtTime(0.3, now + i * 0.15 + 0.05)
    gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.15 + 0.4)
    
    osc.connect(gain).connect(c.destination)
    osc.start(now + i * 0.15)
    osc.stop(now + i * 0.15 + 0.4)
  })
}

export function playAmbientTone(tier = 'basic', duration = 3000) {
  const c = getCtx()
  const now = c.currentTime
  
  const freqs = AUDIO_CONFIG.ambient[tier] || AUDIO_CONFIG.ambient.basic
  
  freqs.forEach((freq, i) => {
    const osc = c.createOscillator()
    const gain = c.createGain()
    
    osc.type = 'sine'
    osc.frequency.setValueAtTime(freq, now)
    osc.frequency.linearRampToValueAtTime(freq * 1.05, now + duration / 2000)
    osc.frequency.linearRampToValueAtTime(freq, now + duration / 1000)
    
    gain.gain.setValueAtTime(0, now)
    gain.gain.linearRampToValueAtTime(0.1 / (i + 1), now + 0.5)
    gain.gain.linearRampToValueAtTime(0.05 / (i + 1), now + duration / 1000 - 0.5)
    gain.gain.linearRampToValueAtTime(0, now + duration / 1000)
    
    osc.connect(gain).connect(c.destination)
    osc.start(now)
    osc.stop(now + duration / 1000)
  })
}

export function playCardFlip() {
  const c = getCtx()
  const now = c.currentTime
  
  // Quick whoosh sound for card flip
  const osc = c.createOscillator()
  const gain = c.createGain()
  
  osc.type = 'sawtooth'
  osc.frequency.setValueAtTime(800, now)
  osc.frequency.exponentialRampToValueAtTime(200, now + 0.3)
  
  gain.gain.setValueAtTime(0.2, now)
  gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3)
  
  osc.connect(gain).connect(c.destination)
  osc.start(now)
  osc.stop(now + 0.3)
}

export function playMagicalSparkle() {
  const c = getCtx()
  const now = c.currentTime
  
  // Sparkly magical sound
  for (let i = 0; i < 8; i++) {
    const osc = c.createOscillator()
    const gain = c.createGain()
    
    const freq = 800 + Math.random() * 1200
    const startTime = now + i * 0.08
    
    osc.type = 'sine'
    osc.frequency.setValueAtTime(freq, startTime)
    osc.frequency.exponentialRampToValueAtTime(freq * 2, startTime + 0.15)
    
    gain.gain.setValueAtTime(0.15, startTime)
    gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.15)
    
    osc.connect(gain).connect(c.destination)
    osc.start(startTime)
    osc.stop(startTime + 0.15)
  }
}


