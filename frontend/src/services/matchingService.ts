/**
 * Service pour le matching CV-Offre
 * Utilise exclusivement les données du backend - AUCUNE donnée mock
 */

const API_BASE_URL = 'http://localhost:5000/api';

export interface MatchResult {
  totalScore: number;
  scoreBreakdown: ScoreBreakdownItem[];
  skillsData: SkillDataItem[];
  fitCriteria: FitCriterionItem[];
  recommendation: string;
  level: LevelDetection;
  missingSkills: SkillGap[];
  matchingSkills: string[];
  candidate?: CandidateInfo;
  job: JobInfo;
  
}

export interface ScoreBreakdownItem {
  category: string;
  score: number;
  contribution: number;
  icon: string;
  detail: string;
}

export interface SkillDataItem {
  skill: string;
  required: number;
  user: number;
}

export interface FitCriterionItem {
  name: string;
  required: string;
  candidate: string;
  matchPercent: number;
  icon: string;
}

export interface LevelDetection {
  level: string;
  confidence: number;
  reasons: string[];
}

export interface SkillGap {
  name: string;
  requiredLevel: number;
  currentLevel: number;
  impactPercent: number;
  suggestions: string[];
}

export interface CandidateInfo {
  name: string;
  email: string;
  location: string;
  experience: number;
  level: string;
  skills: string[];
}

export interface JobInfo {
  id: string;
  title: string;
  company: string;
  location: string;
  experience: number;
  level: string;
  skills: string[];
}

export interface CandidateDetails {
  id: string;
  name: string;
  email: string;
  title: string;
  location: string;
  experience: number;
  skills: string[];
  level: string;
  cvSummary: string;
}

export interface JobDetails {
  id: string;
  title: string;
  company: string;
  skills: string[];
  description: string;
  location: string;
  remote: boolean;
  experience: number;
  level: string;
  posted: string;
}

