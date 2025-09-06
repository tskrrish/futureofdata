import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

// Define badge tiers matching the volunteer tracker system
export const BADGE_TIERS = {
  legendary: {
    name: "GUIDING LIGHT",
    minHours: 500,
    rating: 99,
    color: "#FF6B35",
    description: "500+ hours of leadership"
  },
  special: {
    name: "PASSION IN ACTION",
    minHours: 100,
    rating: 89,
    color: "#1B1B1B",
    description: "100+ hours of impact"
  },
  rare: {
    name: "COMMITMENT CHAMPION",
    minHours: 50,
    rating: 84,
    color: "#FFD700",
    description: "Dedicated to service"
  },
  uncommon: {
    name: "SERVICE STAR",
    minHours: 25,
    rating: 74,
    color: "#C0C0C0",
    description: "Making a difference"
  },
  common: {
    name: "FIRST IMPACT",
    minHours: 10,
    rating: 64,
    color: "#CD7F32",
    description: "Your journey begins"
  },
  basic: {
    name: "VOLUNTEER",
    minHours: 0,
    rating: 45,
    color: "#8B4513",
    description: "Community supporter"
  }
};

export const MILESTONES = [
  { threshold: 10, label: "First Impact" },
  { threshold: 25, label: "Service Star" },
  { threshold: 50, label: "Commitment Champion" },
  { threshold: 100, label: "Passion In Action Award" },
  { threshold: 500, label: "Guiding Light Award" },
];

function getTierForHours(hours) {
  if (hours >= 500) return 'legendary';
  if (hours >= 100) return 'special';
  if (hours >= 50) return 'rare';
  if (hours >= 25) return 'uncommon';
  if (hours >= 10) return 'common';
  return 'basic';
}

function createVolunteerBadgeCanvas(volunteer) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  
  canvas.width = 800;
  canvas.height = 1000;
  
  const totalHours = volunteer.hours_total || 0;
  const tier = BADGE_TIERS[getTierForHours(totalHours)];
  
  // Create gradient background
  const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  gradient.addColorStop(0, '#1a1a2e');
  gradient.addColorStop(0.5, '#16213e');
  gradient.addColorStop(1, '#0f0f23');
  
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // Add tier-specific accent color
  ctx.fillStyle = tier.color;
  ctx.globalAlpha = 0.1;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.globalAlpha = 1;
  
  // Title
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 48px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('VOLUNTEER PASSPORT', canvas.width / 2, 80);
  
  // Rating badge
  ctx.fillStyle = tier.color;
  ctx.beginPath();
  ctx.roundRect(canvas.width / 2 - 50, 120, 100, 80, 10);
  ctx.fill();
  
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 32px Arial';
  ctx.fillText(tier.rating.toString(), canvas.width / 2, 170);
  
  // Volunteer name
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 36px Arial';
  const fullName = `${volunteer.assignee || 'Volunteer'}`;
  ctx.fillText(fullName, canvas.width / 2, 280);
  
  // Tier name
  ctx.fillStyle = tier.color;
  ctx.font = 'bold 24px Arial';
  ctx.fillText(tier.name, canvas.width / 2, 320);
  
  // Stats section
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 20px Arial';
  ctx.fillText('IMPACT SUMMARY', canvas.width / 2, 400);
  
  // Hours circle
  ctx.strokeStyle = tier.color;
  ctx.lineWidth = 8;
  ctx.beginPath();
  ctx.arc(canvas.width / 2, 480, 60, 0, 2 * Math.PI);
  ctx.stroke();
  
  ctx.fillStyle = '#00FF88';
  ctx.font = 'bold 32px Arial';
  ctx.fillText(totalHours.toString(), canvas.width / 2, 490);
  
  ctx.fillStyle = '#ffffff';
  ctx.font = '16px Arial';
  ctx.fillText('HOURS', canvas.width / 2, 510);
  
  // Additional stats
  const activities = volunteer.assignments_count || 0;
  const branches = volunteer.branch_count || 1;
  
  ctx.font = '18px Arial';
  ctx.fillText(`${activities} Activities`, canvas.width / 2 - 150, 580);
  ctx.fillText(`${branches} Branch${branches > 1 ? 'es' : ''}`, canvas.width / 2 + 150, 580);
  
  // Achievements
  const achievements = MILESTONES.filter(m => totalHours >= m.threshold);
  if (achievements.length > 0) {
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 20px Arial';
    ctx.fillText('ACHIEVEMENTS', canvas.width / 2, 650);
    
    achievements.forEach((achievement, index) => {
      ctx.fillStyle = '#00FF88';
      ctx.font = '16px Arial';
      ctx.fillText(`✓ ${achievement.label}`, canvas.width / 2, 690 + (index * 30));
    });
  }
  
  // Footer
  ctx.fillStyle = '#999999';
  ctx.font = '14px Arial';
  ctx.fillText('YMCA of Greater Cincinnati', canvas.width / 2, 920);
  ctx.fillText('BELONGING BY DESIGN', canvas.width / 2, 950);
  
  return canvas;
}

