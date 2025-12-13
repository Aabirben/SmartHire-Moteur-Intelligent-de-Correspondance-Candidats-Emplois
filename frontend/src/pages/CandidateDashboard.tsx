import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AdvancedSearchFilters } from "@/components/search/AdvancedSearchFilters";
import { CVUpload } from "@/components/candidate/CVUpload";
import { LogOut, Briefcase, MessageSquare, Upload, FileText, RefreshCw, Search, Lightbulb, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import { AuthGuard } from "@/components/AuthGuard";
import { cvService } from "@/services/cvService";
import { SearchFilters } from "@/types";
import { searchService } from "@/services/searchService";
import { matchingService } from "@/services/matchingService";

// Interface pour les jobs du backend
interface BackendJob {
  id: string | number;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  experience: number;
  skills: string[];
  description: string;
  matchScore?: number;
  postedDate?: string;
  source?: string;
}

export default function CandidateDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [jobs, setJobs] = useState<BackendJob[]>([]);
  const [filteredJobs, setFilteredJobs] = useState<BackendJob[]>([]);
  const [hasCV, setHasCV] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculatingScores, setIsCalculatingScores] = useState(false);
  const [searchMode, setSearchMode] = useState<string>("auto");
  const [totalResults, setTotalResults] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [cvInfo, setCvInfo] = useState<any>(null);
  const [sortOrder, setSortOrder] = useState<"score-desc" | "score-asc" | "experience" | "none">("none");
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    location: "Any",
    experience: [0, 10],
    skills: [],
    booleanOperator: "AND",
    remote: false,
  });
  const [hasSearched, setHasSearched] = useState(false);
  const [searchType, setSearchType] = useState<'simple' | 'cv_based'>('simple');

  useEffect(() => {
    loadInitialJobs();
    checkCVStatus();
  }, []);

  // Fonction pour calculer le score de matching pour un job (algorithmique) - RÉEL
  const calculateJobMatchScore = async (job: BackendJob): Promise<BackendJob> => {
    if (!hasCV || !cvInfo?.id) return { ...job, matchScore: 0 };
    
    try {
      const matchResult = await matchingService.getMatchAnalysis(cvInfo.id.toString(), job.id.toString());
      return {
        ...job,
        matchScore: matchResult.totalScore
      };
    } catch (error) {
      console.warn(`Erreur calcul matching job ${job.id}:`, error);
      return { ...job, matchScore: 0 };
    }
  };

  // Calculer les scores pour une liste de jobs (algorithmique) - RÉEL
  const calculateScoresForJobs = async (jobsList: BackendJob[]): Promise<BackendJob[]> => {
    if (!hasCV || !cvInfo?.id || jobsList.length === 0) {
      return jobsList.map(job => ({ ...job, matchScore: undefined }));
    }
    
    setIsCalculatingScores(true);
    try {
      const jobsWithScores: BackendJob[] = [];
      
      for (let i = 0; i < jobsList.length; i += 3) {
        const batch = jobsList.slice(i, i + 3);
        const batchPromises = batch.map(job => calculateJobMatchScore(job));
        const batchResults = await Promise.all(batchPromises);
        jobsWithScores.push(...batchResults);
        
        if (i === 0) {
          setFilteredJobs(prev => {
            const updated = [...prev];
            batchResults.forEach((result, index) => {
              updated[index] = result;
            });
            return updated;
          });
        }
      }
      
      return jobsWithScores;
    } catch (error) {
      console.error('Erreur calcul des scores:', error);
      return jobsList.map(job => ({ ...job, matchScore: undefined }));
    } finally {
      setIsCalculatingScores(false);
    }
  };

  const loadInitialJobs = async () => {
    setIsLoading(true);
    try {
      const response = await searchService.advancedSearch({
        query: "",
        target: 'jobs',
        limit: 20
      });
      
      const processedJobs = response.results.map((job: any, index: number) => ({
        ...job,
        id: job.id && job.id.toString().trim() ? job.id.toString() : `job-${index}`,
        skills: Array.isArray(job.skills) ? job.skills : [],
        experience: typeof job.experience === 'number' ? job.experience : 0,
        remote: Boolean(job.remote),
        matchScore: undefined
      }));
      
      setJobs(processedJobs);
      
      // Calculer les scores selon le type de recherche
      let jobsWithScores = processedJobs;
      if (hasCV && cvInfo?.id) {
        setSearchType('cv_based');
        jobsWithScores = await calculateScoresForJobs(processedJobs);
      } else {
        setSearchType('simple');
        jobsWithScores = processedJobs.map(job => ({ ...job, matchScore: undefined }));
      }
      
      setFilteredJobs(jobsWithScores);
      setTotalResults(response.totalResults);
      setHasSearched(false);
      
    } catch (error) {
      console.error('Erreur lors du chargement des emplois:', error);
      toast.error("Impossible de charger les emplois. Veuillez réessayer.");
      setJobs([]);
      setFilteredJobs([]);
    } finally {
      setIsLoading(false);
    }
  };

  const checkCVStatus = async () => {
    try {
      const info = await cvService.getCVInfo();
      setHasCV(info.exists);
      setCvInfo(info);
      setSearchType(info.exists ? 'cv_based' : 'simple');
      
      // STOCKER IMMÉDIATEMENT DANS LOCALSTORAGE QUAND ON VERIFIE LE STATUT DU CV
      localStorage.setItem('candidateSearchType', info.exists ? 'cv_based' : 'simple');
      localStorage.setItem('candidateHasCV', info.exists ? 'true' : 'false');
      if (info.exists && info.id) {
        localStorage.setItem('candidateCVId', info.id.toString());
      } else {
        localStorage.removeItem('candidateCVId');
      }
      
    } catch (error) {
      console.error('Erreur vérification CV:', error);
      setHasCV(false);
      setCvInfo(null);
      setSearchType('simple');
      
      // Nettoyer le localStorage en cas d'erreur
      localStorage.setItem('candidateHasCV', 'false');
      localStorage.setItem('candidateSearchType', 'simple');
      localStorage.removeItem('candidateCVId');
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Déconnexion réussie");
    } catch (error) {
      toast.error("Erreur lors de la déconnexion");
    }
  };

  // Fonction principale de recherche - RÉELLE
  const handleSearch = async (
    query: string, 
    filters: SearchFilters, 
    mode: "auto" | "boolean" | "vectoriel" | "hybrid" = "auto"
  ) => {
    setIsLoading(true);
    setSearchQuery(query);
    setSearchFilters(filters);
    
    try {
      const apiFilters: any = {};
      
      if (filters.location && filters.location !== "Any") {
        apiFilters.location = [filters.location];
      }
      
      if (filters.skills.length > 0) {
        apiFilters.skills = filters.skills;
        apiFilters.booleanOperator = filters.booleanOperator;
      }
      
      if (filters.experience) {
        apiFilters.experience = filters.experience;
      }
      
      if (filters.remote !== undefined) {
        apiFilters.remote = filters.remote;
      }
      
      const response = await searchService.advancedSearch({
        query: query.trim(),
        filters: apiFilters,
        target: 'jobs',
        mode: mode,
        limit: 20
      });
      
      const processedResults = response.results.map((job: any, index: number) => ({
        ...job,
        id: job.id && job.id.toString().trim() ? job.id.toString() : `search-${index}`,
        skills: Array.isArray(job.skills) ? job.skills : [],
        experience: typeof job.experience === 'number' ? job.experience : 0,
        remote: Boolean(job.remote),
        matchScore: undefined
      }));
      
      let resultsWithScores = processedResults;
      
      // DÉTERMINER LE TYPE DE RECHERCHE
      if (hasCV && cvInfo?.id) {
        // RECHERCHE AVEC CV → calculer les scores algorithmiques RÉELS
        setSearchType('cv_based');
        resultsWithScores = await calculateScoresForJobs(processedResults);
        
        // Stocker le contexte pour JobDetails
        localStorage.setItem('candidateSearchType', 'cv_based');
        localStorage.setItem('candidateHasCV', 'true');
        localStorage.setItem('candidateCVId', cvInfo.id.toString());
        
      } else {
        // RECHERCHE SIMPLE → PAS de scores mockés
        setSearchType('simple');
        
        // Stocker le contexte pour JobDetails
        localStorage.setItem('candidateSearchType', 'simple');
        localStorage.setItem('candidateHasCV', 'false');
        localStorage.removeItem('candidateCVId');
      }
      
      setFilteredJobs(resultsWithScores);
      setTotalResults(response.totalResults);
      setSearchMode(response.modeUsed);
      setHasSearched(true);
      
      toast.success(`${response.totalResults} emploi(s) trouvé(s)`);
      
    } catch (error) {
      console.error('Erreur lors de la recherche:', error);
      toast.error("Erreur lors de la recherche");
      
      // Pas de fallback mocké - on laisse l'erreur
      setFilteredJobs([]);
      setTotalResults(0);
      setSearchMode("error");
      setHasSearched(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCVUploadSuccess = async (skills: string[], cvId: number) => {
    try {
      await checkCVStatus();
      setShowUpload(false);
      
      // Mettre à jour le contexte
      setSearchType('cv_based');
      localStorage.setItem('candidateSearchType', 'cv_based');
      localStorage.setItem('candidateHasCV', 'true');
      localStorage.setItem('candidateCVId', cvId.toString());
      
      // Recherche automatique avec les compétences du CV
      await handleSearch("", {
        location: "Any",
        experience: [0, 10],
        skills: skills,
        booleanOperator: "OR",
        remote: false,
      }, "hybrid");
      
      toast.success("CV uploadé avec succès ! Emplois correspondants trouvés.");
    } catch (error) {
      toast.error("Erreur lors de la recherche personnalisée");
    }
  };

  const handleDeleteCV = async () => {
    try {
      await cvService.deleteCV();
      setHasCV(false);
      setCvInfo(null);
      setSearchType('simple');
      
      // Mettre à jour le contexte
      localStorage.setItem('candidateSearchType', 'simple');
      localStorage.setItem('candidateHasCV', 'false');
      localStorage.removeItem('candidateCVId');
      
      // Recalculer les scores en mode simple
      const jobsWithoutScores = jobs.map(job => ({ ...job, matchScore: undefined }));
      setJobs(jobsWithoutScores);
      setFilteredJobs(jobsWithoutScores);
      
      toast.success("CV supprimé avec succès");
    } catch (error) {
      console.error('Erreur suppression CV:', error);
      toast.error("Erreur lors de la suppression du CV");
    }
  };

  const refreshJobs = async () => {
    await loadInitialJobs();
    toast.info("Actualisation des emplois");
  };

  // Trier les jobs
  const sortJobs = (jobsToSort: BackendJob[], order: typeof sortOrder): BackendJob[] => {
    const sorted = [...jobsToSort];
    
    switch (order) {
      case "score-desc":
        // Ne trier que les jobs qui ont un score
        return sorted.sort((a, b) => {
          const scoreA = a.matchScore || -1;
          const scoreB = b.matchScore || -1;
          return scoreB - scoreA;
        });
      case "score-asc":
        return sorted.sort((a, b) => {
          const scoreA = a.matchScore || Infinity;
          const scoreB = b.matchScore || Infinity;
          return scoreA - scoreB;
        });
      case "experience":
        return sorted.sort((a, b) => b.experience - a.experience);
      case "none":
      default:
        return sorted;
    }
  };

  const handleSortChange = (order: typeof sortOrder) => {
    setSortOrder(order);
    const sortedJobs = sortJobs(filteredJobs, order);
    setFilteredJobs(sortedJobs);
  };

  const handleResetSearch = () => {
    setHasSearched(false);
    setSearchQuery("");
    setSearchFilters({
      location: "Any",
      experience: [0, 10],
      skills: [],
      booleanOperator: "AND",
      remote: false,
    });
    setSortOrder("none");
    loadInitialJobs();
  };

  // FONCTION CORRIGÉE : Pour naviguer vers les détails d'une offre
  const handleViewJobDetails = (job: BackendJob) => {
    // Stocker TOUTES les infos nécessaires avec un timestamp
    const context = {
      jobId: job.id,
      searchType: searchType,
      hasCV: hasCV,
      cvId: cvInfo?.id,
      matchScore: job.matchScore,
      timestamp: Date.now()
    };
    
    localStorage.setItem('lastJobContext', JSON.stringify(context));
    
    // Stocker aussi les variables globales (fallback)
    localStorage.setItem('candidateSearchType', searchType);
    localStorage.setItem('candidateHasCV', hasCV ? 'true' : 'false');
    if (hasCV && cvInfo?.id) {
      localStorage.setItem('candidateCVId', cvInfo.id.toString());
    } else {
      localStorage.removeItem('candidateCVId');
    }
    
    console.log('Navigation vers JobDetails avec contexte:', context);
    navigate(`/candidate/job/${job.id}`);
  };

  if (showUpload) {
    return (
      <div className="min-h-screen p-6 mesh-gradient">
        <div className="max-w-2xl mx-auto">
          <Button onClick={() => setShowUpload(false)} variant="ghost" className="mb-4">
            ← Retour au tableau de bord
          </Button>
          <CVUpload onUploadSuccess={handleCVUploadSuccess} />
        </div>
      </div>
    );
  }

  return (
    <AuthGuard requireAuth requireRole="candidat">
      <div className="min-h-screen mesh-gradient">
        <header className="border-b border-border glass-strong">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gradient">Tableau de bord Candidat</h1>
              <p className="text-sm text-muted-foreground">Bonjour, {user?.prenom} !</p>
            </div>
            <div className="flex items-center gap-4">
              <Button 
                onClick={() => setShowUpload(true)} 
                variant={hasCV ? "outline" : "default"}
                className={`gap-2 ${hasCV ? "" : "bg-gradient-to-r from-primary to-accent text-white"}`}
              >
                {hasCV ? (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Mettre à jour CV
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Déposer CV
                  </>
                )}
              </Button>
              
              <Button onClick={() => navigate("/messages")} variant="outline" className="gap-2">
                <MessageSquare className="w-4 h-4" />
                Messages
              </Button>
              <Button onClick={handleLogout} variant="ghost" className="gap-2">
                <LogOut className="w-4 h-4" />
                Déconnexion
              </Button>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-8">
          {/* Section CV */}
          <Card className="glass-strong p-6 mb-6 border-l-4 border-primary">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${hasCV ? 'bg-green-100 dark:bg-green-900' : 'bg-blue-100 dark:bg-blue-900'}`}>
                  {hasCV ? (
                    <FileText className="w-6 h-6 text-green-600 dark:text-green-400" />
                  ) : (
                    <Upload className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold mb-1 flex items-center gap-2">
                    {hasCV ? "Votre CV est déposé" : "Améliorez vos correspondances !"}
                    {hasCV && (
                      <Badge variant="secondary" className="text-xs">
                        Mode: Matching avancé
                      </Badge>
                    )}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {hasCV 
                      ? "Votre CV est analysé pour des recommandations personnalisées. Mettez-le à jour pour améliorer les résultats."
                      : "Déposez votre CV pour obtenir des recommandations d'emplois personnalisées avec scores algorithmiques"}
                  </p>
                  {hasCV && cvInfo && cvInfo.skills && (
                    <div className="mt-2">
                      <p className="text-xs text-muted-foreground mb-1">Compétences détectées:</p>
                      <div className="flex flex-wrap gap-1">
                        {cvInfo.skills.slice(0, 5).map((skill: string, index: number) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                        {cvInfo.skills.length > 5 && (
                          <Badge variant="outline" className="text-xs">
                            +{cvInfo.skills.length - 5} autres
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {hasCV && (
                  <Button 
                    onClick={handleDeleteCV} 
                    variant="ghost" 
                    size="sm"
                    className="text-red-600 hover:text-red-800 hover:bg-red-50"
                  >
                    Supprimer
                  </Button>
                )}
                <Button 
                  onClick={() => setShowUpload(true)} 
                  className={`${hasCV ? "bg-gradient-to-r from-blue-500 to-cyan-500" : "bg-gradient-to-r from-primary to-accent"}`}
                >
                  {hasCV ? "Mettre à jour" : "Déposer maintenant"}
                </Button>
              </div>
            </div>
          </Card>

          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-bold">Recherche d'emplois</h2>
            <div className="flex items-center gap-2">
              
              {hasSearched && (
                <Button 
                  onClick={handleResetSearch} 
                  variant="outline" 
                  size="sm"
                  className="gap-1"
                >
                  <RefreshCw className="w-3 h-3" />
                  Nouvelle recherche
                </Button>
              )}
              <Button onClick={refreshJobs} variant="outline" size="sm" disabled={isLoading}>
                Actualiser
              </Button>
            </div>
          </div>

          <AdvancedSearchFilters 
            onSearch={handleSearch}
            placeholder="Rechercher un emploi par titre, entreprise ou compétences..."
            isLoading={isLoading}
            showSuggestions={true}
            initialQuery={searchQuery}
            initialFilters={searchFilters}
          />

          {/* Section "Emplois disponibles" - SEULEMENT visible après une recherche */}
          {hasSearched && (
            <div className="mt-8">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                <div className="flex items-center gap-4">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    Emplois disponibles
                    <Badge variant="secondary">{filteredJobs.length}</Badge>
                  </h2>
                  {searchMode && searchMode !== "error" && (
                    <Badge variant="outline" className="text-xs">
                      Mode: {searchMode}
                    </Badge>
                  )}
                  <Badge variant={searchType === 'cv_based' ? 'default' : 'outline'} className="text-xs">
                    {searchType === 'cv_based' ? 'Matching avancé' : 'Recherche simple'}
                  </Badge>
                </div>
                
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                  <p className="text-sm text-muted-foreground">
                    {totalResults > 0 
                      ? `Affichage de ${filteredJobs.length} sur ${totalResults} emplois` 
                      : `Affichage de ${filteredJobs.length} emplois`}
                  </p>
                  
                  {filteredJobs.length > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">Trier par:</span>
                      <select 
                        className="text-sm bg-background border rounded px-2 py-1"
                        value={sortOrder}
                        onChange={(e) => handleSortChange(e.target.value as typeof sortOrder)}
                      >
                        <option value="none">Aucun tri</option>
                        <option value="score-desc">Score ↓</option>
                        <option value="score-asc">Score ↑</option>
                        <option value="experience">Expérience</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>
              
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-muted-foreground">Chargement des emplois...</p>
                </div>
              ) : isCalculatingScores ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-4 text-muted-foreground">Calcul des scores de correspondance...</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Nous analysons votre CV pour trouver les meilleures correspondances
                  </p>
                </div>
              ) : searchMode === "error" ? (
                <Card className="glass-strong p-8 text-center">
                  <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
                    <Briefcase className="w-8 h-8 text-destructive" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Erreur de recherche</h3>
                  <p className="text-muted-foreground mb-4">
                    Impossible d'effectuer la recherche. Veuillez réessayer plus tard.
                  </p>
                  <Button onClick={handleResetSearch}>
                    Nouvelle recherche
                  </Button>
                </Card>
              ) : filteredJobs.length === 0 ? (
                <Card className="glass-strong p-8 text-center">
                  <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <Briefcase className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Aucun emploi trouvé</h3>
                  <p className="text-muted-foreground mb-4">
                    {searchQuery || searchFilters.skills.length > 0 || searchFilters.location !== "Any" 
                      ? "Essayez d'autres critères de recherche" 
                      : "Aucun emploi disponible pour le moment"}
                  </p>
                  <Button onClick={handleResetSearch}>
                    Nouvelle recherche
                  </Button>
                </Card>
              ) : (
                <>
                  {/* Statistiques réelles seulement si des scores existent */}
                  {filteredJobs.some(job => job.matchScore && job.matchScore > 0) && (
                    <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card className="glass-strong p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">Score moyen</p>
                            <p className="text-2xl font-bold">
                              {Math.round(filteredJobs.reduce((sum, job) => sum + (job.matchScore || 0), 0) / filteredJobs.length)}%
                            </p>
                          </div>
                          <Sparkles className="w-8 h-8 text-blue-500" />
                        </div>
                      </Card>
                      
                      <Card className="glass-strong p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">Meilleur match</p>
                            <p className="text-2xl font-bold">
                              {Math.max(...filteredJobs.map(job => job.matchScore || 0))}%
                            </p>
                          </div>
                          <Briefcase className="w-8 h-8 text-green-500" />
                        </div>
                      </Card>
                      
                      <Card className="glass-strong p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">Correspondances</p>
                            <p className="text-2xl font-bold">
                              {filteredJobs.filter(job => (job.matchScore || 0) >= 60).length}/{filteredJobs.length}
                            </p>
                          </div>
                          <Briefcase className="w-8 h-8 text-primary" />
                        </div>
                      </Card>
                    </div>
                  )}
                  
                  {/* Liste des emplois */}
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {filteredJobs.map((job, index) => (
                      <Card 
                        key={job.id || `job-card-${index}`}
                        className="glass-strong p-6 hover:scale-[1.02] hover:glow-primary transition-all cursor-pointer group relative"
                        onClick={() => handleViewJobDetails(job)}
                      >
                        {/* Score de correspondance - RÉEL ou non affiché */}
                        {job.matchScore !== undefined && job.matchScore > 0 ? (
                          <div className="mb-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Badge className={`
                                ${job.matchScore >= 80 
                                  ? 'bg-gradient-to-r from-green-500 to-emerald-600' 
                                  : job.matchScore >= 60 
                                  ? 'bg-gradient-to-r from-yellow-500 to-amber-600'
                                  : 'bg-gradient-to-r from-orange-500 to-red-500'}
                                animate-pulse-glow
                              `}>
                                {job.matchScore}% Correspondance
                              </Badge>
                              {sortOrder.startsWith('score') && (
                                <Badge variant="outline" className="text-xs">
                                  #{index + 1}
                                </Badge>
                              )}
                            </div>
                            
                            <div className="text-xs text-muted-foreground">
                              {job.matchScore >= 80 ? '🎯 Excellent' : 
                               job.matchScore >= 60 ? '👍 Bon' : 
                               job.matchScore >= 40 ? '🤝 Moyen' : '📉 Faible'}
                            </div>
                          </div>
                        ) : searchType === 'cv_based' ? (
                          <div className="mb-3">
                            <Badge variant="outline" className="bg-gray-100 dark:bg-gray-800">
                              Score en cours de calcul...
                            </Badge>
                          </div>
                        ) : null}
                        
                        {/* Indicateur type de score */}
                        <div className="mb-2">
                          <Badge 
                            variant="outline" 
                            className={`text-xs ${
                              searchType === 'cv_based' 
                                ? 'border-primary text-primary' 
                                : 'border-blue-500 text-blue-600'
                            }`}
                          >
                            {searchType === 'cv_based' ? 'Matching algorithmique' : 'Recherche simple'}
                          </Badge>
                        </div>
                        
                        <h3 className="font-bold text-lg mb-2 group-hover:text-primary transition-colors">{job.title}</h3>
                        <p className="text-muted-foreground mb-4">{job.company}</p>
                        
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center gap-2">
                            <Briefcase className="w-4 h-4 text-primary" />
                            <span>{job.location}</span>
                            {job.remote && <Badge variant="outline">Télétravail</Badge>}
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <span>Expérience: {job.experience}+ ans</span>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-1 mt-4">
                          {job.skills.slice(0, 3).map((skill: string, skillIndex: number) => (
                            <Badge 
                              key={`${job.id}-skill-${skillIndex}`}
                              variant="secondary" 
                              className="text-xs"
                            >
                              {skill}
                            </Badge>
                          ))}
                          {job.skills.length > 3 && (
                            <Badge 
                              variant="outline" 
                              className="text-xs"
                            >
                              +{job.skills.length - 3}
                            </Badge>
                          )}
                        </div>
                        
                        {/* Indicateur de position dans le tri */}
                        {sortOrder.startsWith('score') && job.matchScore && job.matchScore > 0 && (
                          <div className="absolute top-2 right-2">
                            {index === 0 ? (
                              <span className="text-green-500 text-xs font-bold">TOP</span>
                            ) : index === filteredJobs.length - 1 ? (
                              <span className="text-orange-500 text-xs">DERNIER</span>
                            ) : null}
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Message d'accueil quand aucune recherche n'a été effectuée */}
          {!hasSearched && !isLoading && (
            <div className="mt-12 text-center">
              <Card className="glass-strong p-8 max-w-2xl mx-auto">
                <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Search className="w-8 h-8 text-primary" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Commencez votre recherche</h2>
                <p className="text-muted-foreground mb-6">
                  {hasCV 
                    ? "Utilisez les filtres pour trouver des emplois qui correspondent à votre profil. Votre CV est analysé pour un matching personnalisé."
                    : "Utilisez les filtres pour trouver des emplois. Déposez votre CV pour obtenir des scores de matching algorithmiques."}
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="text-center p-4">
                    <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 mx-auto mb-3 flex items-center justify-center">
                      <Lightbulb className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="font-semibold mb-1">Recherche intelligente</h3>
                    <p className="text-sm text-muted-foreground">
                      Utilisez notre moteur de recherche avancé pour trouver les offres qui vous correspondent
                    </p>
                  </div>
                  
                  <div className="text-center p-4">
                    <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900 mx-auto mb-3 flex items-center justify-center">
                      <Sparkles className="w-6 h-6 text-green-600 dark:text-green-400" />
                    </div>
                    <h3 className="font-semibold mb-1">Matching automatique</h3>
                    <p className="text-sm text-muted-foreground">
                      {hasCV 
                        ? "Votre CV est analysé pour calculer des scores de correspondance précis"
                        : "Déposez votre CV pour obtenir des scores de matching personnalisés"}
                    </p>
                  </div>
                  
                  <div className="text-center p-4">
                    <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900 mx-auto mb-3 flex items-center justify-center">
                      <Briefcase className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <h3 className="font-semibold mb-1">Tri intelligent</h3>
                    <p className="text-sm text-muted-foreground">
                      Triez les résultats par score de matching pour voir les meilleures opportunités en premier
                    </p>
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-3 justify-center">
                  {hasCV && cvInfo?.skills && (
                    <Button 
                      onClick={() => {
                        handleSearch("", {
                          location: "Any",
                          experience: [0, 10],
                          skills: cvInfo.skills.slice(0, 10),
                          booleanOperator: "OR",
                          remote: false,
                        }, "hybrid");
                      }}
                      className="gap-2"
                    >
                      <Briefcase className="w-4 h-4" />
                      Rechercher selon mon CV
                    </Button>
                  )}
                  
                  <Button 
                    onClick={() => handleSearch("", {
                      location: "Any",
                      experience: [0, 10],
                      skills: [],
                      booleanOperator: "AND",
                      remote: false,
                    })}
                    variant="outline"
                    className="gap-2"
                  >
                    <Search className="w-4 h-4" />
                    Voir toutes les offres
                  </Button>
                </div>
              </Card>
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}