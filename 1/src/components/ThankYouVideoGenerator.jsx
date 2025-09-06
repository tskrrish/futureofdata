import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Video, Download, Play, Pause, User, Clock, Award } from 'lucide-react';

export function ThankYouVideoGenerator({ volunteerData, leaderboard, badges }) {
  const canvasRef = useRef(null);
  const [selectedVolunteer, setSelectedVolunteer] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [videoBlob, setVideoBlob] = useState(null);
  
  const volunteers = leaderboard?.map(v => v.assignee) || [];
  
  const getVolunteerMetrics = useCallback((volunteerName) => {
    if (!volunteerName || !volunteerData) return null;
    
    const volunteerRecords = volunteerData.filter(r => 
      (r.assignee || '').toLowerCase() === volunteerName.toLowerCase()
    );
    
    if (volunteerRecords.length === 0) return null;
    
    const totalHours = volunteerRecords.reduce((acc, r) => acc + (Number(r.hours) || 0), 0);
    const branches = [...new Set(volunteerRecords.map(r => r.branch))];
    const projects = [...new Set(volunteerRecords.map(r => r.project))];
    const isMember = volunteerRecords.some(r => r.is_member);
    const mostRecentDate = volunteerRecords.reduce((latest, r) => {
      const date = new Date(r.date);
      return date > new Date(latest) ? r.date : latest;
    }, volunteerRecords[0].date);
    
    const volunteerBadges = badges?.find(b => b.assignee === volunteerName)?.badges || [];
    const rank = leaderboard?.findIndex(l => l.assignee === volunteerName) + 1 || 0;
    
    return {
      name: volunteerName,
      totalHours: Number(totalHours.toFixed(1)),
      branches: branches.length,
      branchNames: branches,
      projects: projects.length,
      isMember,
      mostRecentDate,
      badges: volunteerBadges,
      rank,
      recentActivity: volunteerRecords.slice(-3)
    };
  }, [volunteerData, badges, leaderboard]);

  const drawFrame = (ctx, frameNumber, metrics) => {
    const canvas = ctx.canvas;
    const { width, height } = canvas;
    
    // Clear canvas
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, width, height);
    
    // YMCA Brand colors
    const primaryColor = '#e11d48';
    const secondaryColor = '#1e293b';
    const accentColor = '#0ea5e9';
    
    // Animation progress (0-1)
    const progress = Math.min(frameNumber / 120, 1);
    const slideProgress = Math.max(0, (frameNumber - 30) / 90);
    
    // Background gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#f8fafc');
    gradient.addColorStop(1, '#e2e8f0');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // YMCA Logo area
    ctx.fillStyle = primaryColor;
    ctx.fillRect(0, 0, width, 80);
    
    // YMCA Text
    ctx.fillStyle = 'white';
    ctx.font = 'bold 28px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('YMCA of Greater Cincinnati', width / 2, 45);
    
    // Thank you header
    ctx.fillStyle = secondaryColor;
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    const headerY = 140 + (progress * 0);
    ctx.fillText('Thank You, ' + metrics.name + '!', width / 2, headerY);
    
    // Impact metrics section
    if (slideProgress > 0) {
      const metricsY = 200;
      const slideOffset = (1 - slideProgress) * 100;
      
      // Hours card
      ctx.fillStyle = 'white';
      ctx.shadowColor = 'rgba(0,0,0,0.1)';
      ctx.shadowBlur = 10;
      ctx.fillRect(50 - slideOffset, metricsY, 140, 100);
      ctx.shadowBlur = 0;
      
      ctx.fillStyle = accentColor;
      ctx.font = 'bold 32px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(metrics.totalHours.toString(), 120 - slideOffset, metricsY + 45);
      
      ctx.fillStyle = secondaryColor;
      ctx.font = '16px Arial';
      ctx.fillText('Hours Volunteered', 120 - slideOffset, metricsY + 70);
      
      // Projects card
      ctx.fillStyle = 'white';
      ctx.shadowColor = 'rgba(0,0,0,0.1)';
      ctx.shadowBlur = 10;
      ctx.fillRect(210 - slideOffset, metricsY, 140, 100);
      ctx.shadowBlur = 0;
      
      ctx.fillStyle = primaryColor;
      ctx.font = 'bold 32px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(metrics.projects.toString(), 280 - slideOffset, metricsY + 45);
      
      ctx.fillStyle = secondaryColor;
      ctx.font = '16px Arial';
      ctx.fillText('Projects Supported', 280 - slideOffset, metricsY + 70);
      
      // Rank card
      ctx.fillStyle = 'white';
      ctx.shadowColor = 'rgba(0,0,0,0.1)';
      ctx.shadowBlur = 10;
      ctx.fillRect(370 - slideOffset, metricsY, 140, 100);
      ctx.shadowBlur = 0;
      
      ctx.fillStyle = '#f59e0b';
      ctx.font = 'bold 32px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('#' + metrics.rank, 440 - slideOffset, metricsY + 45);
      
      ctx.fillStyle = secondaryColor;
      ctx.font = '16px Arial';
      ctx.fillText('Volunteer Rank', 440 - slideOffset, metricsY + 70);
    }
    
    // Badges section
    if (slideProgress > 0.3 && metrics.badges.length > 0) {
      const badgeY = 340;
      const badgeSlideOffset = (1 - Math.min((slideProgress - 0.3) / 0.3, 1)) * 50;
      
      ctx.fillStyle = secondaryColor;
      ctx.font = 'bold 24px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Achievement Badges', width / 2, badgeY - badgeSlideOffset);
      
      metrics.badges.forEach((badge, index) => {
        const x = (width / 2) - (metrics.badges.length * 30) + (index * 60);
        const y = badgeY + 30 - badgeSlideOffset;
        
        // Badge circle
        ctx.fillStyle = '#fbbf24';
        ctx.beginPath();
        ctx.arc(x, y, 25, 0, 2 * Math.PI);
        ctx.fill();
        
        // Badge text
        ctx.fillStyle = secondaryColor;
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(badge + 'h', x, y + 5);
      });
    }
    
    // Branch impact
    if (slideProgress > 0.6) {
      const branchY = 450;
      const branchSlideOffset = (1 - Math.min((slideProgress - 0.6) / 0.4, 1)) * 50;
      
      ctx.fillStyle = secondaryColor;
      ctx.font = 'bold 20px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Making a difference at:', width / 2, branchY - branchSlideOffset);
      
      ctx.font = '18px Arial';
      ctx.fillStyle = primaryColor;
      const branchText = metrics.branchNames.join(', ');
      ctx.fillText(branchText, width / 2, branchY + 25 - branchSlideOffset);
    }
    
    // Closing message
    if (slideProgress > 0.8) {
      const closingY = 530;
      const closingSlideOffset = (1 - Math.min((slideProgress - 0.8) / 0.2, 1)) * 30;
      
      ctx.fillStyle = secondaryColor;
      ctx.font = 'italic 18px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('Your dedication strengthens our community', width / 2, closingY - closingSlideOffset);
      
      ctx.font = 'bold 16px Arial';
      ctx.fillStyle = primaryColor;
      ctx.fillText('Thank you for being a Champion for Youth!', width / 2, closingY + 25 - closingSlideOffset);
    }
  };

  const generateVideo = async () => {
    if (!selectedVolunteer) return;
    
    const metrics = getVolunteerMetrics(selectedVolunteer);
    if (!metrics) return;
    
    setIsGenerating(true);
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = 560;
    canvas.height = 600;
    
    // Generate frames for a 5-second video at 30fps
    const totalFrames = 150;
    const frames = [];
    
    for (let frame = 0; frame < totalFrames; frame++) {
      drawFrame(ctx, frame, metrics);
      
      // Convert canvas to blob for this frame
      const imageData = canvas.toDataURL('image/png');
      frames.push(imageData);
      
      // Update progress
      if (frame % 10 === 0) {
        setCurrentFrame(frame);
      }
    }
    
    // For demo purposes, we'll just show the final frame
    // In a real implementation, you'd use MediaRecorder or similar to create a video
    canvas.toBlob(blob => {
      setVideoBlob(blob);
      setIsGenerating(false);
    });
  };

  const downloadVideo = () => {
    if (!videoBlob) return;
    
    const url = URL.createObjectURL(videoBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `thank-you-video-${selectedVolunteer.replace(/\s+/g, '-').toLowerCase()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };


  useEffect(() => {
    if (!selectedVolunteer) return;
    
    const metrics = getVolunteerMetrics(selectedVolunteer);
    if (!metrics) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = 560;
    canvas.height = 600;
    
    let frame = 0;
    const animate = () => {
      drawFrame(ctx, frame, metrics);
      frame = (frame + 1) % 150;
      
      if (isPlaying) {
        requestAnimationFrame(animate);
      }
    };
    
    if (isPlaying) {
      animate();
    } else {
      drawFrame(ctx, 0, metrics);
    }
  }, [selectedVolunteer, isPlaying, getVolunteerMetrics]);

  return (
    <div className="bg-white rounded-lg p-6 shadow-lg">
      <div className="flex items-center gap-3 mb-6">
        <Video className="w-6 h-6 text-red-500" />
        <h2 className="text-xl font-bold text-gray-800">Thank You Video Generator</h2>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        {/* Controls */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Volunteer
            </label>
            <select
              value={selectedVolunteer}
              onChange={(e) => setSelectedVolunteer(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            >
              <option value="">Choose a volunteer...</option>
              {volunteers.map(volunteer => (
                <option key={volunteer} value={volunteer}>
                  {volunteer}
                </option>
              ))}
            </select>
          </div>
          
          {selectedVolunteer && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-2">Volunteer Impact Summary</h3>
              {(() => {
                const metrics = getVolunteerMetrics(selectedVolunteer);
                if (!metrics) return <p className="text-gray-500">No data found</p>;
                
                return (
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-blue-500" />
                      <span>{metrics.totalHours} hours volunteered</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-green-500" />
                      <span>{metrics.projects} projects, {metrics.branches} branches</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-yellow-500" />
                      <span>Rank #{metrics.rank} volunteer</span>
                    </div>
                    {metrics.badges.length > 0 && (
                      <div className="flex items-center gap-2">
                        <Award className="w-4 h-4 text-purple-500" />
                        <span>{metrics.badges.length} achievement badges</span>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              disabled={!selectedVolunteer}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {isPlaying ? 'Pause' : 'Preview'}
            </button>
            
            <button
              onClick={generateVideo}
              disabled={!selectedVolunteer || isGenerating}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              <Video className="w-4 h-4" />
              {isGenerating ? 'Generating...' : 'Generate'}
            </button>
          </div>
          
          {videoBlob && (
            <button
              onClick={downloadVideo}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              <Download className="w-4 h-4" />
              Download Video Frame
            </button>
          )}
          
          {isGenerating && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center justify-between text-sm text-blue-800">
                <span>Generating video...</span>
                <span>{Math.round((currentFrame / 150) * 100)}%</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(currentFrame / 150) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
        
        {/* Canvas Preview */}
        <div className="flex flex-col">
          <h3 className="font-semibold text-gray-800 mb-3">Video Preview</h3>
          <div className="bg-gray-100 rounded-lg p-4 flex-1 flex items-center justify-center">
            <canvas
              ref={canvasRef}
              className="max-w-full max-h-full border border-gray-300 rounded shadow-lg"
              style={{ maxHeight: '400px' }}
            />
          </div>
        </div>
      </div>
      
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-sm text-yellow-800">
          <strong>Note:</strong> This demo generates a static frame of the personalized thank-you video. 
          In a full implementation, this would create an animated video with smooth transitions and 
          motion graphics showcasing the volunteer's impact metrics.
        </p>
      </div>
    </div>
  );
}