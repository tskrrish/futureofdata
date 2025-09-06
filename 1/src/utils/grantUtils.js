// Utility functions for grant reporting templates

// Calculate economic impact value based on volunteer hours
// Using Independent Sector's 2024 estimate of $33.49/hour for volunteer time value
const VOLUNTEER_HOUR_VALUE = 33.49;

export function prefillTemplateData(template, volunteerData) {
  const { 
    totalHours, 
    activeVolunteersCount, 
    memberVolunteersCount,
    hoursByBranch,
    raw
  } = volunteerData;

  // Helper functions to generate auto-prefilled content
  const autoPrefillMap = {
    'auto:total_volunteers': () => activeVolunteersCount.toString(),
    'auto:total_hours': () => totalHours.toFixed(1),
    'auto:member_volunteers': () => memberVolunteersCount.toString(),
    'auto:member_percentage': () => `${((memberVolunteersCount / Math.max(activeVolunteersCount, 1)) * 100).toFixed(1)}%`,
    'auto:economic_value': () => (totalHours * VOLUNTEER_HOUR_VALUE).toFixed(0),
    
    'auto:hours_by_branch': () => {
      return hoursByBranch.map(branch => 
        `${branch.branch}: ${branch.hours.toFixed(1)} hours`
      ).join('\n');
    },
    
    'auto:branches_list': () => {
      return hoursByBranch.map(branch => branch.branch).join(', ');
    },
    
    'auto:programs_list': () => {
      const programs = [...new Set(raw.map(item => item.project_catalog).filter(Boolean))];
      return programs.length > 0 ? programs.join(', ') : 'Various YMCA programs and services';
    },
    
    'auto:projects_list': () => {
      const projects = [...new Set(raw.map(item => item.project).filter(Boolean))];
      return projects.length > 0 ? projects.join(', ') : 'Community service projects and volunteer activities';
    },
    
    'auto:volunteer_summary': () => {
      return `During this reporting period, ${activeVolunteersCount} volunteers contributed ${totalHours.toFixed(1)} hours of service across ${hoursByBranch.length} YMCA locations. ${memberVolunteersCount} volunteers (${((memberVolunteersCount / Math.max(activeVolunteersCount, 1)) * 100).toFixed(1)}%) were YMCA members, demonstrating strong community engagement within our membership base.`;
    }
  };

  // Create prefilled template with actual data
  const prefilledTemplate = {
    ...template,
    fields: template.fields.map(field => {
      let prefilledValue = field.prefill;
      
      // Check if this is an auto-prefill field
      if (typeof prefilledValue === 'string' && prefilledValue.startsWith('auto:')) {
        const autoFillFunction = autoPrefillMap[prefilledValue];
        if (autoFillFunction) {
          prefilledValue = autoFillFunction();
        }
      }
      
      return {
        ...field,
        value: prefilledValue || ''
      };
    })
  };

  return prefilledTemplate;
}

export function exportTemplateAsText(templateData, formValues) {
  let output = `${templateData.name} - ${templateData.description}\n`;
  output += '='.repeat(output.length - 1) + '\n\n';
  
  templateData.fields.forEach(field => {
    const value = formValues[field.id] || field.value || '';
    output += `${field.label}:\n`;
    output += `${value}\n\n`;
  });
  
  output += `Generated on: ${new Date().toLocaleDateString()}\n`;
  
  return output;
}

export function exportTemplateAsCSV(templateData, formValues) {
  const headers = ['Field', 'Value'];
  const rows = templateData.fields.map(field => [
    field.label,
    formValues[field.id] || field.value || ''
  ]);
  
  // Add metadata
  rows.unshift(['Template Name', templateData.name]);
  rows.unshift(['Description', templateData.description]);
  rows.unshift(['Generated Date', new Date().toLocaleDateString()]);
  rows.unshift(['', '']); // Empty row for spacing
  
  const csvContent = [headers, ...rows]
    .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\n');
    
  return csvContent;
}