class MatchingService {
  /**
   * Obtenir le matching détaillé entre un CV et une offre
   * Utilise uniquement le backend - PAS de données mocks
   */
  async getMatchAnalysis(cvId: string, jobId: string): Promise<MatchResult> {
    try {
      console.log(`[MatchingService] getMatchAnalysis: cv=${cvId}, job=${jobId}`);
      
      const response = await fetch(
        `${API_BASE_URL}/matching/cv/${cvId}/job/${jobId}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        }
      );

      console.log(`[MatchingService] Response status: ${response.status}`);
      
      if (!response.ok) {
        let errorMessage = `Erreur HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (jsonError) {
          // Si la réponse n'est pas du JSON, utiliser le texte brut
          const textError = await response.text();
          errorMessage = textError || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('[MatchingService] Matching data received:', data);
      return data;
      
    } catch (error) {
      console.error('[MatchingService] Error in getMatchAnalysis:', error);
      throw error; // Propager l'erreur pour la gérer dans les composants
    }
  }

  /**
   * Obtenir les détails d'un candidat (pour recruteur)
   * Utilise uniquement le backend - PAS de données mocks
   */
  async getCandidateDetails(candidateId: string): Promise<CandidateDetails> {
    try {
      console.log(`[MatchingService] getCandidateDetails: ${candidateId}`);
      
      const response = await fetch(
        `${API_BASE_URL}/matching/candidate/${candidateId}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        }
      );

      console.log(`[MatchingService] Response status: ${response.status}`);
      
      if (!response.ok) {
        let errorMessage = `Erreur HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (jsonError) {
          const textError = await response.text();
          errorMessage = textError || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('[MatchingService] Candidate data received:', data);
      return data;
      
    } catch (error) {
      console.error('[MatchingService] Error in getCandidateDetails:', error);
      throw error;
    }
  }

  /**
   * Obtenir les détails d'une offre (pour candidat)
   * Utilise uniquement le backend - PAS de données mocks
   */
  async getJobDetails(jobId: string): Promise<JobDetails> {
    try {
      console.log(`[MatchingService] getJobDetails: ${jobId}`);
      
      const response = await fetch(
        `${API_BASE_URL}/matching/job/${jobId}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
        }
      );

      console.log(`[MatchingService] Response status: ${response.status}`);
      
      if (!response.ok) {
        let errorMessage = `Erreur HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (jsonError) {
          const textError = await response.text();
          errorMessage = textError || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('[MatchingService] Job data received:', data);
      
      // S'assurer que les champs obligatoires existent
      const processedData: JobDetails = {
        id: data.id?.toString() || jobId,
        title: data.title || 'Offre sans titre',
        company: data.company || 'Entreprise non spécifiée',
        skills: Array.isArray(data.skills) ? data.skills : [],
        description: data.description || '',
        location: data.location || 'Localisation non spécifiée',
        remote: data.remote === true || (data.location && data.location.toLowerCase().includes('remote')),
        experience: typeof data.experience === 'number' ? data.experience : 0,
        level: data.level || '',
        posted: data.posted || ''
      };
      
      return processedData;
      
    } catch (error) {
      console.error('[MatchingService] Error in getJobDetails:', error);
      throw error;
    }
  }

  /**
   * Tester la connexion au service de matching
   */
  async testConnection(): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/matching/debug/ids`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        return {
          success: true,
          message: `Service disponible. CVs: ${data.total_cvs || 0}, Offres: ${data.total_jobs || 0}`
        };
      } else {
        return {
          success: false,
          message: `Service non disponible: ${response.status}`
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `Erreur de connexion: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Obtenir les IDs disponibles pour débogage
   */
  async getAvailableIds(): Promise<{ cvs: any[], jobs: any[] }> {
    try {
      const response = await fetch(`${API_BASE_URL}/matching/debug/ids`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        return await response.json();
      } else {
        throw new Error(`Failed to get IDs: ${response.status}`);
      }
    } catch (error) {
      console.error('[MatchingService] Error in getAvailableIds:', error);
      return { cvs: [], jobs: [] };
    }
  }

  /**
   * Rechercher des candidats pour une offre (pour recruteur)
   */
  async findCandidatesForJob(jobId: string, limit: number = 10): Promise<CandidateDetails[]> {
    try {
      // Cette route pourrait être implémentée dans votre backend
      const response = await fetch(
        `${API_BASE_URL}/matching/job/${jobId}/candidates?limit=${limit}`,
        {
          method: 'GET',
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data.candidates) ? data.candidates : [];
      } else {
        console.warn(`Route /matching/job/${jobId}/candidates non disponible`);
        return [];
      }
    } catch (error) {
      console.error('[MatchingService] Error in findCandidatesForJob:', error);
      return [];
    }
  }

  /**
   * Obtenir les offres recommandées pour un candidat
   */
  async getRecommendedJobs(cvId: string, limit: number = 10): Promise<JobDetails[]> {
    try {
      // Cette route pourrait être implémentée dans votre backend
      const response = await fetch(
        `${API_BASE_URL}/matching/cv/${cvId}/recommendations?limit=${limit}`,
        {
          method: 'GET',
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data.jobs)) {
          return data.jobs.map((job: any) => ({
            id: job.id?.toString() || '',
            title: job.title || 'Offre',
            company: job.company || '',
            skills: Array.isArray(job.skills) ? job.skills : [],
            description: job.description || '',
            location: job.location || '',
            remote: job.remote === true,
            experience: typeof job.experience === 'number' ? job.experience : 0,
            level: job.level || '',
            posted: job.posted || ''
          }));
        }
        return [];
      } else {
        console.warn(`Route /matching/cv/${cvId}/recommendations non disponible`);
        return [];
      }
    } catch (error) {
      console.error('[MatchingService] Error in getRecommendedJobs:', error);
      return [];
    }
  }
}

export const matchingService = new MatchingService();

// Fonctions utilitaires
export const formatMatchScore = (score: number): string => {
  if (score >= 90) return 'Excellent';
  if (score >= 75) return 'Très bon';
  if (score >= 60) return 'Bon';
  if (score >= 40) return 'Moyen';
  return 'Faible';
};

export const getMatchColor = (score: number): string => {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
  if (score >= 40) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
};

export const getMatchBadgeVariant = (score: number): "default" | "secondary" | "destructive" | "outline" => {
  if (score >= 80) return 'default';
  if (score >= 60) return 'secondary';
  if (score >= 40) return 'outline';
  return 'destructive';
};