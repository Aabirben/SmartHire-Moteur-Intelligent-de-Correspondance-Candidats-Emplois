/**
 * Service pour la gestion des CVs
 */

const API_BASE_URL = 'http://localhost:5000/api';

interface CVUploadResponse {
  success: boolean;
  message: string;
  cv_id: number;
  skills: string[];
  infos: {
    nom: string;
    titre_profil: string;
    annees_experience: number;
    localisation: string;
    resume: string;
    description_experience: string;
    projets: string;
  };
  stats: {
    nb_competences: number;
    has_skills_section: boolean;
    annees_experience: number;
  };
}

interface CVInfo {
  exists: boolean;
  id: number;
  nom: string;
  competences: string[];
  niveau_estime: string;
  localisation: string;
  annees_experience: number;
  tags_manuels: string[];
  texte_preview: string;
  date_upload: string | null;
  indexed_in_whoosh: boolean;
  whoosh_info: {
    original_filename: string;
    user_id: string;
    nb_tokens_original: number;
    nb_tokens_processed: number;
  };
}

interface HealthCheck {
  status: 'ok' | 'degraded';
  services: {
    postgresql: boolean;
    whoosh_index: boolean;
    nltk_resources: boolean;
    [key: string]: any;
  };
  timestamp: string;
}

class CVService {
  /**
   * Upload un fichier PDF
   */
  async uploadCV(file: File): Promise<CVUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/cv/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `Upload failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Récupère les informations du CV de l'utilisateur
   */
  async getCVInfo(): Promise<CVInfo> {
    const response = await fetch(`${API_BASE_URL}/cv/info`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Failed to get CV info: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Supprime le CV de l'utilisateur
   */
  async deleteCV(): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/cv/delete`, {
      method: 'DELETE',
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `Delete failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Analyse un texte de CV (prévisualisation)
   */
  async analyzeText(text: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/cv/analyze-text`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `Analysis failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Vérifie l'état des services
   */
  async healthCheck(): Promise<HealthCheck> {
    const response = await fetch(`${API_BASE_URL}/cv/health`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Valide un fichier PDF avant upload
   */
  validateFile(file: File): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    const maxSize = 5 * 1024 * 1024; // 5MB

    // Vérifier le type
    if (file.type !== 'application/pdf') {
      errors.push('Seuls les fichiers PDF sont acceptés');
    }

    // Vérifier la taille
    if (file.size > maxSize) {
      errors.push(`Fichier trop volumineux (max: ${maxSize / 1024 / 1024}MB)`);
    }

    // Vérifier le nom
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      errors.push('Le fichier doit avoir une extension .pdf');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

export const cvService = new CVService();