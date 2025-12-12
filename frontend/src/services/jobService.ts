/**
 * Service pour la gestion des offres d'emploi
 */

const API_BASE_URL = 'http://localhost:5000/api';

export interface JobData {
  title: string;
  company: string;
  location: string;
  remote: boolean;
  salaryMin: number;
  salaryMax: number;
  experience: number;
  description: string;
  skills: string[];
}

export interface JobResponse {
  id: number;
  job_id: number;
  id_offre: number;
  titre: string;
  entreprise: string;
  competences_requises: string[];
  description: string;
  localisation: string;
  niveau_souhaite: string;
  type_contrat: string;
  diplome_requis: string;
  experience_min: number;
  tags_manuels: string[];
  date_publication: string;
  est_active: boolean;
}

export interface JobDetails {
  id: number;
  title: string;
  company: string;
  description: string;
  location: string;
  remote: boolean;
  experience: number;
  skills: string[];
  level: string;
  education: string;
  posted: string;
  recruiter: string;
  matchAnalysis?: {
    totalScore: number;
    scoreBreakdown: any;
    missingSkills: Array<{ skill: string; importance: string }>;
    matchingSkills: string[];
    recommendation: string;
  };
}

export interface ApplicationResponse {
  success: boolean;
  message: string;
  applicationId: number;
  date: string;
}

