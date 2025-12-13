import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Briefcase, MapPin, Clock, Loader2, Lightbulb, Building, Award, DollarSign, Globe, Upload, FileText, Target, BarChart3, Users, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { matchingService } from "@/services/matchingService";
import type { MatchResult, JobDetails as JobDetailsType } from "@/services/matchingService";
import { ExplainableScoreBreakdown } from "@/components/charts/ExplainableScoreBreakdown";
import { SkillRadarChart } from "@/components/charts/SkillRadarChart";
import { SkillGapList } from "@/components/matching/SkillGapList";
import { useAuth } from "@/hooks/useAuth";
import { CVUpload } from "@/components/candidate/CVUpload";

export default function JobDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [job, setJob] = useState<JobDetailsType | null>(null);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMatching, setIsLoadingMatching] = useState(false);
  const [cvId, setCvId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasApplied, setHasApplied] = useState(false);
  const [searchContext, setSearchContext] = useState<{
    searchType: 'simple' | 'cv_based';
    hasCV: boolean;
    cvId?: string;
    matchScore?: number;
  }>({
    searchType: 'simple',
    hasCV: false
  });
  
  // NOUVEAU ÉTAT : pour afficher le composant d'upload de CV
  const [showCVUpload, setShowCVUpload] = useState(false);

  useEffect(() => {
    if (id && !showCVUpload) {
      loadJobData();
      loadSearchContext();
      if (user?.user_type === 'candidat') {
        checkIfApplied();
      }
    }
  }, [id, user, showCVUpload]);

  // FONCTION CORRIGÉE : Charger le contexte de la recherche précédente
  const loadSearchContext = async () => {
    try {
      console.log('=== CHARGEMENT CONTEXTE JOB DETAILS ===');
      
      // 1. Essayer depuis lastJobContext (depuis CandidateDashboard)
      const lastContext = localStorage.getItem('lastJobContext');
      
      if (lastContext) {
        try {
          const context = JSON.parse(lastContext);
          console.log('Contexte trouvé dans localStorage:', context);
          
          // Vérifier que le contexte est récent (moins de 10 minutes)
          const isRecent = Date.now() - (context.timestamp || 0) < 10 * 60 * 1000;
          
          if (isRecent) {
            setSearchContext({
              searchType: context.searchType,
              hasCV: context.hasCV,
              cvId: context.cvId,
              matchScore: context.matchScore
            });
            
            if (context.hasCV && context.cvId) {
              setCvId(context.cvId.toString());
              console.log('CV ID défini depuis contexte:', context.cvId);
            }
            
            // Ne pas nettoyer tout de suite
            return;
          } else {
            console.log('Contexte trop ancien, nettoyage');
            localStorage.removeItem('lastJobContext');
          }
        } catch (parseError) {
          console.warn('Erreur parsing contexte:', parseError);
          localStorage.removeItem('lastJobContext');
        }
      }
      
      // 2. Fallback: vérifier si le candidat a un CV en base
      console.log('Fallback: vérification CV utilisateur...');
      await checkUserCVDirectly();
      
    } catch (error) {
      console.warn('Erreur chargement contexte:', error);
      // Par défaut
      setSearchContext({
        searchType: 'simple',
        hasCV: false
      });
    }
  };

  // NOUVELLE FONCTION : Vérifier directement si l'utilisateur a un CV
  const checkUserCVDirectly = async () => {
    if (user?.user_type !== 'candidat') return;
    
    try {
      const response = await fetch('http://localhost:5000/api/cv/info', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const cvInfo = await response.json();
        console.log('CV info récupéré directement:', cvInfo);
        
        if (cvInfo.exists && cvInfo.id) {
          setSearchContext({
            searchType: 'cv_based',
            hasCV: true,
            cvId: cvInfo.id.toString(),
            matchScore: undefined
          });
          setCvId(cvInfo.id.toString());
          
          // Mettre à jour localStorage pour la prochaine fois
          localStorage.setItem('candidateSearchType', 'cv_based');
          localStorage.setItem('candidateHasCV', 'true');
          localStorage.setItem('candidateCVId', cvInfo.id.toString());
          
          console.log('CV direct chargé avec succès');
          return true;
        }
      }
    } catch (error) {
      console.warn('CV direct non disponible:', error);
    }
    
    // Fallback: vérifier dans localStorage
    const candidateHasCV = localStorage.getItem('candidateHasCV');
    const candidateCVId = localStorage.getItem('candidateCVId');
    const candidateSearchType = localStorage.getItem('candidateSearchType');
    
    if (candidateHasCV === 'true' && candidateCVId) {
      setSearchContext({
        searchType: (candidateSearchType as 'simple' | 'cv_based') || 'cv_based',
        hasCV: true,
        cvId: candidateCVId,
        matchScore: undefined
      });
      setCvId(candidateCVId);
      console.log('CV chargé depuis localStorage fallback');
      return true;
    }
    
    return false;
  };

  const checkIfApplied = async () => {
    if (!id) return;
    
    try {
      const response = await fetch(`http://localhost:5000/api/candidate/applications?job_id=${id}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const applications = await response.json();
        setHasApplied(applications.some((app: any) => app.job_id.toString() === id));
      }
    } catch (error) {
      console.warn('Impossible de vérifier les candidatures:', error);
    }
  };

  const loadJobData = async () => {
    if (!id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      console.log(`Chargement job: ${id}`);
      
      // 1. Charger détails de l'offre
      const jobData = await matchingService.getJobDetails(id);
      setJob(jobData);
      console.log('Données offre chargées:', jobData);

      // 2. Attendre que le contexte soit chargé, puis charger le matching si nécessaire
      // Le matching sera chargé via useEffect ci-dessous
      
    } catch (error) {
      console.error('Erreur chargement offre:', error);
      const errorMessage = error instanceof Error ? error.message : "Erreur lors du chargement de l'offre";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // CORRIGÉ : Fonction pour charger les données de matching
  const loadMatchingData = async (cvIdParam: string, jobId: string) => {
    setIsLoadingMatching(true);
    try {
      console.log(`Chargement matching avec CV: ${cvIdParam} et Job: ${jobId}`);
      const matching = await matchingService.getMatchAnalysis(cvIdParam, jobId);
      setMatchResult(matching);
      console.log('Matching chargé avec succès:', matching);
      toast.success("Analyse de matching chargée avec succès!");
    } catch (matchingError) {
      console.warn('Matching non disponible:', matchingError);
      setMatchResult(null);
      
      // Si le matching échoue, on reste en mode cv_based mais sans résultats
      toast.warning("Matching détaillé non disponible pour le moment");
    } finally {
      setIsLoadingMatching(false);
    }
  };

  // CORRIGÉ : useEffect pour charger le matching automatiquement
  useEffect(() => {
    const loadMatchingIfNeeded = async () => {
      // Vérifier si on doit charger le matching
      const shouldLoadMatching = 
        searchContext.hasCV && 
        searchContext.searchType === 'cv_based' && 
        searchContext.cvId && 
        id && 
        !matchResult && 
        !isLoadingMatching &&
        !isLoading;
      
      console.log('Vérification chargement matching:', {
        shouldLoadMatching,
        hasCV: searchContext.hasCV,
        searchType: searchContext.searchType,
        cvId: searchContext.cvId,
        jobId: id,
        hasMatchResult: !!matchResult,
        isLoading,
        isLoadingMatching
      });
      
      if (shouldLoadMatching) {
        // Typescript sait maintenant que cvId et id sont définis grâce à shouldLoadMatching
        await loadMatchingData(searchContext.cvId!, id);
      }
    };
    
    loadMatchingIfNeeded();
  }, [searchContext, id, matchResult, isLoading, isLoadingMatching]);

  const handleApply = async () => {
    if (!id || !user || user.user_type !== 'candidat') return;
    
    try {
      setIsLoading(true);
      
      const response = await fetch('http://localhost:5000/api/candidate/applications', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ offre_id: parseInt(id) })
      });

      if (response.ok) {
        setHasApplied(true);
        toast.success("Candidature envoyée avec succès!");
        
        // Envoyer un message automatique au recruteur
        if (job) {
          try {
            await fetch('http://localhost:5000/api/messages/send', {
              method: 'POST',
              credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                recipient_id: job.company, // À adapter selon votre structure
                content: `Bonjour, je suis intéressé par le poste "${job.title}" que vous avez publié. J'ai soumis ma candidature.`
              })
            });
          } catch (messageError) {
            console.warn('Message automatique non envoyé:', messageError);
          }
        }
      } else {
        const error = await response.json();
        throw new Error(error.error || "Erreur lors de la candidature");
      }
    } catch (error) {
      console.error('Erreur candidature:', error);
      const errorMessage = error instanceof Error ? error.message : "Erreur réseau";
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // FONCTION CORRIGÉE : Gestion du succès de l'upload CV
  const handleCVUploadSuccess = async (skills: string[], cvId: number) => {
    try {
      // Mettre à jour le contexte
      setSearchContext({
        searchType: 'cv_based',
        hasCV: true,
        cvId: cvId.toString(),
        matchScore: undefined
      });
      setCvId(cvId.toString());
      
      // Mettre à jour localStorage
      localStorage.setItem('candidateSearchType', 'cv_based');
      localStorage.setItem('candidateHasCV', 'true');
      localStorage.setItem('candidateCVId', cvId.toString());
      
      // Recharger le matching avec le nouveau CV
      if (id) {
        await loadMatchingData(cvId.toString(), id);
      }
      
      // Revenir à la vue de l'offre
      setShowCVUpload(false);
      
      toast.success("CV uploadé avec succès ! Matching mis à jour.");
    } catch (error) {
      console.error('Erreur après upload CV:', error);
      toast.error("CV uploadé mais erreur lors du matching");
      setShowCVUpload(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getExperienceLabel = (experience: number) => {
    if (experience === 0) return "Pas d'expérience requise";
    if (experience === 1) return "1 an d'expérience";
    return `${experience} ans d'expérience`;
  };

  const getMatchQuality = (score: number) => {
    if (score >= 80) return { label: 'Excellent', color: 'text-green-500', bg: 'bg-green-500/10' };
    if (score >= 60) return { label: 'Bon', color: 'text-yellow-500', bg: 'bg-yellow-500/10' };
    if (score >= 40) return { label: 'Moyen', color: 'text-orange-500', bg: 'bg-orange-500/10' };
    return { label: 'Faible', color: 'text-red-500', bg: 'bg-red-500/10' };
  };

  // FONCTION CORRIGÉE : Condition pour afficher le matching complet
  const showFullMatching = searchContext.hasCV && searchContext.searchType === 'cv_based' && cvId;
  const hasBasicScore = searchContext.matchScore !== undefined;
  const currentScore = matchResult?.totalScore || searchContext.matchScore;

  // Log de débogage
  console.log('=== ÉTAT JOB DETAILS ===');
  console.log('showFullMatching:', showFullMatching);
  console.log('searchContext:', searchContext);
  console.log('cvId:', cvId);
  console.log('hasCV:', searchContext.hasCV);
  console.log('searchType:', searchContext.searchType);
  console.log('currentScore:', currentScore);
  console.log('matchResult:', matchResult);
  console.log('isLoadingMatching:', isLoadingMatching);
  console.log('showCVUpload:', showCVUpload);
  console.log('========================');

  // SI ON AFFICHE LE COMPOSANT D'UPLOAD CV
  if (showCVUpload) {
    return (
      <div className="min-h-screen mesh-gradient">
        <header className="border-b border-border glass-strong">
          <div className="container mx-auto px-6 py-4">
            <Button 
              onClick={() => setShowCVUpload(false)} 
              variant="ghost" 
              className="gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à l'offre
            </Button>
          </div>
        </header>
        
        <main className="container mx-auto px-6 py-8 max-w-4xl">
          <Card className="glass-strong mb-6">
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-2">Déposer votre CV pour cette offre</h2>
              <p className="text-muted-foreground mb-4">
                Uploader votre CV pour obtenir une analyse détaillée de matching avec :
              </p>
              <div className="flex items-center gap-2 mb-6">
                <Badge variant="secondary">{job?.company}</Badge>
                <span className="font-medium">{job?.title}</span>
              </div>
            </div>
          </Card>
          
          <CVUpload onUploadSuccess={handleCVUploadSuccess} />
        </main>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen mesh-gradient flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Chargement de l'offre...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen mesh-gradient p-6">
        <div className="max-w-4xl mx-auto">
          <Button onClick={() => navigate("/candidate/dashboard")} variant="ghost" className="gap-2 mb-6">
            <ArrowLeft className="w-4 h-4" />
            Retour
          </Button>
          
          <Card className="glass-strong p-8 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
              <Loader2 className="w-8 h-8 text-destructive" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Erreur de chargement</h1>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={loadJobData}>Réessayer</Button>
          </Card>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen mesh-gradient p-6">
        <div className="max-w-4xl mx-auto">
          <Button onClick={() => navigate("/candidate/dashboard")} variant="ghost" className="gap-2 mb-6">
            <ArrowLeft className="w-4 h-4" />
            Retour aux Offres
          </Button>
          
          <Card className="glass-strong p-8 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Briefcase className="w-8 h-8 text-muted-foreground" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Offre non trouvée</h1>
            <p className="text-muted-foreground mb-4">L'offre avec l'ID {id} n'existe pas ou a été supprimée.</p>
            <Button onClick={() => navigate("/candidate/dashboard")}>Retour aux offres</Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen mesh-gradient">
      <header className="border-b border-border glass-strong">
        <div className="container mx-auto px-6 py-4">
          <Button 
            onClick={() => navigate("/candidate/dashboard")} 
            variant="ghost" 
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour aux Offres
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-6xl">
        {/* Bandeau contextuel - CORRIGÉ */}
        <Card className={`glass-strong p-4 mb-6 ${
          showFullMatching 
            ? 'bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border-blue-200 dark:border-blue-800' 
            : 'bg-gradient-to-r from-gray-50 to-slate-50 dark:from-gray-900/20 dark:to-slate-900/20 border-gray-200 dark:border-gray-800'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {showFullMatching ? (
                <Target className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              ) : (
                <BarChart3 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              )}
              <div>
                <p className={`font-medium ${showFullMatching ? 'text-blue-800 dark:text-blue-300' : 'text-gray-800 dark:text-gray-300'}`}>
                  {showFullMatching ? '🎯 Matching avancé activé' : '🔍 Recherche simple'}
                </p>
                <p className="text-sm text-muted-foreground">
                  {showFullMatching 
                    ? 'Votre CV est analysé pour une correspondance détaillée' 
                    : hasBasicScore 
                      ? 'Score basé sur vos critères de recherche' 
                      : 'Déposez votre CV pour une analyse personnalisée'}
                  {showFullMatching && isLoadingMatching && ' (chargement en cours...)'}
                </p>
              </div>
            </div>
            
            {(currentScore !== undefined) && (
              <div className="text-center">
                <div className="text-3xl font-bold text-gradient">
                  {currentScore}%
                </div>
                <div className={`text-xs font-medium ${getMatchQuality(currentScore).color}`}>
                  {getMatchQuality(currentScore).label}
                </div>
              </div>
            )}
          </div>
          
          {/* Message d'information */}
          {!showFullMatching && (
            <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {hasBasicScore ? (
                <span>Pour une analyse détaillée (compétences manquantes, recommandations, etc.), déposez votre CV.</span>
              ) : (
                <span>Déposez votre CV pour obtenir une analyse complète de matching avec cette offre.</span>
              )}
            </div>
          )}
        </Card>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Contenu principal */}
          <div className="lg:col-span-2 space-y-6">
            {/* En-tête de l'offre */}
            <Card className="glass-strong p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Badge variant="secondary" className="text-sm">
                      {job.company}
                    </Badge>
                    {job.remote && (
                      <Badge variant="outline" className="gap-1">
                        <Globe className="w-3 h-3" />
                        Remote
                      </Badge>
                    )}
                  </div>
                  <h1 className="text-3xl font-bold mb-2 text-gradient">{job.title}</h1>
                  <p className="text-xl text-muted-foreground">{job.company}</p>
                </div>
                {(currentScore !== undefined) && (
                  <div className="text-5xl font-bold text-gradient animate-pulse-glow">
                    {currentScore}%
                  </div>
                )}
              </div>

              {/* Métadonnées */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-primary" />
                  <span className="font-medium">Localisation:</span>
                  <span>{job.location}</span>
                  {job.remote && <Badge variant="outline">Remote</Badge>}
                </div>
                
                <div className="flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-primary" />
                  <span className="font-medium">Expérience:</span>
                  <span>{getExperienceLabel(job.experience)}</span>
                </div>
                
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-primary" />
                  <span className="font-medium">Niveau:</span>
                  <Badge variant="secondary">{job.level || "Non spécifié"}</Badge>
                </div>
                
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  <span className="font-medium">Publiée:</span>
                  <span>{job.posted ? formatDate(job.posted) : "Date non disponible"}</span>
                </div>
              </div>

              {/* Compétences Requises */}
              <div className="mb-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Briefcase className="w-5 h-5" />
                  Compétences Requises:
                </h3>
                <div className="flex flex-wrap gap-2">
                  {job.skills?.length > 0 ? (
                    job.skills.map((skill: string) => (
                      <Badge key={skill} variant="secondary" className="text-sm">
                        {skill}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-muted-foreground italic">Aucune compétence spécifiée</p>
                  )}
                </div>
              </div>

              {/* Description */}
              <div>
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Building className="w-5 h-5" />
                  Description:
                </h3>
                {job.description ? (
                  <div className="bg-surface/50 rounded-lg p-4">
                    <p className="text-muted-foreground whitespace-pre-line">{job.description}</p>
                  </div>
                ) : (
                  <p className="text-muted-foreground italic">Aucune description disponible</p>
                )}
              </div>
            </Card>

            {/* SECTION MATCHING DÉTAILLÉ - SEULEMENT SI showFullMatching = true */}
            {showFullMatching ? (
              isLoadingMatching ? (
                <Card className="glass-strong p-6">
                  <div className="text-center py-8">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-muted-foreground">Calcul du matching en cours...</p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Nous analysons votre CV pour une correspondance détaillée avec cette offre
                    </p>
                  </div>
                </Card>
              ) : matchResult ? (
                <>
                  <ExplainableScoreBreakdown 
                    scoreBreakdown={matchResult.scoreBreakdown}
                    totalScore={matchResult.totalScore}
                  />

                  {matchResult.skillsData && matchResult.skillsData.length > 0 && (
                    <SkillRadarChart skillsData={matchResult.skillsData} />
                  )}

                  {matchResult.missingSkills && matchResult.missingSkills.length > 0 && (
                    <SkillGapList missingSkills={matchResult.missingSkills} />
                  )}
                </>
              ) : (
                <Card className="glass-strong p-6">
                  <div className="text-center py-8">
                    <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mb-4">
                      <Lightbulb className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">Matching non disponible</h3>
                    <p className="text-muted-foreground mb-4">
                      Impossible de charger l'analyse de matching pour le moment.
                      <br />
                      <span className="text-sm">
                        Votre CV est détecté mais le service de matching ne répond pas.
                      </span>
                    </p>
                    <div className="flex gap-2 justify-center">
                      <Button 
                        onClick={() => {
                          if (cvId && id) {
                            loadMatchingData(cvId, id);
                          }
                        }}
                        variant="outline"
                        className="gap-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        Réessayer
                      </Button>
                      <Button 
                        onClick={() => navigate("/candidate/dashboard")}
                        variant="ghost"
                      >
                        Retour aux offres
                      </Button>
                    </div>
                  </div>
                </Card>
              )
            ) : (
              /* SECTION INVITATION À UPLOADER CV - QUAND PAS DE CV */
              <Card className="glass-strong p-6 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20">
                <div className="text-center py-8">
                  <div className="mx-auto w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mb-4">
                    <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">
                    {hasBasicScore ? 'Obtenez une analyse détaillée' : 'Découvrez votre matching personnalisé'}
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    Déposez votre CV pour obtenir une analyse complète de votre compatibilité avec cette offre :
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="text-center p-3">
                      <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900 mx-auto mb-2 flex items-center justify-center">
                        <BarChart3 className="w-5 h-5 text-green-600 dark:text-green-400" />
                      </div>
                      <p className="text-sm font-medium">Score détaillé</p>
                      <p className="text-xs text-muted-foreground">Breakdown par catégorie</p>
                    </div>
                    
                    <div className="text-center p-3">
                      <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900 mx-auto mb-2 flex items-center justify-center">
                        <Target className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                      </div>
                      <p className="text-sm font-medium">Compétences manquantes</p>
                      <p className="text-xs text-muted-foreground">Recommandations ciblées</p>
                    </div>
                    
                    <div className="text-center p-3">
                      <div className="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900 mx-auto mb-2 flex items-center justify-center">
                        <Lightbulb className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                      </div>
                      <p className="text-sm font-medium">Recommandations</p>
                      <p className="text-xs text-muted-foreground">Comment améliorer</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-3 justify-center">
                    
                    <Button 
                      variant="outline"
                      onClick={() => navigate("/candidate/dashboard")}
                    >
                      Retour aux offres
                    </Button>
                  </div>
                  
                  {hasBasicScore && (
                    <div className="mt-4 text-sm text-blue-600 dark:text-blue-400">
                      Votre score actuel basé sur les filtres : <strong>{searchContext.matchScore}%</strong>
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>

          {/* Sidebar avec actions */}
          <div className="space-y-6">
            <Card className="glass-strong p-6 sticky top-6">
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                <Briefcase className="w-5 h-5" />
                Postuler à cette offre
              </h3>
              
              {/* Score de matching si disponible */}
              {(currentScore !== undefined) && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">Votre correspondance:</p>
                    <Badge className={`text-sm ${
                      currentScore >= 80 ? 'bg-green-500' :
                      currentScore >= 60 ? 'bg-yellow-500' : 'bg-orange-500'
                    }`}>
                      {currentScore}%
                    </Badge>
                  </div>
                  
                  {currentScore >= 80 ? (
                    <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                      ✅ Excellent match !
                    </p>
                  ) : currentScore >= 60 ? (
                    <p className="text-sm text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
                      ⚠️ Bon potentiel
                    </p>
                  ) : (
                    <p className="text-sm text-orange-600 dark:text-orange-400 flex items-center gap-1">
                      ⚠️ Correspondance faible
                    </p>
                  )}
                  
                  <p className="text-xs text-muted-foreground mt-2">
                    {showFullMatching && matchResult?.recommendation 
                      ? matchResult.recommendation 
                      : "Déposez votre CV pour des recommandations personnalisées"}
                  </p>
                </div>
              )}
              
              {/* Type de matching */}
              <div className="mb-4">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">Mode:</span>
                  <Badge variant={showFullMatching ? "default" : "outline"} className="text-xs">
                    {showFullMatching ? 'Matching avancé' : 'Recherche simple'}
                  </Badge>
                </div>
              </div>
              
              {/* Boutons d'action */}
              <div className="space-y-3">
                {user?.user_type === 'candidat' ? (
                  <>
                    <Button 
                      onClick={handleApply}
                      disabled={hasApplied || isLoading}
                      className={`w-full gap-2 ${
                        hasApplied 
                          ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed' 
                          : 'bg-gradient-to-r from-primary to-accent hover:scale-[1.02]'
                      } transition-all`}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Traitement...
                        </>
                      ) : hasApplied ? (
                        "✓ Déjà postulé"
                      ) : (
                        "Postuler Maintenant"
                      )}
                    </Button>
                    
                    <Button 
                      variant="outline"
                      className="w-full"
                      onClick={() => navigate(`/messages?new=job-${id}`)}
                    >
                      Contacter le recruteur
                    </Button>
                    
                    
                  </>
                ) : (
                  <div className="text-center py-4">
                    <p className="text-sm text-muted-foreground mb-3">
                      Connectez-vous en tant que candidat pour postuler
                    </p>
                    <Button onClick={() => navigate("/login")}>
                      Se connecter
                    </Button>
                  </div>
                )}
              </div>
              
              {/* Conseils d'amélioration (seulement en mode full matching) */}
              {showFullMatching && matchResult?.missingSkills && matchResult.missingSkills.length > 0 && (
                <div className="mt-4 p-3 bg-surface/50 rounded-lg">
                  <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-500" />
                    Conseils pour améliorer votre matching:
                  </h4>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {matchResult.missingSkills.slice(0, 2).map((skill, idx) => (
                      <li key={idx} className="flex items-start gap-1">
                        <span className="text-primary mt-1">•</span>
                        <span>
                          Développer <strong>{skill.name}</strong> 
                          <span className="text-xs text-gray-500 ml-1">
                            (impact: {skill.impactPercent}%)
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Informations sur l'offre */}
              <div className="mt-4 pt-4 border-t border-border/50">
                <h4 className="font-semibold text-sm mb-2">À propos de cette offre</h4>
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>• ID: {job.id}</p>
                  <p>• Source: {job.company}</p>
                  <p>• Type: {job.remote ? "Remote possible" : "Présentiel"}</p>
                  {job.posted && (
                    <p>• Publiée: {formatDate(job.posted)}</p>
                  )}
                </div>
              </div>
            </Card>

            {/* Offres similaires suggérées */}
            <Card className="glass-strong p-6">
              <h3 className="font-bold text-lg mb-4">Offres similaires</h3>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  D'autres offres qui pourraient vous intéresser
                </p>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => {
                    if (job.skills?.length > 0) {
                      navigate(`/candidate/dashboard?skills=${job.skills.slice(0,3).join(',')}`);
                    } else {
                      navigate("/candidate/dashboard");
                    }
                  }}
                >
                  Voir les offres similaires
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}