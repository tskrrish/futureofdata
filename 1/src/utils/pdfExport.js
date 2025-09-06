import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

// YMCA Brand Colors
const BRAND_COLORS = {
  primary: '#E31837',    // YMCA Red
  secondary: '#00A651',  // YMCA Green  
  accent: '#0072CE',     // YMCA Blue
  dark: '#1A1A1A',
  light: '#F8F9FA',
  gray: '#6C757D'
};

class BoardPDFExporter {
  constructor() {
    this.doc = null;
    this.currentY = 0;
    this.pageHeight = 280; // A4 height in mm minus margins
    this.pageWidth = 210;  // A4 width in mm
    this.margin = 20;
  }

  // Initialize PDF document with YMCA branding
  initializeDoc() {
    this.doc = new jsPDF('p', 'mm', 'a4');
    this.currentY = this.margin;
    
    // Set default font
    this.doc.setFont('helvetica');
  }

  // Add YMCA header with branding
  addBrandedHeader(title, subtitle = '') {
    // YMCA Logo placeholder (red rectangle)
    this.doc.setFillColor(227, 24, 55); // YMCA Red
    this.doc.rect(this.margin, this.currentY, 40, 10, 'F');
    
    // YMCA text
    this.doc.setTextColor(255, 255, 255);
    this.doc.setFontSize(14);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text('YMCA', this.margin + 20, this.currentY + 7, { align: 'center' });
    
    // Title
    this.doc.setTextColor(26, 26, 26);
    this.doc.setFontSize(20);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(title, this.margin + 50, this.currentY + 7);
    
    if (subtitle) {
      this.doc.setFontSize(12);
      this.doc.setFont('helvetica', 'normal');
      this.doc.setTextColor(108, 117, 125);
      this.doc.text(subtitle, this.margin + 50, this.currentY + 15);
    }
    
    this.currentY += 25;
    
    // Add separator line
    this.doc.setDrawColor(227, 24, 55);
    this.doc.setLineWidth(0.5);
    this.doc.line(this.margin, this.currentY, this.pageWidth - this.margin, this.currentY);
    this.currentY += 10;
  }

  // Add footer with YMCA branding
  addBrandedFooter(pageNum = 1, totalPages = 1) {
    const footerY = this.pageHeight + this.margin - 10;
    
    // Footer line
    this.doc.setDrawColor(227, 24, 55);
    this.doc.setLineWidth(0.5);
    this.doc.line(this.margin, footerY - 5, this.pageWidth - this.margin, footerY - 5);
    
    // YMCA Cincinnati branding
    this.doc.setTextColor(108, 117, 125);
    this.doc.setFontSize(9);
    this.doc.setFont('helvetica', 'normal');
    this.doc.text('YMCA of Greater Cincinnati', this.margin, footerY);
    
    // Page numbers
    this.doc.text(`Page ${pageNum} of ${totalPages}`, this.pageWidth - this.margin, footerY, { align: 'right' });
    
    // Generation timestamp
    const timestamp = new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    this.doc.text(`Generated: ${timestamp}`, this.pageWidth / 2, footerY, { align: 'center' });
  }

  // Check if we need a new page
  checkPageBreak(additionalHeight = 20) {
    if (this.currentY + additionalHeight > this.pageHeight) {
      this.addBrandedFooter();
      this.doc.addPage();
      this.currentY = this.margin + 15; // Account for reduced header on subsequent pages
      return true;
    }
    return false;
  }

  // Add section header
  addSectionHeader(title, narrative = '') {
    this.checkPageBreak(30);
    
    // Section background
    this.doc.setFillColor(248, 249, 250);
    this.doc.rect(this.margin, this.currentY, this.pageWidth - 2 * this.margin, 15, 'F');
    
    // Section title
    this.doc.setTextColor(26, 26, 26);
    this.doc.setFontSize(14);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text(title, this.margin + 5, this.currentY + 10);
    
    this.currentY += 20;
    
    // Add narrative if provided
    if (narrative) {
      this.addNarrative(narrative);
    }
  }

  // Add narrative text
  addNarrative(text, isHighlight = false) {
    this.checkPageBreak(15);
    
    if (isHighlight) {
      // Highlight box for key insights
      this.doc.setFillColor(0, 166, 81, 0.1); // Light green background
      this.doc.rect(this.margin, this.currentY, this.pageWidth - 2 * this.margin, 12, 'F');
      this.doc.setDrawColor(0, 166, 81);
      this.doc.setLineWidth(0.5);
      this.doc.rect(this.margin, this.currentY, this.pageWidth - 2 * this.margin, 12);
    }
    
    this.doc.setTextColor(26, 26, 26);
    this.doc.setFontSize(10);
    this.doc.setFont('helvetica', isHighlight ? 'bold' : 'normal');
    
    // Split text for proper wrapping
    const maxWidth = this.pageWidth - 2 * this.margin - 10;
    const lines = this.doc.splitTextToSize(text, maxWidth);
    
    const lineHeight = 5;
    lines.forEach((line, index) => {
      if (index > 0) this.checkPageBreak(lineHeight);
      this.doc.text(line, this.margin + 5, this.currentY + 7);
      if (index < lines.length - 1) this.currentY += lineHeight;
    });
    
    this.currentY += 15;
  }