class JobService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    console.log(`[JobService] ${options.method || 'GET'} ${url}`, {
      body: options.body,
      timestamp: new Date().toISOString()
    });

    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    console.log(`[JobService] Response ${response.status} ${response.statusText}`, {
      url,
      timestamp: new Date().toISOString()
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error(`[JobService] Error ${response.status}:`, error);
      throw new Error(error.error || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Crée une nouvelle offre d'emploi
   */
  async createJob(jobData: JobData): Promise<JobResponse> {
    console.log('[JobService] Creating job with data:', {
      ...jobData,
      skillsCount: jobData.skills.length
    });

    // Convertir le format frontend vers backend
    const backendData = {
      titre: jobData.title,
      entreprise: jobData.company,
      competences_requises: jobData.skills,
      description: jobData.description,
      localisation: jobData.location,
      niveau_souhaite: this.determineLevel(jobData.experience),
      type_contrat: this.determineContractType(jobData.remote),
      diplome_requis: this.determineDiploma(jobData.experience),
      experience_min: jobData.experience,
      tags_manuels: [...jobData.skills, jobData.location, this.determineLevel(jobData.experience)],
      texte_complet: `${jobData.description} ${jobData.skills.join(' ')}`
    };

    console.log('[JobService] Transformed data for backend:', backendData);

    try {
      const result = await this.request<JobResponse>('/recruiter/jobs', {
        method: 'POST',
        body: JSON.stringify(backendData),
      });

      const jobId = result.id || result.job_id || result.id_offre;
      console.log('[JobService] Created job ID:', jobId);

      if (jobId) {
        this.triggerIndexing(jobId, backendData).catch(err => {
          console.warn('[JobService] Indexing triggered but may have failed:', err);
        });
      } else {
        console.warn('[JobService] No job ID found in response, skipping indexing');
      }

      return result;
    } catch (error) {
      console.error('[JobService] Failed to create job:', error);
      throw error;
    }
  }

  /**
   * Déclenche l'indexation en temps réel
   */
  private async triggerIndexing(jobId: number, jobData: any) {
    try {
      console.log('[JobService] Triggering real-time indexing for job:', jobId);
      
      const indexResponse = await fetch(`${API_BASE_URL}/jobs/index/${jobId}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          job_data: jobData,
          timestamp: new Date().toISOString()
        }),
      });

      if (indexResponse.ok) {
        const indexResult = await indexResponse.json();
        console.log('[JobService] Job indexed successfully:', indexResult);
        return indexResult;
      } else {
        console.warn('[JobService] Indexing may have failed, job saved in DB only');
        return null;
      }
    } catch (error) {
      console.error('[JobService] Indexing error (non-blocking):', error);
      return null;
    }
  }

  /**
   * Récupère les offres du recruteur
   */
  async getRecruiterJobs(): Promise<JobResponse[]> {
    console.log('[JobService] Fetching recruiter jobs');
    return this.request<JobResponse[]>('/recruiter/jobs');
  }

  /**
   * Recherche d'offres (pour candidats)
   */
  async searchJobs(query: string = '', filters?: any): Promise<JobResponse[]> {
    console.log('[JobService] Searching jobs:', { query, filters });
    
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (filters?.location) params.append('location', filters.location);
    if (filters?.skills) {
      filters.skills.forEach((skill: string) => params.append('skills', skill));
    }

    return this.request<JobResponse[]>(`/jobs/search?${params.toString()}`);
  }

  /**
   * Vérifie si le recruteur est authentifié
   */
  async checkRecruiterAuth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/check-auth`, {
        credentials: 'include',
      });
      
      const data = await response.json();
      const isRecruiter = data.authenticated && data.user?.user_type === 'recruteur';
      
      console.log('[JobService] Auth check:', {
        authenticated: data.authenticated,
        userType: data.user?.user_type,
        isRecruiter
      });
      
      return isRecruiter;
    } catch (error) {
      console.error('[JobService] Auth check failed:', error);
      return false;
    }
  }

  /**
   * Détermine le niveau en fonction de l'expérience
   */
  private determineLevel(experience: number): string {
    if (experience < 2) return 'débutant';
    if (experience < 5) return 'intermédiaire';
    if (experience < 10) return 'senior';
    return 'expert';
  }

  /**
   * Détermine le type de contrat
   */
  private determineContractType(remote: boolean): string {
    return remote ? 'télétravail' : 'cdi';
  }

  /**
   * Détermine le diplôme requis
   */
  private determineDiploma(experience: number): string {
    if (experience > 5) return 'bac+5';
    if (experience > 3) return 'bac+3';
    return 'bac+2';
  }

  /**
   * ✅ CORRECTION : Valide les données du formulaire
   */
  validateJobData(jobData: JobData): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Titre
    if (!jobData.title || jobData.title.trim().length < 5) {
      errors.push('Le titre doit contenir au moins 5 caractères');
    }

    // Entreprise
    if (!jobData.company || !jobData.company.trim()) {
      errors.push('Le nom de l\'entreprise est requis');
    }

    // ✅ CORRECTION : Location - accepte ville OU Remote
    if (!jobData.location || !jobData.location.trim()) {
      errors.push('La localisation est requise (ville ou Remote)');
    }

    // Description
    if (!jobData.description || jobData.description.trim().length < 50) {
      errors.push('La description doit contenir au moins 50 caractères');
    }

    // Compétences
    if (!jobData.skills || jobData.skills.length < 3) {
      errors.push('Au moins 3 compétences sont requises');
    }

    // Salaires
    if (jobData.salaryMin && jobData.salaryMax && jobData.salaryMin > jobData.salaryMax) {
      errors.push('Le salaire minimum ne peut pas être supérieur au maximum');
    }

    if (jobData.salaryMin < 0 || jobData.salaryMax < 0) {
      errors.push('Les salaires ne peuvent pas être négatifs');
    }

    // Expérience
    if (jobData.experience < 0) {
      errors.push('L\'expérience ne peut pas être négative');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Récupère les détails complets d'une offre
   */
  async getJobDetails(jobId: number): Promise<JobDetails> {
    console.log('[JobService] Fetching job details:', jobId);
    
    const response = await this.request<{ success: boolean; job: JobDetails }>(
      `/job/${jobId}`
    );
    
    return response.job;
  }

  /**
   * Postuler à une offre (pour candidats)
   */
  async applyToJob(
    jobId: number, 
    message?: string
  ): Promise<ApplicationResponse> {
    console.log('[JobService] Applying to job:', jobId);
    
    return this.request<ApplicationResponse>(`/job/${jobId}/apply`, {
      method: 'POST',
      body: JSON.stringify({ 
        message: message || '',
        timestamp: new Date().toISOString()
      }),
    });
  }

  /**
   * Obtenir les candidatures pour une offre (pour recruteurs)
   */
  async getJobApplications(jobId: number): Promise<any[]> {
    console.log('[JobService] Fetching job applications:', jobId);
    
    const response = await this.request<{ success: boolean; applications: any[] }>(
      `/job/${jobId}/applications`
    );
    
    return response.applications;
  }

  /**
   * Mettre à jour le statut d'une candidature
   */
  async updateApplicationStatus(
    applicationId: number,
    status: string
  ): Promise<{ success: boolean; message: string }> {
    console.log('[JobService] Updating application status:', { applicationId, status });
    
    return this.request<{ success: boolean; message: string }>(`/job/application/${applicationId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }
}

export const jobService = new JobService();