export async function exportVolunteerPassportPDF(volunteer) {
  try {
    const pdf = new jsPDF('portrait', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    
    // Create badge canvas
    const badgeCanvas = createVolunteerBadgeCanvas(volunteer);
    const badgeImg = badgeCanvas.toDataURL('image/png');
    
    // Add badge to PDF
    const imgWidth = 120;
    const imgHeight = 150;
    const imgX = (pdfWidth - imgWidth) / 2;
    const imgY = 20;
    
    pdf.addImage(badgeImg, 'PNG', imgX, imgY, imgWidth, imgHeight);
    
    // Add detailed impact summary
    const summaryY = imgY + imgHeight + 20;
    
    pdf.setFontSize(18);
    pdf.setTextColor(51, 51, 51);
    pdf.text('Detailed Impact Report', 20, summaryY);
    
    // Volunteer details
    const totalHours = volunteer.hours_total || 0;
    const tier = BADGE_TIERS[getTierForHours(totalHours)];
    const fullName = volunteer.assignee || 'Volunteer';
    
    pdf.setFontSize(12);
    pdf.setTextColor(68, 68, 68);
    
    const details = [
      `Volunteer Name: ${fullName}`,
      `Total Service Hours: ${totalHours}`,
      `Current Tier: ${tier.name}`,
      `Branch: ${volunteer.branch || 'Multiple'}`,
      `Member Status: ${volunteer.is_member ? 'YMCA Member' : 'Community Volunteer'}`,
      `Last Activity: ${volunteer.date || 'Not specified'}`
    ];
    
    details.forEach((detail, index) => {
      pdf.text(detail, 20, summaryY + 15 + (index * 8));
    });
    
    // Service areas/projects
    const projectsY = summaryY + 80;
    pdf.setFontSize(16);
    pdf.setTextColor(51, 51, 51);
    pdf.text('Service Areas', 20, projectsY);
    
    pdf.setFontSize(12);
    pdf.setTextColor(68, 68, 68);
    
    const serviceAreas = [
      volunteer.project_tag,
      volunteer.project_catalog,
      volunteer.project,
      volunteer.category
    ].filter(Boolean).filter((value, index, self) => self.indexOf(value) === index);
    
    serviceAreas.forEach((area, index) => {
      pdf.text(`• ${area}`, 20, projectsY + 15 + (index * 8));
    });
    
    // Achievements section
    const achievements = MILESTONES.filter(m => totalHours >= m.threshold);
    if (achievements.length > 0) {
      const achievementsY = projectsY + 60;
      pdf.setFontSize(16);
      pdf.setTextColor(51, 51, 51);
      pdf.text('Earned Badges & Milestones', 20, achievementsY);
      
      pdf.setFontSize(12);
      pdf.setTextColor(68, 68, 68);
      
      achievements.forEach((achievement, index) => {
        pdf.text(`✓ ${achievement.label} (${achievement.threshold}+ hours)`, 20, achievementsY + 15 + (index * 8));
      });
    }
    
    // Footer
    const footerY = pdfHeight - 20;
    pdf.setFontSize(10);
    pdf.setTextColor(153, 153, 153);
    pdf.text(`Generated on ${new Date().toLocaleDateString()}`, 20, footerY);
    pdf.text('YMCA Volunteer Passport System', pdfWidth - 20, footerY, { align: 'right' });
    
    // Generate filename
    const safeFilename = fullName.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const filename = `${safeFilename}_volunteer_passport.pdf`;
    
    pdf.save(filename);
    return true;
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw error;
  }
}

export async function exportMultipleVolunteersPDF(volunteers) {
  try {
    const pdf = new jsPDF('portrait', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    
    // Group volunteers by tier for better organization
    const volunteersByTier = volunteers.reduce((acc, volunteer) => {
      const tier = getTierForHours(volunteer.hours_total || 0);
      if (!acc[tier]) acc[tier] = [];
      acc[tier].push(volunteer);
      return acc;
    }, {});
    
    // Sort tiers by importance
    const tierOrder = ['legendary', 'special', 'rare', 'uncommon', 'common', 'basic'];
    let isFirstPage = true;
    
    for (const tierKey of tierOrder) {
      const tierVolunteers = volunteersByTier[tierKey];
      if (!tierVolunteers || tierVolunteers.length === 0) continue;
      
      if (!isFirstPage) pdf.addPage();
      isFirstPage = false;
      
      const tier = BADGE_TIERS[tierKey];
      
      // Tier header
      pdf.setFontSize(20);
      pdf.setTextColor(51, 51, 51);
      pdf.text(`${tier.name} TIER VOLUNTEERS`, pdfWidth / 2, 20, { align: 'center' });
      
      pdf.setFontSize(12);
      pdf.setTextColor(102, 102, 102);
      pdf.text(`${tier.description} (${tier.minHours}+ hours)`, pdfWidth / 2, 30, { align: 'center' });
      
      let yPos = 50;
      
      tierVolunteers.forEach((volunteer, index) => {
        if (yPos > pdfHeight - 40) {
          pdf.addPage();
          yPos = 30;
        }
        
        // Volunteer summary box
        pdf.setDrawColor(200, 200, 200);
        pdf.setLineWidth(0.5);
        pdf.rect(15, yPos - 5, pdfWidth - 30, 25);
        
        const fullName = volunteer.assignee || 'Volunteer';
        const totalHours = volunteer.hours_total || 0;
        
        pdf.setFontSize(14);
        pdf.setTextColor(51, 51, 51);
        pdf.text(fullName, 20, yPos + 5);
        
        pdf.setFontSize(10);
        pdf.setTextColor(68, 68, 68);
        pdf.text(`${totalHours} hours | ${volunteer.branch || 'Multiple branches'}`, 20, yPos + 12);
        
        // Tier rating
        pdf.setFontSize(16);
        pdf.setTextColor(tier.color === '#1B1B1B' ? 100 : parseInt(tier.color.slice(1, 3), 16), 
                         tier.color === '#1B1B1B' ? 100 : parseInt(tier.color.slice(3, 5), 16), 
                         tier.color === '#1B1B1B' ? 100 : parseInt(tier.color.slice(5, 7), 16));
        pdf.text(tier.rating.toString(), pdfWidth - 30, yPos + 8);
        
        yPos += 35;
      });
    }
    
    // Summary page
    pdf.addPage();
    
    pdf.setFontSize(20);
    pdf.setTextColor(51, 51, 51);
    pdf.text('VOLUNTEER IMPACT SUMMARY', pdfWidth / 2, 30, { align: 'center' });
    
    const totalVolunteers = volunteers.length;
    const totalHours = volunteers.reduce((sum, v) => sum + (v.hours_total || 0), 0);
    const avgHours = Math.round(totalHours / totalVolunteers);
    
    pdf.setFontSize(14);
    pdf.setTextColor(68, 68, 68);
    
    const summary = [
      `Total Volunteers: ${totalVolunteers}`,
      `Total Service Hours: ${totalHours}`,
      `Average Hours per Volunteer: ${avgHours}`,
      '',
      'Distribution by Tier:'
    ];
    
    summary.forEach((line, index) => {
      pdf.text(line, 30, 60 + (index * 10));
    });
    
    // Tier distribution
    let yPos = 120;
    tierOrder.forEach(tierKey => {
      const tierVolunteers = volunteersByTier[tierKey];
      if (tierVolunteers && tierVolunteers.length > 0) {
        const tier = BADGE_TIERS[tierKey];
        pdf.text(`• ${tier.name}: ${tierVolunteers.length} volunteers`, 40, yPos);
        yPos += 10;
      }
    });
    
    // Footer
    const footerY = pdfHeight - 20;
    pdf.setFontSize(10);
    pdf.setTextColor(153, 153, 153);
    pdf.text(`Generated on ${new Date().toLocaleDateString()}`, 20, footerY);
    pdf.text('YMCA Volunteer Recognition Report', pdfWidth - 20, footerY, { align: 'right' });
    
    const filename = `volunteer_recognition_report_${new Date().toISOString().split('T')[0]}.pdf`;
    pdf.save(filename);
    return true;
  } catch (error) {
    console.error('Error generating multi-volunteer PDF:', error);
    throw error;
  }
}