  // Add KPI cards
  addKPISection(kpis) {
    this.addSectionHeader('Key Performance Indicators', 
      'These metrics provide a high-level overview of volunteer engagement and impact across all YMCA programs and branches.');
    
    const cardWidth = (this.pageWidth - 2 * this.margin - 10) / 2;
    const cardHeight = 20;
    let xOffset = this.margin;
    let cardsInRow = 0;
    
    kpis.forEach((kpi, index) => {
      if (cardsInRow === 2) {
        this.currentY += cardHeight + 5;
        this.checkPageBreak(cardHeight + 10);
        xOffset = this.margin;
        cardsInRow = 0;
      }
      
      // KPI Card background
      this.doc.setFillColor(255, 255, 255);
      this.doc.rect(xOffset, this.currentY, cardWidth, cardHeight, 'F');
      this.doc.setDrawColor(227, 24, 55);
      this.doc.setLineWidth(0.5);
      this.doc.rect(xOffset, this.currentY, cardWidth, cardHeight);
      
      // KPI Value
      this.doc.setTextColor(227, 24, 55);
      this.doc.setFontSize(18);
      this.doc.setFont('helvetica', 'bold');
      this.doc.text(kpi.value, xOffset + 5, this.currentY + 10);
      
      // KPI Label
      this.doc.setTextColor(26, 26, 26);
      this.doc.setFontSize(10);
      this.doc.setFont('helvetica', 'normal');
      this.doc.text(kpi.label, xOffset + 5, this.currentY + 16);
      
      xOffset += cardWidth + 5;
      cardsInRow++;
    });
    
    this.currentY += cardHeight + 15;
  }

  // Add data table
  addDataTable(headers, rows, title = '') {
    if (title) {
      this.addSectionHeader(title);
    }
    
    this.checkPageBreak(40);
    
    const colWidth = (this.pageWidth - 2 * this.margin) / headers.length;
    const rowHeight = 8;
    
    // Table headers
    this.doc.setFillColor(227, 24, 55);
    this.doc.rect(this.margin, this.currentY, this.pageWidth - 2 * this.margin, rowHeight, 'F');
    
    this.doc.setTextColor(255, 255, 255);
    this.doc.setFontSize(10);
    this.doc.setFont('helvetica', 'bold');
    
    headers.forEach((header, index) => {
      this.doc.text(header, this.margin + (index * colWidth) + 2, this.currentY + 6);
    });
    
    this.currentY += rowHeight;
    
    // Table rows
    rows.forEach((row, rowIndex) => {
      this.checkPageBreak(rowHeight + 5);
      
      // Alternating row colors
      if (rowIndex % 2 === 0) {
        this.doc.setFillColor(248, 249, 250);
        this.doc.rect(this.margin, this.currentY, this.pageWidth - 2 * this.margin, rowHeight, 'F');
      }
      
      this.doc.setTextColor(26, 26, 26);
      this.doc.setFontSize(9);
      this.doc.setFont('helvetica', 'normal');
      
      row.forEach((cell, cellIndex) => {
        this.doc.text(String(cell), this.margin + (cellIndex * colWidth) + 2, this.currentY + 6);
      });
      
      this.currentY += rowHeight;
    });
    
    this.currentY += 10;
  }

  // Generate narrative insights
  generateInsights(data) {
    const insights = [];
    
    // Total Impact
    insights.push({
      title: 'Volunteer Impact Summary',
      text: `Our volunteer community contributed ${data.totalHours} hours across ${data.activeVolunteersCount} active volunteers. This represents tremendous community engagement and demonstrates the strong commitment to YMCA's mission of building healthy communities.`,
      highlight: true
    });
    
    // Membership engagement
    const membershipRate = ((data.memberVolunteersCount / data.activeVolunteersCount) * 100).toFixed(1);
    if (membershipRate > 60) {
      insights.push({
        title: 'Strong Member Engagement',
        text: `${membershipRate}% of our volunteers are YMCA members, indicating strong internal community engagement and loyalty to our organization's mission.`
      });
    } else if (membershipRate < 40) {
      insights.push({
        title: 'Growth Opportunity',
        text: `${membershipRate}% of volunteers are currently YMCA members. This presents an opportunity to strengthen member engagement and potentially convert community volunteers to members.`
      });
    }
    
    // Branch performance
    if (data.hoursByBranch.length > 0) {
      const topBranch = data.hoursByBranch[0];
      const topPercentage = ((topBranch.hours / data.totalHours) * 100).toFixed(1);
      insights.push({
        title: 'Leading Branch Performance',
        text: `${topBranch.branch} leads volunteer engagement with ${topBranch.hours} hours (${topPercentage}% of total), showcasing exceptional community involvement and program effectiveness.`
      });
    }
    
    // Youth Development Impact
    if (data.ydeStats) {
      const ydeHours = data.ydeStats.reduce((acc, stat) => acc + stat.hours, 0);
      const ydePercentage = ((ydeHours / data.totalHours) * 100).toFixed(1);
      if (ydeHours > 0) {
        insights.push({
          title: 'Youth Development Excellence',
          text: `Youth Development & Education programs generated ${ydeHours} volunteer hours (${ydePercentage}% of total), reflecting our strong commitment to nurturing the next generation.`
        });
      }
    }
    
    // High-impact volunteers
    const dedicatedVolunteers = data.leaderboard.filter(v => v.hours >= 50).length;
    if (dedicatedVolunteers > 0) {
      insights.push({
        title: 'Volunteer Champions',
        text: `${dedicatedVolunteers} volunteers contributed 50+ hours each, representing our most dedicated community champions who embody the YMCA spirit of service.`
      });
    }
    
    return insights;
  }

