const API_BASE_URL = 'http://localhost:5000/api';

// Fonction utilitaire pour les appels API
async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include', // Important pour les cookies de session
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// Auth API
export const authApi = {
  register: async (data: {
    email: string;
    password: string;
    user_type: 'candidat' | 'recruteur';
    nom: string;
    prenom: string;
    entreprise?: string;
    telephone?: string;
  }) => {
    return fetchApi('/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  login: async (email: string, password: string) => {
    return fetchApi('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  logout: async () => {
    return fetchApi('/logout', { method: 'POST' });
  },

  checkAuth: async () => {
    return fetchApi('/check-auth');
  },
};

// Profile API
export const profileApi = {
  getProfile: async () => {
    return fetchApi('/profile');
  },

  updateProfile: async (data: {
    nom: string;
    prenom: string;
    entreprise?: string;
    telephone?: string;
  }) => {
    return fetchApi('/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

// CV API (Candidat)
export const cvApi = {
  uploadCV: async (data: any) => {
    return fetchApi('/candidate/cv', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getCV: async () => {
    return fetchApi('/candidate/cv');
  },
};

// Jobs API (Recruteur)
export const jobsApi = {
  createJob: async (data: any) => {
    return fetchApi('/recruiter/jobs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getRecruiterJobs: async () => {
    return fetchApi('/recruiter/jobs');
  },

  searchJobs: async (filters: {
    q?: string;
    location?: string;
    skills?: string[];
  }) => {
    const params = new URLSearchParams();
    if (filters.q) params.append('q', filters.q);
    if (filters.location) params.append('location', filters.location);
    if (filters.skills) {
      filters.skills.forEach(skill => params.append('skills', skill));
    }
    
    return fetchApi(`/jobs/search?${params.toString()}`);
  },
};

// Applications API (Candidat)
export const applicationsApi = {
  applyForJob: async (offre_id: number, message?: string) => {
    return fetchApi('/candidate/applications', {
      method: 'POST',
      body: JSON.stringify({ offre_id, message }),
    });
  },

  getApplications: async () => {
    return fetchApi('/candidate/applications');
  },
};

// Messaging API
export const messagingApi = {
  getConversations: async () => {
    return fetchApi('/messages');
  },

  getMessages: async (otherUserId: number) => {
    return fetchApi(`/messages/${otherUserId}`);
  },

  sendMessage: async (receiver_id: number, content: string) => {
    return fetchApi('/messages', {
      method: 'POST',
      body: JSON.stringify({ receiver_id, content }),
    });
  },
};