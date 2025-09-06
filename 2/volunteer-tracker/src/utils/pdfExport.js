import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export async function exportVolunteerPassportPDF(volunteer, badgeElementRef) {
  try {
    if (!badgeElementRef.current) {
      throw new Error('Badge element not found');
    }

    // Capture the badge as canvas
    const canvas = await html2canvas(badgeElementRef.current, {
      backgroundColor: null,
      scale: 2, // Higher resolution
      useCORS: true,
      allowTaint: true,
      scrollX: 0,
      scrollY: 0
    });

    // Create PDF with A4 dimensions
    const pdf = new jsPDF('portrait', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();

    // Add title
    pdf.setFontSize(24);
    pdf.setTextColor(51, 51, 51);
    pdf.text('Volunteer Passport', pdfWidth / 2, 20, { align: 'center' });

    // Add YMCA branding
    pdf.setFontSize(14);
    pdf.setTextColor(102, 102, 102);
    pdf.text('YMCA of Greater Cincinnati', pdfWidth / 2, 30, { align: 'center' });

    // Add volunteer badge
    const imgData = canvas.toDataURL('image/png');
    const imgWidth = 160; // Adjust size as needed
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    const imgX = (pdfWidth - imgWidth) / 2;
    const imgY = 40;

    pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth, imgHeight);

    // Calculate position for impact summary
    const summaryY = imgY + imgHeight + 20;

    // Add impact summary section
    pdf.setFontSize(18);
    pdf.setTextColor(51, 51, 51);
    pdf.text('Impact Summary', 20, summaryY);

    // Add impact details
    const totalHours = Number(volunteer.hours_total) || 0;
    const assignmentsCount = volunteer.assignments_count || 0;
    const currentYear = new Date().getFullYear();
    const startYear = volunteer.first_activity ? new Date(volunteer.first_activity).getFullYear() : currentYear;
    const yearsActive = Math.max(1, currentYear - startYear + 1);

    pdf.setFontSize(12);
    pdf.setTextColor(68, 68, 68);
    
    const impactDetails = [
      `Total Service Hours: ${totalHours}`,
      `Activities Completed: ${assignmentsCount}`,
      `Years of Service: ${yearsActive}`,
      `Member Since: ${startYear}`
    ];

    impactDetails.forEach((detail, index) => {
      pdf.text(detail, 20, summaryY + 15 + (index * 8));
    });

    // Add achievements/milestones section if volunteer has significant hours
    if (totalHours >= 10) {
      const achievementsY = summaryY + 60;
      pdf.setFontSize(18);
      pdf.setTextColor(51, 51, 51);
      pdf.text('Achievements & Badges', 20, achievementsY);

      pdf.setFontSize(12);
      pdf.setTextColor(68, 68, 68);

      const achievements = [];
      if (totalHours >= 10) achievements.push('✓ First Impact Badge (10+ hours)');
      if (totalHours >= 25) achievements.push('✓ Service Star Badge (25+ hours)');
      if (totalHours >= 50) achievements.push('✓ Commitment Champion Badge (50+ hours)');
      if (totalHours >= 100) achievements.push('✓ Passion In Action Award (100+ hours)');
      if (totalHours >= 500) achievements.push('✓ Guiding Light Award (500+ hours)');

      achievements.forEach((achievement, index) => {
        pdf.text(achievement, 20, achievementsY + 15 + (index * 8));
      });
    }

    // Add storyworlds/projects section if available
    if (volunteer.storyworlds && volunteer.storyworlds.length > 0) {
      const storyworldsY = summaryY + 120;
      pdf.setFontSize(18);
      pdf.setTextColor(51, 51, 51);
      pdf.text('Service Areas', 20, storyworldsY);

      pdf.setFontSize(12);
      pdf.setTextColor(68, 68, 68);
      
      volunteer.storyworlds.forEach((storyworld, index) => {
        pdf.text(`• ${storyworld}`, 20, storyworldsY + 15 + (index * 8));
      });
    }

    // Add footer
    const footerY = pdfHeight - 20;
    pdf.setFontSize(10);
    pdf.setTextColor(153, 153, 153);
    pdf.text('Generated on ' + new Date().toLocaleDateString(), 20, footerY);
    pdf.text('YMCA Volunteer Passport System', pdfWidth - 20, footerY, { align: 'right' });

    // Generate filename
    const fullName = `${volunteer.first_name || ''} ${volunteer.last_name || ''}`.trim() || 'volunteer';
    const filename = `${fullName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_passport.pdf`;

    // Save the PDF
    pdf.save(filename);

    return true;
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw error;
  }
}

export async function exportMultiplePassportsPDF(volunteers, badgeRefs) {
  try {
    const pdf = new jsPDF('portrait', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();

    for (let i = 0; i < volunteers.length; i++) {
      const volunteer = volunteers[i];
      const badgeRef = badgeRefs[i];

      if (i > 0) {
        pdf.addPage();
      }

      if (!badgeRef?.current) {
        continue;
      }

      const canvas = await html2canvas(badgeRef.current, {
        backgroundColor: null,
        scale: 2,
        useCORS: true,
        allowTaint: true,
        scrollX: 0,
        scrollY: 0
      });

      // Add title for each volunteer
      pdf.setFontSize(20);
      pdf.setTextColor(51, 51, 51);
      const fullName = `${volunteer.first_name || ''} ${volunteer.last_name || ''}`.trim();
      pdf.text(`${fullName} - Volunteer Passport`, pdfWidth / 2, 20, { align: 'center' });

      // Add badge
      const imgData = canvas.toDataURL('image/png');
      const imgWidth = 140;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      const imgX = (pdfWidth - imgWidth) / 2;
      const imgY = 30;

      pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth, imgHeight);

      // Add summary for each volunteer
      const summaryY = imgY + imgHeight + 15;
      const totalHours = Number(volunteer.hours_total) || 0;
      
      pdf.setFontSize(12);
      pdf.setTextColor(68, 68, 68);
      pdf.text(`Total Hours: ${totalHours} | Activities: ${volunteer.assignments_count || 0}`, 
                pdfWidth / 2, summaryY, { align: 'center' });
    }

    // Save multi-volunteer PDF
    const filename = `volunteer_passports_${new Date().toISOString().split('T')[0]}.pdf`;
    pdf.save(filename);

    return true;
  } catch (error) {
    console.error('Error generating multi-volunteer PDF:', error);
    throw error;
  }
}