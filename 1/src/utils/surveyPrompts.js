// Utility functions for managing survey prompts and notifications

export const PROMPT_CHANNELS = {
  EMAIL: 'email',
  SMS: 'sms',
  IN_APP: 'in_app',
  PUSH: 'push'
};

export const PROMPT_TEMPLATES = {
  postEvent: {
    email: {
      subject: "How was your volunteer experience at YMCA?",
      body: "Hi {name}, thank you for volunteering with us at {project}! We'd love to hear about your experience. Please take 2 minutes to share your feedback.",
      cta: "Share Your Feedback"
    },
    sms: {
      message: "Hi {name}! Thanks for volunteering at {project}. How was your experience? Share feedback here: {surveyLink}"
    },
    inApp: {
      title: "Rate your volunteer experience",
      message: "Help us improve volunteer experiences by sharing your feedback about {project}.",
      action: "Rate Experience"
    }
  },
  
  reminder: {
    email: {
      subject: "Quick feedback reminder - YMCA volunteer survey",
      body: "Hi {name}, we sent you a survey about your recent volunteer experience at {project}. Your feedback is important to us!",
      cta: "Complete Survey"
    },
    sms: {
      message: "Reminder: Please share feedback about your volunteer experience at {project}: {surveyLink}"
    }
  },
  
  followUp: {
    email: {
      subject: "Thank you for your feedback!",
      body: "Hi {name}, thank you for your feedback about {project}. We appreciate your time and will use your input to improve our volunteer programs.",
      cta: "View Upcoming Opportunities"
    }
  }
};

// Simulate sending survey prompt
export function sendSurveyPrompt(volunteerInfo, promptType = 'postEvent', channel = PROMPT_CHANNELS.EMAIL) {
  const template = PROMPT_TEMPLATES[promptType]?.[channel];
  
  if (!template) {
    throw new Error(`Template not found for ${promptType}/${channel}`);
  }
  
  // Simulate API call to send prompt
  const prompt = {
    id: `prompt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    volunteerId: volunteerInfo.assignee,
    volunteerName: volunteerInfo.assignee,
    projectName: volunteerInfo.project,
    branch: volunteerInfo.branch,
    eventDate: volunteerInfo.date,
    promptType,
    channel,
    template,
    sentAt: new Date().toISOString(),
    surveyLink: generateSurveyLink(volunteerInfo),
    status: 'sent'
  };
  
  // Log the prompt (in real app, this would be stored in database)
  console.log('Survey prompt sent:', prompt);
  
  return prompt;
}

// Generate unique survey link for volunteer
export function generateSurveyLink(volunteerInfo) {
  const baseUrl = window.location.origin;
  const surveyId = btoa(`${volunteerInfo.assignee}-${volunteerInfo.project}-${volunteerInfo.date}`);
  return `${baseUrl}/survey/${surveyId}`;
}

// Simulate sending automated reminders
export function scheduleReminderPrompts(volunteers, delay = 3) {
  console.log(`Scheduling reminder prompts for ${volunteers.length} volunteers in ${delay} days`);
  
  // In a real implementation, this would schedule actual reminders
  const scheduledReminders = volunteers.map(volunteer => ({
    id: `reminder-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    volunteerId: volunteer.assignee,
    volunteerName: volunteer.assignee,
    projectName: volunteer.project,
    branch: volunteer.branch,
    scheduledFor: new Date(Date.now() + delay * 24 * 60 * 60 * 1000).toISOString(),
    status: 'scheduled',
    type: 'reminder'
  }));
  
  return scheduledReminders;
}

// Analytics for prompt effectiveness
export function calculatePromptAnalytics(prompts, responses) {
  const totalPrompts = prompts.length;
  const totalResponses = responses.length;
  const responseRate = totalPrompts > 0 ? (totalResponses / totalPrompts) * 100 : 0;
  
  // Response time analysis
  const responsesByPrompt = responses.reduce((acc, response) => {
    const promptId = prompts.find(p => 
      p.volunteerName === response.volunteerName && 
      p.projectName === response.projectName
    )?.id;
    
    if (promptId) {
      acc[promptId] = response;
    }
    return acc;
  }, {});
  
  const avgResponseTime = Object.keys(responsesByPrompt).length > 0 
    ? Object.values(responsesByPrompt).reduce((sum, response) => sum + response.responseTime, 0) / Object.keys(responsesByPrompt).length
    : 0;
  
  // Channel effectiveness
  const channelStats = prompts.reduce((acc, prompt) => {
    if (!acc[prompt.channel]) {
      acc[prompt.channel] = { sent: 0, responses: 0 };
    }
    acc[prompt.channel].sent++;
    
    if (responsesByPrompt[prompt.id]) {
      acc[prompt.channel].responses++;
    }
    return acc;
  }, {});
  
  Object.keys(channelStats).forEach(channel => {
    channelStats[channel].rate = channelStats[channel].sent > 0 
      ? (channelStats[channel].responses / channelStats[channel].sent) * 100 
      : 0;
  });
  
  return {
    totalPrompts,
    totalResponses,
    responseRate: Math.round(responseRate * 100) / 100,
    avgResponseTime: Math.round(avgResponseTime),
    channelStats,
    responsesByPrompt
  };
}

// User-friendly prompt status messages
export function getPromptStatusMessage(prompt) {
  const timeSinceSent = Date.now() - new Date(prompt.sentAt).getTime();
  const daysSince = Math.floor(timeSinceSent / (1000 * 60 * 60 * 24));
  
  if (prompt.status === 'sent' && daysSince === 0) {
    return 'Survey sent today';
  } else if (prompt.status === 'sent' && daysSince === 1) {
    return 'Survey sent yesterday';
  } else if (prompt.status === 'sent' && daysSince > 1) {
    return `Survey sent ${daysSince} days ago`;
  } else if (prompt.status === 'scheduled') {
    return 'Reminder scheduled';
  } else if (prompt.status === 'responded') {
    return 'Survey completed';
  }
  
  return 'Unknown status';
}