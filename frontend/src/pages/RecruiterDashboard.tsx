import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdvancedSearchFilters } from "@/components/search/AdvancedSearchFilters";
import { JobPostForm } from "@/components/recruiter/JobPostForm";
import { 
  LogOut, 
  User, 
  MessageSquare, 
  MapPin, 
  Briefcase, 
  Calendar,
  Globe,
  Clock,
  CheckCircle,
  XCircle,
  Share2,
  Search,
  Users,
  FileText,
  TrendingUp,
  RefreshCw,
  Eye,
  Mail,
  TrendingDown,
  Filter
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import { AuthGuard } from "@/components/AuthGuard";
import { searchService } from "@/services/searchService";
import { SearchFilters } from "@/types";
import { matchingService } from "@/services/matchingService";

// Type pour les jobs du backend
interface BackendJob {
  id: number;
  id_offre?: number;
  titre: string;
  entreprise: string;
  localisation: string;
  experience_min: number;
  description: string;
  competences_requises: string[];
  niveau_souhaite?: string;
  type_contrat?: string;
  date_publication: string;
  est_active: boolean;
  salaire_min?: number;
  salaire_max?: number;
  remote?: boolean;
  nb_candidats?: number;
}

// Interface pour le formatage des résultats
interface FormattedCandidate {
  id: string | number;
  name: string;
  email: string;
  title: string;
  location: string;
  experience: number;
  skills: string[];
  level: string;
  cvSummary: string;
  matchScore?: number;
  source: string;
  cvId?: number;
}

export default function RecruiterDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [candidates, setCandidates] = useState<FormattedCandidate[]>([]);
  const [jobs, setJobs] = useState<BackendJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [isCalculatingScores, setIsCalculatingScores] = useState(false);
  const [activeTab, setActiveTab] = useState("search");
  const [searchMode, setSearchMode] = useState<string>("");
  const [totalResults, setTotalResults] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedJobForMatching, setSelectedJobForMatching] = useState<BackendJob | null>(null);
  const [matchingEnabled, setMatchingEnabled] = useState(false);
  const [candidateSortOrder, setCandidateSortOrder] = useState<"score-desc" | "score-asc" | "experience" | "none">("none");
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    location: "Any",
    experience: [0, 10],
    skills: [],
    booleanOperator: "AND",
    remote: false,
  });
  const [searchStats, setSearchStats] = useState({
    totalSearches: 0,
    avgMatchScore: 0,
    topSkills: [] as string[]
  });
  const [currentScoreType, setCurrentScoreType] = useState<'job' | 'search'>('search');

  useEffect(() => {
    fetchJobs();
    loadSearchStats();
  }, []);

  useEffect(() => {
    if (jobs.length > 0 && !selectedJobForMatching) {
      const activeJob = jobs.find(job => job.est_active);
      if (activeJob) {
        setSelectedJobForMatching(activeJob);
      }
    }
  }, [jobs]);

  // Fonction pour calculer le score de matching avec une offre - RÉEL
  const calculateCandidateMatchScore = async (candidate: FormattedCandidate): Promise<FormattedCandidate> => {
    if (!selectedJobForMatching || !candidate.cvId) {
      return { ...candidate, matchScore: undefined };
    }
    
    try {
      const matchResult = await matchingService.getMatchAnalysis(
        candidate.cvId.toString(), 
        selectedJobForMatching.id.toString()
      );
      return {
        ...candidate,
        matchScore: matchResult.totalScore
      };
    } catch (error) {
      console.warn(`Erreur calcul matching candidat ${candidate.id}:`, error);
      return { ...candidate, matchScore: 0 };
    }
  };

  // Calculer les scores pour une liste de candidats - RÉEL
  const calculateScoresForCandidates = async (candidatesList: FormattedCandidate[]): Promise<FormattedCandidate[]> => {
    if (!selectedJobForMatching || candidatesList.length === 0) {
      return candidatesList;
    }
    
    setIsCalculatingScores(true);
    try {
      const candidatesWithScores: FormattedCandidate[] = [];
      
      for (let i = 0; i < candidatesList.length; i += 3) {
        const batch = candidatesList.slice(i, i + 3);
        const batchPromises = batch.map(candidate => calculateCandidateMatchScore(candidate));
        const batchResults = await Promise.all(batchPromises);
        candidatesWithScores.push(...batchResults);
        
        if (i === 0) {
          setCandidates(prev => {
            const updated = [...prev];
            batchResults.forEach((result, index) => {
              updated[index] = result;
            });
            return updated;
          });
        }
      }
      
      return candidatesWithScores;
    } catch (error) {
      console.error('Erreur calcul des scores:', error);
      return candidatesList.map(candidate => ({ ...candidate, matchScore: 0 }));
    } finally {
      setIsCalculatingScores(false);
    }
  };

  const fetchJobs = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:5000/api/recruiter/jobs', {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP! status: ${response.status}`);
      }
      
      const data = await response.json();
      setJobs(data);
    } catch (error) {
      console.error("Erreur lors du chargement des offres:", error);
      toast.error("Impossible de charger vos offres");
    } finally {
      setIsLoading(false);
    }
  };

  const loadSearchStats = async () => {
    try {
      setSearchStats({
        totalSearches: 0,
        avgMatchScore: 0,
        topSkills: []
      });
    } catch (error) {
      console.error("Erreur lors du chargement des statistiques:", error);
      setSearchStats({
        totalSearches: 0,
        avgMatchScore: 0,
        topSkills: []
      });
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Déconnexion réussie");
    } catch (error) {
      console.error("Erreur lors de la déconnexion:", error);
      toast.error("Erreur lors de la déconnexion");
    }
  };

  // Fonction de recherche - RÉELLE
  const handleSearch = async (
    query: string, 
    filters: SearchFilters, 
    mode: "auto" | "boolean" | "vectoriel" | "hybrid" = "auto",
    enableMatching: boolean = matchingEnabled
  ) => {
    setIsSearching(true);
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
        target: 'cvs',
        mode: mode,
        limit: 20
      });
      
      if (!response.success) {
        throw new Error(response.error || "Échec de la recherche");
      }
      
      // Formatage des résultats avec cvSummary requis
      const formattedCandidates: FormattedCandidate[] = response.results.map((cv: any, index: number) => ({
        id: cv.id || cv.cv_id || `cand-${index}`,
        name: cv.name || "Candidat",
        email: cv.email || '',
        title: cv.title || cv.titre_profil || 'Développeur',
        location: cv.location || cv.localisation || 'Non spécifié',
        experience: cv.experience || cv.annees_experience || 0,
        skills: Array.isArray(cv.skills) ? cv.skills : 
               Array.isArray(cv.competences) ? cv.competences : [],
        level: getLevelFromExperience(cv.experience || cv.annees_experience || 0),
        cvSummary: cv.cvSummary || cv.texte_preview || cv.description || '',
        matchScore: undefined,
        source: cv.source || 'uploaded',
        cvId: cv.cv_id || cv.id
      }));
      
      let candidatesWithScores = formattedCandidates;
      
      // DÉTERMINER LE TYPE DE SCORE À UTILISER
      if (enableMatching && selectedJobForMatching) {
        // Score basé sur une offre spécifique - RÉEL
        setCurrentScoreType('job');
        candidatesWithScores = await calculateScoresForCandidates(formattedCandidates);
      } else {
        // Pas de matching par offre → pas de scores algorithmiques
        setCurrentScoreType('search');
        candidatesWithScores = formattedCandidates.map(candidate => ({
          ...candidate,
          matchScore: undefined
        }));
      }
      
      // Calculer la moyenne des scores (seulement si des scores existent)
      const scores = candidatesWithScores
        .filter(c => c.matchScore !== undefined && c.matchScore > 0)
        .map(c => c.matchScore!);
      
      const avgScore = scores.length > 0 
        ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) 
        : 0;
      
      setSearchStats(prev => ({
        ...prev,
        avgMatchScore: avgScore
      }));
      
      setCandidates(candidatesWithScores);
      setTotalResults(response.totalResults);
      setSearchMode(response.modeUsed || mode);
      
      // Message personnalisé selon le type de score
      const scoreTypeMessage = currentScoreType === 'job' 
        ? `(Matching algorithmique avec offre: ${selectedJobForMatching?.titre})`
        : `(Recherche simple - pas de matching par offre)`;
      
      toast.success(`${response.totalResults} candidat(s) trouvé(s)`, {
        description: `Mode: ${response.modeUsed || mode} • ${scoreTypeMessage}`
      });
      
    } catch (error: any) {
      console.error('Erreur lors de la recherche de candidats:', error);
      toast.error("Erreur lors de la recherche", {
        description: error.message || "Veuillez réessayer"
      });
      setCandidates([]);
      setTotalResults(0);
    } finally {
      setIsSearching(false);
    }
  };

  const handleJobPosted = async (newJob: any) => {
    try {
      toast.success("Offre publiée avec succès !", {
        description: `${newJob.titre} est maintenant en ligne`,
      });
      
      await fetchJobs();
      setActiveTab("jobs");
    } catch (error) {
      console.error("Erreur lors du traitement de la nouvelle offre:", error);
      toast.error("Erreur lors de la publication");
    }
  };

  const toggleJobStatus = async (jobId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`http://localhost:5000/api/recruiter/jobs/${jobId}/status`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !currentStatus })
      });
      
      if (response.ok) {
        const updatedJobs = jobs.map(job => 
          job.id === jobId ? { ...job, est_active: !currentStatus } : job
        );
        setJobs(updatedJobs);
        
        toast.success(`Offre ${!currentStatus ? "activée" : "désactivée"}`);
      } else {
        const error = await response.json();
        throw new Error(error.error || "Échec de la mise à jour");
      }
    } catch (error: any) {
      console.error("Erreur modification statut offre:", error);
      toast.error("Erreur lors de la modification", {
        description: error.message
      });
    }
  };

  const getLevelFromExperience = (experience: number): string => {
    if (experience < 2) return "Junior";
    if (experience < 5) return "Intermédiaire";
    if (experience < 8) return "Senior";
    return "Expert";
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // CORRECTION PRINCIPALE : Bien passer les paramètres au backend
  const viewCandidateProfile = (candidateId: string | number, cvId?: number, matchScore?: number) => {
    const candidateIdToUse = cvId || candidateId;
    
    // Toujours passer jobId si disponible
    const jobIdParam = selectedJobForMatching ? `?jobId=${selectedJobForMatching.id}` : '';
    
    // Le matchingParam indique si on doit afficher l'analyse de matching
    const matchingParam = matchingEnabled ? '&matching=true' : '';
    
    // Passer le scoreType pour indiquer le type de score calculé
    const scoreTypeParam = `&scoreType=${currentScoreType}`;
    
    // Passer le score calculé (si disponible)
    const scoreParam = matchScore !== undefined ? `&score=${matchScore}` : '';
    
    navigate(`/recruiter/candidate/${candidateIdToUse}${jobIdParam}${matchingParam}${scoreTypeParam}${scoreParam}`);
  };

  const contactCandidate = (email: string, name: string) => {
    window.location.href = `mailto:${email}?subject=Opportunité d'emploi&body=Bonjour ${name},`;
    toast.info("Client email ouvert", {
      description: `Prêt à contacter ${name}`
    });
  };

  const refreshCandidates = () => {
    if (searchQuery || searchFilters.skills.length > 0 || searchFilters.location !== "Any") {
      handleSearch(searchQuery, searchFilters, searchMode as any, matchingEnabled);
    } else {
      toast.info("Aucune recherche active à rafraîchir");
    }
  };

  const applyQuickFilter = (skills: string[], label: string) => {
    setSearchQuery("");
    const newFilters: SearchFilters = { 
      location: "Any", 
      experience: [0, 10], 
      skills, 
      booleanOperator: "OR", 
      remote: false,
    };
    setSearchFilters(newFilters);
    setActiveTab("search");
    setMatchingEnabled(false);
    setCurrentScoreType('search');
    
    toast.info(`Filtre "${label}" appliqué`, {
      description: "Cliquez sur 'Chercher' pour lancer la recherche"
    });
  };

  // Mettre à jour les scores des candidats quand on change d'offre - RÉEL
  const handleJobSelectionForMatching = async (job: BackendJob) => {
    setSelectedJobForMatching(job);
    
    if (candidates.length > 0 && matchingEnabled) {
      setIsCalculatingScores(true);
      try {
        const candidatesWithScores = await calculateScoresForCandidates(candidates);
        setCandidates(candidatesWithScores);
        setCurrentScoreType('job');
        
        toast.info(`Scores recalculés pour l'offre: ${job.titre}`, {
          description: "Matching algorithmique activé"
        });
      } catch (error) {
        console.error('Erreur recalcul des scores:', error);
        toast.error("Erreur lors du recalcul des scores");
      } finally {
        setIsCalculatingScores(false);
      }
    }
  };

  // Trier les candidats
  const sortCandidates = (candidatesToSort: FormattedCandidate[], order: typeof candidateSortOrder): FormattedCandidate[] => {
    const sorted = [...candidatesToSort];
    
    switch (order) {
      case "score-desc":
        // Ne trier que les candidats qui ont un score
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

  const handleCandidateSortChange = (order: typeof candidateSortOrder) => {
    setCandidateSortOrder(order);
    const sortedCandidates = sortCandidates(candidates, order);
    setCandidates(sortedCandidates);
  };

  const handleViewJobDetails = (jobId: number) => {
    navigate(`/recruiter/jobs/${jobId}`);
  };

  const quickFilters = [
    { label: "Développeurs Senior", skills: ["Senior", "Lead", "Architect"], icon: "" },
    { label: "Experts React", skills: ["React", "TypeScript", "Redux"], icon: "" },
    { label: "Python/Django", skills: ["Python", "Django", "FastAPI"], icon: "" },
    { label: "DevOps", skills: ["AWS", "Docker", "Kubernetes"], icon: "" },
    { label: "Full Stack", skills: ["Node.js", "React", "MongoDB"], icon: "" },
    { label: "Data Science", skills: ["Python", "Machine Learning", "Pandas"], icon: "" },
  ];

  const getActiveJobsCount = () => {
    return jobs.filter(j => j.est_active).length;
  };

  const getTotalCandidatesCount = () => {
    return jobs.reduce((total, job) => total + (job.nb_candidats || 0), 0);
  };

  // Obtenir le libellé du type de score
  const getScoreTypeLabel = () => {
    if (currentScoreType === 'job' && selectedJobForMatching) {
      return `Matching algorithmique avec: ${selectedJobForMatching.titre}`;
    } else {
      return "Recherche simple - pas de matching par offre";
    }
  };

  return (
    <AuthGuard requireAuth requireRole="recruteur">
      <div className="min-h-screen mesh-gradient">
        <header className="border-b border-border glass-strong sticky top-0 z-50">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gradient">Tableau de bord Recruteur</h1>
              <p className="text-sm text-muted-foreground">
                Bienvenue, {user?.entreprise || user?.prenom || "Recruteur"} !
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Button 
                onClick={() => navigate("/messages")} 
                variant="outline" 
                className="gap-2"
              >
                <MessageSquare className="w-4 h-4" />
                Messages
              </Button>
              <Button 
                onClick={handleLogout} 
                variant="ghost" 
                className="gap-2 hover:text-destructive"
              >
                <LogOut className="w-4 h-4" />
                Déconnexion
              </Button>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-8">
          {/* Statistiques rapides */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Card className="glass-strong p-6 hover:scale-[1.02] transition-all">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Candidats trouvés</p>
                  <p className="text-2xl font-bold">{totalResults}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {searchQuery || searchFilters.skills.length > 0 ? "Recherche active" : "Tous les candidats"}
                  </p>
                </div>
                <Users className="w-8 h-8 text-primary" />
              </div>
            </Card>
            
            <Card className="glass-strong p-6 hover:scale-[1.02] transition-all">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Offres actives</p>
                  <p className="text-2xl font-bold">{getActiveJobsCount()}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    sur {jobs.length} offres publiées
                  </p>
                </div>
                <Briefcase className="w-8 h-8 text-accent" />
              </div>
            </Card>
            
            <Card className="glass-strong p-6 hover:scale-[1.02] transition-all">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Score moyen</p>
                  <p className="text-2xl font-bold">{searchStats.avgMatchScore}%</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {getScoreTypeLabel()}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-green-500" />
              </div>
            </Card>
          </div>

          {/* Filtres rapides */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium flex items-center gap-2">
                <Search className="w-4 h-4" />
                Recherches rapides
              </h3>
              <Button 
                onClick={refreshCandidates} 
                variant="ghost" 
                size="sm"
                className="gap-2"
                disabled={isSearching}
              >
                <RefreshCw className={`w-3 h-3 ${isSearching ? 'animate-spin' : ''}`} />
                Actualiser
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {quickFilters.map((filter, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="cursor-pointer hover:bg-primary/10 hover:scale-[1.02] transition-all px-3 py-1.5"
                  onClick={() => applyQuickFilter(filter.skills, filter.label)}
                >
                  <span className="mr-1">{filter.icon}</span>
                  {filter.label}
                </Badge>
              ))}
            </div>
          </div>

          {/* Onglets principaux */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="search" className="flex items-center gap-2">
                <Search className="w-4 h-4" />
                Rechercher candidats
                {candidates.length > 0 && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {candidates.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="post" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Publier offre
              </TabsTrigger>
              <TabsTrigger value="jobs" className="flex items-center gap-2">
                <Briefcase className="w-4 h-4" />
                Mes offres
                {jobs.length > 0 && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {jobs.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            {/* Onglet Recherche de candidats */}
            <TabsContent value="search" className="space-y-6">
              {/* Sélecteur d'offre pour le matching */}
              <Card className="glass-strong p-4 mb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-primary" />
                    <span className="text-sm font-medium">Comparer avec l'offre :</span>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {/* Toggle pour activer/désactiver le matching */}
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-muted-foreground">Matching :</label>
                      <button
                        type="button"
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          matchingEnabled ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                        }`}
                        onClick={() => {
                          const newMatchingState = !matchingEnabled;
                          setMatchingEnabled(newMatchingState);
                          
                          if (newMatchingState && selectedJobForMatching && candidates.length > 0) {
                            // Activer le matching → recalculer les scores avec l'offre
                            handleJobSelectionForMatching(selectedJobForMatching);
                          } else if (!newMatchingState && candidates.length > 0) {
                            // Désactiver le matching → supprimer les scores basés sur l'offre
                            setCurrentScoreType('search');
                            setCandidates(prev => prev.map(candidate => ({
                              ...candidate,
                              matchScore: undefined
                            })));
                          }
                        }}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            matchingEnabled ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                    
                    <select
                      className="flex-1 max-w-md p-2 rounded border bg-background text-sm"
                      value={selectedJobForMatching?.id || ""}
                      onChange={(e) => {
                        const job = jobs.find(j => j.id.toString() === e.target.value);
                        if (job) {
                          setSelectedJobForMatching(job);
                          setMatchingEnabled(true);
                          setCurrentScoreType('job');
                          if (candidates.length > 0) {
                            handleJobSelectionForMatching(job);
                          }
                        }
                      }}
                    >
                      <option value="">Sélectionner une offre...</option>
                      {jobs.filter(j => j.est_active).map((job) => (
                        <option key={job.id} value={job.id}>
                          {job.titre} - {job.entreprise}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                {/* Message d'information */}
                {matchingEnabled && selectedJobForMatching ? (
                  <div className="mt-2 text-xs text-green-600 dark:text-green-400">
                     Matching algorithmique activé avec l'offre : <strong>{selectedJobForMatching.titre}</strong>
                    <br />
                    <span className="text-muted-foreground">
                      Les scores sont calculés par rapport à cette offre via le backend
                    </span>
                  </div>
                ) : matchingEnabled && !selectedJobForMatching ? (
                  <div className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                     Sélectionnez une offre pour activer le matching algorithmique
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
                    
                    <span className="text-muted-foreground">
                      Activez le matching pour obtenir des scores algorithmiques basés sur une offre
                    </span>
                  </div>
                )}
              </Card>

              <AdvancedSearchFilters 
                onSearch={(query, filters, mode) => handleSearch(query, filters, mode, matchingEnabled)}
                placeholder="Rechercher des candidats par nom, compétences ou expérience..."
                target="cvs"
                isLoading={isLoading || isSearching}
                showSuggestions={true}
                initialQuery={searchQuery}
                initialFilters={searchFilters}
              />

              {/* En-tête résultats */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    Candidats correspondants
                    <Badge variant="secondary" className="ml-2">
                      {candidates.length}
                    </Badge>
                    {searchMode && searchMode !== "auto" && (
                      <Badge variant="outline" className="text-xs">
                        {searchMode}
                      </Badge>
                    )}
                    {currentScoreType === 'job' ? (
                      <Badge className="bg-gradient-to-r from-primary to-accent text-xs">
                        Matching algorithmique
                      </Badge>
                    ) : (
                      <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-xs">
                        Recherche simple
                      </Badge>
                    )}
                  </h2>
                  {totalResults > 0 && (
                    <p className="text-sm text-muted-foreground mt-1">
                      Affichage de {candidates.length} candidat(s) sur {totalResults}
                      <span className="ml-2 font-medium">
                        • {getScoreTypeLabel()}
                      </span>
                    </p>
                  )}
                </div>
                
                {candidates.length > 0 && (
                  <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                    <div className="flex items-center gap-4 text-sm">
                      {currentScoreType === 'job' && (
                        <>
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-green-500"></div>
                            <span>Haute correspondance</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                            <span>Moyenne correspondance</span>
                          </div>
                        </>
                      )}
                    </div>
                    
                    {currentScoreType === 'job' && candidates.some(c => c.matchScore !== undefined) && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">Trier par:</span>
                        <select 
                          className="text-sm bg-background border rounded px-2 py-1"
                          value={candidateSortOrder}
                          onChange={(e) => handleCandidateSortChange(e.target.value as typeof candidateSortOrder)}
                        >
                          <option value="none">Aucun tri</option>
                          <option value="score-desc">Score ↓</option>
                          <option value="score-asc">Score ↑</option>
                          <option value="experience">Expérience</option>
                        </select>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* États de chargement */}
              {isLoading || isSearching ? (
                <Card className="glass-strong p-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-muted-foreground">
                    {isSearching ? "Recherche de candidats..." : "Chargement des candidats..."}
                  </p>
                </Card>
              ) : isCalculatingScores ? (
                <Card className="glass-strong p-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-4 text-muted-foreground">Calcul des scores de correspondance...</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Nous comparons les candidats avec l'offre sélectionnée via le backend
                  </p>
                </Card>
              ) : candidates.length === 0 ? (
                <Card className="glass-strong p-12 text-center">
                  <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <Users className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Aucun candidat trouvé</h3>
                  <p className="text-muted-foreground mb-6">
                    {searchQuery || searchFilters.skills.length > 0 || searchFilters.location !== "Any"
                      ? "Essayez d'autres critères de recherche"
                      : "Utilisez la recherche pour trouver des candidats qualifiés"}
                  </p>
                  <div className="flex gap-3 justify-center">
                    <Button 
                      onClick={() => handleSearch("", {
                        location: "Any",
                        experience: [0, 10],
                        skills: [],
                        booleanOperator: "AND",
                        remote: false,
                      }, "auto", false)}
                    >
                      Afficher tous les candidats
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => setActiveTab("post")}
                    >
                      Publier une offre
                    </Button>
                  </div>
                </Card>
              ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {candidates.map((candidate, index) => (
                    <Card 
                      key={candidate.id}
                      className="glass-strong p-6 hover:scale-[1.02] hover:glow-accent transition-all duration-300 group relative"
                    >
                      {/* Score de correspondance - RÉEL ou non affiché */}
                      {candidate.matchScore !== undefined && candidate.matchScore > 0 ? (
                        <div className="mb-3 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge className={`
                              ${candidate.matchScore > 70 
                                ? 'bg-gradient-to-r from-green-500 to-emerald-600' 
                                : candidate.matchScore > 40
                                ? 'bg-gradient-to-r from-yellow-500 to-amber-600'
                                : 'bg-gradient-to-r from-orange-500 to-red-500'}
                              animate-pulse-glow
                            `}>
                              {candidate.matchScore}% Correspondance
                            </Badge>
                            {candidateSortOrder.startsWith('score') && (
                              <Badge variant="outline" className="text-xs">
                                #{index + 1}
                              </Badge>
                            )}
                          </div>
                          
                          <div className="text-xs text-muted-foreground">
                            {candidate.matchScore > 70 ? '🎯 Excellent' : 
                             candidate.matchScore > 40 ? '👍 Bon' : '📉 Faible'}
                          </div>
                        </div>
                      ) : currentScoreType === 'job' ? (
                        <div className="mb-3">
                          <Badge variant="outline" className="bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200">
                            Score en cours de calcul...
                          </Badge>
                        </div>
                      ) : (
                        <div className="mb-3"></div>
                      )}
                      
                      {/* Type de score */}
                      <div className="mb-2">
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${currentScoreType === 'job' ? 'border-primary text-primary' : 'border-blue-500 text-blue-600'}`}
                        >
                          {currentScoreType === 'job' ? 'Matching algorithmique' : 'Recherche simple'}
                        </Badge>
                      </div>
                      
                      {/* Indicateur de position dans le tri */}
                      {candidateSortOrder.startsWith('score') && candidate.matchScore && candidate.matchScore > 0 && (
                        <div className="absolute top-2 right-2">
                          {index === 0 && <TrendingUp className="w-4 h-4 text-green-500" />}
                          {index === candidates.length - 1 && <TrendingDown className="w-4 h-4 text-orange-500" />}
                        </div>
                      )}
                      
                      {/* En-tête candidat */}
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                          <User className="w-6 h-6 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-bold truncate group-hover:text-primary transition-colors">{candidate.name}</h3>
                          <p className="text-sm text-muted-foreground truncate">{candidate.title}</p>
                        </div>
                      </div>
                      
                      {/* Informations candidat */}
                      <div className="space-y-2 text-sm mb-4">
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                          <span className="truncate">{candidate.location}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                          <span>{candidate.experience} ans d'expérience</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Briefcase className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                          <Badge variant="outline" className="text-xs">
                            {candidate.level}
                          </Badge>
                        </div>
                      </div>

                      {/* Compétences */}
                      <div className="mb-4">
                        <p className="text-xs font-medium text-muted-foreground mb-2">Compétences :</p>
                        <div className="flex flex-wrap gap-1">
                          {candidate.skills.slice(0, 4).map((skill) => (
                            <Badge key={skill} variant="secondary" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                          {candidate.skills.length > 4 && (
                            <Badge variant="outline" className="text-xs">
                              +{candidate.skills.length - 4}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Résumé CV */}
                      {candidate.cvSummary && candidate.cvSummary.length > 0 && (
                        <div className="mb-4">
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {candidate.cvSummary}
                          </p>
                        </div>
                      )}

                      {/* Boutons d'action - CORRECTION : Passer le score */}
                      <div className="pt-4 border-t border-border/50 flex gap-2">
                        <Button 
                          size="sm" 
                          className="flex-1"
                          onClick={() => viewCandidateProfile(candidate.id, candidate.cvId, candidate.matchScore)}
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          Voir profil
                        </Button>
                        <Button 
                          size="sm"
                          variant="outline"
                          onClick={() => contactCandidate(candidate.email, candidate.name)}
                          disabled={!candidate.email}
                        >
                          <Mail className="w-3 h-3" />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Onglet Publier une offre */}
            <TabsContent value="post">
              <JobPostForm onJobPosted={handleJobPosted} />
            </TabsContent>

            {/* Onglet Mes offres */}
            <TabsContent value="jobs">
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-xl font-bold">
                      Offres publiées
                      <Badge variant="secondary" className="ml-2">
                        {getActiveJobsCount()} actives / {jobs.length} total
                      </Badge>
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      {getTotalCandidatesCount()} candidatures totales
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={fetchJobs}
                      disabled={isLoading}
                      className="gap-2"
                    >
                      <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
                      Actualiser
                    </Button>
                    <Button 
                      variant="default" 
                      size="sm"
                      onClick={() => setActiveTab("post")}
                      className="gap-2"
                    >
                      <FileText className="w-3 h-3" />
                      Nouvelle offre
                    </Button>
                  </div>
                </div>
                
                {isLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">Chargement des offres...</p>
                  </div>
                ) : jobs.length === 0 ? (
                  <Card className="glass-strong p-12 text-center">
                    <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                      <Briefcase className="w-8 h-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">Aucune offre publiée</h3>
                    <p className="text-muted-foreground mb-6">
                      Créez votre première offre pour commencer à recevoir des candidatures
                    </p>
                    <Button onClick={() => setActiveTab("post")}>
                      Publier votre première offre
                    </Button>
                  </Card>
                ) : (
                  <div className="grid gap-6">
                    {jobs.map((job) => {
                      const level = job.niveau_souhaite || getLevelFromExperience(job.experience_min);
                      const isRemote = job.type_contrat === 'télétravail' || job.remote;
                      const isSelectedForMatching = selectedJobForMatching?.id === job.id;
                      
                      return (
                        <Card key={job.id} className={`glass-strong p-6 hover:scale-[1.01] transition-all ${isSelectedForMatching ? 'ring-2 ring-primary' : ''}`}>
                          <div className="flex justify-between items-start mb-4">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-bold text-xl">{job.titre}</h3>
                                {isSelectedForMatching && matchingEnabled && (
                                  <Badge className="bg-gradient-to-r from-primary to-accent text-xs">
                                    Comparaison active
                                  </Badge>
                                )}
                              </div>
                              <p className="text-muted-foreground">{job.entreprise}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge 
                                variant={job.est_active ? "default" : "outline"} 
                                className="flex items-center gap-1"
                              >
                                {job.est_active ? (
                                  <>
                                    <CheckCircle className="w-3 h-3" />
                                    Active
                                  </>
                                ) : (
                                  <>
                                    <XCircle className="w-3 h-3" />
                                    Inactive
                                  </>
                                )}
                              </Badge>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => toggleJobStatus(job.id, job.est_active)}
                              >
                                {job.est_active ? "Désactiver" : "Activer"}
                              </Button>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            {/* Localisation & Niveau */}
                            <div className="space-y-2">
                              <div className="flex items-center gap-2 text-sm">
                                <MapPin className="w-4 h-4 text-muted-foreground" />
                                <span className="font-medium">Localisation :</span>
                                <span>
                                  {isRemote ? (
                                    <Badge variant="outline" className="ml-1">
                                      <Globe className="w-3 h-3 mr-1" />
                                      Télétravail
                                    </Badge>
                                  ) : (
                                    job.localisation
                                  )}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-sm">
                                <Briefcase className="w-4 h-4 text-muted-foreground" />
                                <span className="font-medium">Niveau :</span>
                                <Badge variant="secondary">{level}</Badge>
                              </div>
                            </div>
                            
                            {/* Expérience & Date */}
                            <div className="space-y-2">
                              <div className="flex items-center gap-2 text-sm">
                                <Clock className="w-4 h-4 text-muted-foreground" />
                                <span className="font-medium">Expérience :</span>
                                <span>{job.experience_min}+ ans</span>
                              </div>
                              <div className="flex items-center gap-2 text-sm">
                                <Calendar className="w-4 h-4 text-muted-foreground" />
                                <span className="font-medium">Publiée le :</span>
                                <span>{formatDate(job.date_publication)}</span>
                              </div>
                            </div>
                          </div>
                          
                          {/* Compétences requises */}
                          <div className="mb-6">
                            <h4 className="font-medium mb-2">Compétences requises :</h4>
                            <div className="flex flex-wrap gap-2">
                              {job.competences_requises?.slice(0, 8).map((skill, index) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  {skill}
                                </Badge>
                              ))}
                              {job.competences_requises?.length > 8 && (
                                <Badge variant="outline" className="text-xs">
                                  +{job.competences_requises.length - 8} autres
                                </Badge>
                              )}
                            </div>
                          </div>
                          
                          {/* Description */}
                          {job.description && (
                            <div className="mb-6">
                              <h4 className="font-medium mb-2">Description :</h4>
                              <p className="text-sm text-muted-foreground line-clamp-3">
                                {job.description.substring(0, 200)}...
                              </p>
                            </div>
                          )}
                          
                          {/* Actions */}
                          <div className="flex gap-3 pt-4 border-t">
                            <Button 
                              variant="default" 
                              className="flex-1 gap-2"
                              onClick={() => {
                                setSelectedJobForMatching(job);
                                setMatchingEnabled(true);
                                setCurrentScoreType('job');
                                setActiveTab("search");
                                toast.info(`Offre sélectionnée pour le matching algorithmique : ${job.titre}`, {
                                  description: "Les scores seront calculés par rapport à cette offre"
                                });
                              }}
                            >
                              <Search className="w-3 h-3" />
                              Comparer avec candidats
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleViewJobDetails(job.id)}
                              className="gap-2"
                            >
                              <Eye className="w-3 h-3" />
                              Voir offre
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => {
                                const jobUrl = `${window.location.origin}/job/${job.id}`;
                                navigator.clipboard.writeText(jobUrl);
                                toast.success("Lien copié dans le presse-papier");
                              }}
                            >
                              <Share2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </main>

        {/* Footer */}
        <footer className="mt-12 py-6 border-t border-border">
          <div className="container mx-auto px-6 text-center text-sm text-muted-foreground">
            <p>SmartHire Platform Recruteur • Recherche avancée de candidats</p>
            <p className="mt-2">
              {candidates.length > 0 && matchingEnabled && selectedJobForMatching ? (
                <span>
                  Affichage de {candidates.length} candidats • Matching algorithmique avec l'offre : <strong>{selectedJobForMatching.titre}</strong>
                </span>
              ) : candidates.length > 0 ? (
                <span>
                  Affichage de {candidates.length} candidats • Recherche simple - pas de matching par offre
                </span>
              ) : (
                <span>Utilisez la recherche pour trouver des candidats qualifiés</span>
              )}
            </p>
          </div>
        </footer>
      </div>
    </AuthGuard>
  );
}