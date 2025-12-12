/**
 * Service pour la recherche avancée
 */

const API_BASE_URL = 'http://localhost:5000/api';

export interface SearchFilters {
    skills: string[];
    location: string[];
    experience: [number, number];
    remote: boolean;
    booleanOperator: 'AND' | 'OR';
}

export interface SearchRequest {
    query?: string;
    filters?: Partial<SearchFilters>;
    target?: 'jobs' | 'cvs';
    mode?: 'auto' | 'boolean' | 'vectoriel' | 'hybrid';
    limit?: number;
}

export interface JobResult {
    id: string | number;
    title: string;
    company: string;
    location: string;
    remote: boolean;
    experience: number;
    salary: {
        min: number;
        max: number;
    };
    skills: string[];
    description: string;
    matchScore: number;
    postedDate: string;
    source: string;
}

export interface CVResult {
    id: string | number;
    name: string;
    title: string;
    location: string;
    experience: number;
    skills: string[];
    level: string;
    cvSummary: string;
    matchScore: number;
    uploadDate: string;
    source: string;
}

export interface SearchResponse {
    success: boolean;
    totalResults: number;
    modeUsed: string;
    results: (JobResult | CVResult)[];
    searchStats: {
        query: string;
        filtersApplied: Partial<SearchFilters>;
        mode: string;
        sources: Record<string, number>;
        executionTime: number;
    };
    error?: string; // ← Rendre optionnel
}

export interface SuggestionResponse {
    success: boolean;
    suggestions: string[];
}

class SearchService {
    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${API_BASE_URL}${endpoint}`;
        
        console.log(`[SearchService] ${options.method || 'GET'} ${url}`, {
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

        console.log(`[SearchService] Response ${response.status} ${response.statusText}`, {
            url,
            timestamp: new Date().toISOString()
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            console.error(`[SearchService] Error ${response.status}:`, error);
            throw new Error(error.error || `Request failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Recherche avancée
     */
    async advancedSearch(params: SearchRequest): Promise<SearchResponse> {
        console.log('[SearchService] Advanced search with params:', params);
        
        return this.request('/search/advanced', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    }

    /**
     * Recherche rapide (simplifiée)
     */
    async quickSearch(query: string, target: 'jobs' | 'cvs' = 'jobs'): Promise<SearchResponse> {
        console.log('[SearchService] Quick search:', { query, target });
        
        return this.advancedSearch({
            query,
            target,
            mode: 'vectoriel',
            limit: 10
        });
    }

    /**
     * Obtenir des suggestions de recherche
     */
    async getSuggestions(query?: string): Promise<SuggestionResponse> {
        console.log('[SearchService] Getting suggestions:', query);
        
        const endpoint = query 
            ? `/search/suggestions?q=${encodeURIComponent(query)}`
            : '/search/suggestions';
            
        return this.request(endpoint);
    }

    /**
     * Auto-complétion
     */
    async autocomplete(query: string): Promise<{ suggestions: string[] }> {
        console.log('[SearchService] Autocomplete:', query);
        
        if (!query || query.length < 2) {
            return { suggestions: [] };
        }
        
        return this.request(`/search/autocomplete?q=${encodeURIComponent(query)}`);
    }

    /**
     * Comparer différents modes de recherche
     */
    async compareModes(
        query: string,
        filters?: Partial<SearchFilters>
    ): Promise<Record<string, SearchResponse>> {
        console.log('[SearchService] Comparing search modes');
        
        const modes: Array<'boolean' | 'vectoriel' | 'hybrid'> = ['boolean', 'vectoriel', 'hybrid'];
        const results: Record<string, SearchResponse> = {};
        
        for (const mode of modes) {
            try {
                const result = await this.advancedSearch({
                    query,
                    filters,
                    target: 'jobs',
                    mode,
                    limit: 5
                });
                results[mode] = result;
            } catch (error) {
                console.error(`[SearchService] Mode ${mode} failed:`, error);
                results[mode] = {
                    success: false,
                    error: error instanceof Error ? error.message : 'Unknown error',
                    totalResults: 0,
                    modeUsed: mode,
                    results: [],
                    searchStats: {
                        query,
                        filtersApplied: filters || {},
                        mode,
                        sources: {},
                        executionTime: 0
                    }
                };
            }
        }
        
        return results;
    }

    /**
     * Statistiques du système de recherche
     */
    async getSystemStats(): Promise<any> {
        console.log('[SearchService] Getting system stats');
        
        return this.request('/search/stats');
    }

    /**
     * Recherche personnalisée après upload CV
     */
    async searchAfterCVUpload(skills: string[]): Promise<SearchResponse> {
        console.log('[SearchService] Personalized search after CV upload:', skills);
        
        return this.advancedSearch({
            query: skills.join(' '),
            filters: {
                skills,
                booleanOperator: 'OR'
            },
            target: 'jobs',
            mode: 'hybrid',
            limit: 20
        });
    }
}

export const searchService = new SearchService();