  // Main export function for board report
  async exportBoardReport(data, options = {}) {
    const {
      title = 'YMCA Volunteer Impact Report',
      subtitle = 'Board Executive Summary',
      includeDetails = true
    } = options;
    
    this.initializeDoc();
    this.addBrandedHeader(title, subtitle);
    
    // Generate and add insights
    const insights = this.generateInsights(data);
    
    // Executive Summary
    this.addSectionHeader('Executive Summary');
    insights.forEach(insight => {
      if (insight.title) {
        this.doc.setTextColor(227, 24, 55);
        this.doc.setFontSize(11);
        this.doc.setFont('helvetica', 'bold');
        this.doc.text(insight.title, this.margin, this.currentY);
        this.currentY += 8;
      }
      this.addNarrative(insight.text, insight.highlight);
    });
    
    // KPI Section
    const kpis = [
      { label: 'Total Volunteer Hours', value: data.totalHours.toFixed(1) },
      { label: 'Active Volunteers', value: data.activeVolunteersCount.toString() },
      { label: 'Member Volunteers', value: data.memberVolunteersCount.toString() },
      { label: 'Avg Hours/Volunteer', value: (data.totalHours / Math.max(data.activeVolunteersCount, 1)).toFixed(1) }
    ];
    
    this.addKPISection(kpis);
    
    if (includeDetails) {
      // Branch Performance
      this.addDataTable(
        ['Branch', 'Hours', 'Active Volunteers'],
        data.hoursByBranch.slice(0, 10).map(item => [
          item.branch,
          item.hours.toFixed(1),
          data.activesByBranch.find(a => a.branch === item.branch)?.active || 0
        ]),
        'Branch Performance Overview'
      );
      
      this.addNarrative('This table shows the top-performing branches by volunteer hours, providing insight into community engagement levels across different locations.');
      
      // Top Volunteers
      this.addDataTable(
        ['Volunteer', 'Hours Contributed'],
        data.leaderboard.slice(0, 10).map(item => [
          item.assignee,
          item.hours.toFixed(1)
        ]),
        'Top Volunteer Contributors'
      );
      
      this.addNarrative('These volunteers represent our most dedicated community members, contributing significant time to advance YMCA programs and services.');
      
      // YDE Impact if available
      if (data.ydeStats && data.ydeStats.length > 0) {
        this.addDataTable(
          ['Program Category', 'Hours', 'Volunteers', 'Projects'],
          data.ydeStats.map(item => [
            item.category,
            item.hours.toFixed(1),
            item.volunteers.toString(),
            item.projects.toString()
          ]),
          'Youth Development & Education Impact'
        );
        
        this.addNarrative('Youth Development & Education programs are fundamental to our mission of nurturing potential in children and teens. These metrics demonstrate our impact in building tomorrow\'s leaders.');
      }
    }
    
    // Final recommendations
    this.addSectionHeader('Strategic Recommendations');
    this.addNarrative('Based on this volunteer engagement analysis, we recommend: 1) Expanding successful programs in top-performing branches, 2) Implementing member recruitment strategies where engagement is lower, 3) Recognizing and retaining high-impact volunteers through appreciation programs, 4) Sharing best practices from leading branches across the network.', true);
    
    // Add footer to final page
    this.addBrandedFooter(1, 1);
    
    return this.doc;
  }

  // Export current report
  async exportCurrentReport(data, filename = 'ymca-volunteer-report.pdf') {
    const doc = await this.exportBoardReport(data);
    doc.save(filename);
  }
}

export const pdfExporter = new BoardPDFExporter();

// Export function for easy use in components
export const exportToBoardPDF = async (data, options = {}) => {
  const filename = options.filename || `ymca-board-report-${new Date().toISOString().split('T')[0]}.pdf`;
  return await pdfExporter.exportCurrentReport(data, filename);
};