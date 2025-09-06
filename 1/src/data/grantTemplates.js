// Grant reporting templates for common funders
export const GRANT_TEMPLATES = {
  united_way: {
    id: 'united_way',
    name: 'United Way',
    description: 'United Way Community Impact Report',
    fields: [
      {
        id: 'organization_name',
        label: 'Organization Name',
        type: 'text',
        prefill: 'YMCA Cincinnati',
        required: true
      },
      {
        id: 'reporting_period',
        label: 'Reporting Period',
        type: 'text',
        prefill: '',
        required: true
      },
      {
        id: 'total_volunteers',
        label: 'Total Number of Volunteers',
        type: 'number',
        prefill: 'auto:total_volunteers',
        required: true
      },
      {
        id: 'total_volunteer_hours',
        label: 'Total Volunteer Hours',
        type: 'number',
        prefill: 'auto:total_hours',
        required: true
      },
      {
        id: 'member_volunteers',
        label: 'YMCA Member Volunteers',
        type: 'number',
        prefill: 'auto:member_volunteers',
        required: true
      },
      {
        id: 'programs_served',
        label: 'Programs/Services Supported',
        type: 'textarea',
        prefill: 'auto:programs_list',
        required: true
      },
      {
        id: 'community_impact',
        label: 'Community Impact Description',
        type: 'textarea',
        prefill: '',
        required: true
      }
    ]
  },
  
  federal_grant: {
    id: 'federal_grant',
    name: 'Federal Grant',
    description: 'Federal Grant Performance Report',
    fields: [
      {
        id: 'grant_number',
        label: 'Grant Number',
        type: 'text',
        prefill: '',
        required: true
      },
      {
        id: 'grantee_name',
        label: 'Grantee Organization',
        type: 'text',
        prefill: 'YMCA Cincinnati',
        required: true
      },
      {
        id: 'reporting_period_start',
        label: 'Reporting Period Start Date',
        type: 'date',
        prefill: '',
        required: true
      },
      {
        id: 'reporting_period_end',
        label: 'Reporting Period End Date',
        type: 'date',
        prefill: '',
        required: true
      },
      {
        id: 'volunteer_count',
        label: 'Number of Volunteers Engaged',
        type: 'number',
        prefill: 'auto:total_volunteers',
        required: true
      },
      {
        id: 'volunteer_hours_total',
        label: 'Total Volunteer Service Hours',
        type: 'number',
        prefill: 'auto:total_hours',
        required: true
      },
      {
        id: 'volunteer_hours_by_location',
        label: 'Volunteer Hours by Location',
        type: 'textarea',
        prefill: 'auto:hours_by_branch',
        required: true
      },
      {
        id: 'performance_metrics',
        label: 'Key Performance Indicators',
        type: 'textarea',
        prefill: '',
        required: true
      }
    ]
  },

  foundation_grant: {
    id: 'foundation_grant',
    name: 'Foundation Grant',
    description: 'Private Foundation Grant Report',
    fields: [
      {
        id: 'foundation_name',
        label: 'Foundation Name',
        type: 'text',
        prefill: '',
        required: true
      },
      {
        id: 'organization_name',
        label: 'Organization Name',
        type: 'text',
        prefill: 'YMCA Cincinnati',
        required: true
      },
      {
        id: 'grant_period',
        label: 'Grant Period',
        type: 'text',
        prefill: '',
        required: true
      },
      {
        id: 'volunteer_engagement',
        label: 'Volunteer Engagement Summary',
        type: 'textarea',
        prefill: 'auto:volunteer_summary',
        required: true
      },
      {
        id: 'total_volunteers_served',
        label: 'Total Volunteers Served',
        type: 'number',
        prefill: 'auto:total_volunteers',
        required: true
      },
      {
        id: 'service_hours_delivered',
        label: 'Service Hours Delivered',
        type: 'number',
        prefill: 'auto:total_hours',
        required: true
      },
      {
        id: 'member_participation',
        label: 'YMCA Member Participation Rate',
        type: 'text',
        prefill: 'auto:member_percentage',
        required: true
      },
      {
        id: 'outcomes_achieved',
        label: 'Outcomes Achieved',
        type: 'textarea',
        prefill: '',
        required: true
      }
    ]
  },

  corporate_sponsor: {
    id: 'corporate_sponsor',
    name: 'Corporate Sponsor',
    description: 'Corporate Partnership Impact Report',
    fields: [
      {
        id: 'sponsor_name',
        label: 'Corporate Sponsor Name',
        type: 'text',
        prefill: '',
        required: true
      },
      {
        id: 'partnership_period',
        label: 'Partnership Period',
        type: 'text',
        prefill: '',
        required: true
      },
      {
        id: 'employee_volunteers',
        label: 'Employee Volunteers Engaged',
        type: 'number',
        prefill: 'auto:total_volunteers',
        required: true
      },
      {
        id: 'volunteer_hours_contributed',
        label: 'Volunteer Hours Contributed',
        type: 'number',
        prefill: 'auto:total_hours',
        required: true
      },
      {
        id: 'branch_locations_served',
        label: 'YMCA Locations Served',
        type: 'textarea',
        prefill: 'auto:branches_list',
        required: true
      },
      {
        id: 'volunteer_activities',
        label: 'Volunteer Activities & Projects',
        type: 'textarea',
        prefill: 'auto:projects_list',
        required: true
      },
      {
        id: 'economic_impact',
        label: 'Economic Impact (Dollar Value)',
        type: 'number',
        prefill: 'auto:economic_value',
        required: false
      },
      {
        id: 'partnership_benefits',
        label: 'Partnership Benefits & Outcomes',
        type: 'textarea',
        prefill: '',
        required: true
      }
    ]
  }
};

// Helper function to get template by ID
export function getTemplateById(templateId) {
  return GRANT_TEMPLATES[templateId] || null;
}

// Helper function to get all template options for dropdown
export function getTemplateOptions() {
  return Object.values(GRANT_TEMPLATES).map(template => ({
    value: template.id,
    label: template.name,
    description: template.description
  }));
}