import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  ArrowLeft, MapPin, Briefcase, MessageSquare, Loader2, 
  Mail, GraduationCap, Calendar, Target, Search, 
  TrendingUp, CheckCircle, Users, Eye, BarChart3
} from "lucide-react";
import { toast } from "sonner";
import { matchingService } from "@/services/matchingService";
import type { CandidateDetails as CandidateDetailsType, MatchResult, JobInfo } from "@/services/matchingService";
import { ExplainableScoreBreakdown } from "@/components/charts/ExplainableScoreBreakdown";
import { SkillRadarChart } from "@/components/charts/SkillRadarChart";
import { MatchHeatmap } from "@/components/charts/MatchHeatmap";
import { LevelDetectionCard } from "@/components/matching/LevelDetectionCard";
import { SkillGapList } from "@/components/matching/SkillGapList";

export default function CandidateDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState<CandidateDetailsType | null>(null);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [matchingParam, setMatchingParam] = useState<boolean>(false);
  const [scoreType, setScoreType] = useState<'job' | 'search'>('search');
  const [candidateScore, setCandidateScore] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadCandidateData();
      const params = new URLSearchParams(window.location.search);
      const jobId = params.get('jobId');
      const matching = params.get('matching');
      const scoreTypeParam = params.get('scoreType') as 'job' | 'search';
      const scoreParam = params.get('score');
      
      if (scoreParam) {
        setCandidateScore(parseInt(scoreParam, 10));
      }
      
      if (scoreTypeParam) {
        setScoreType(scoreTypeParam);
      }
      
      if (jobId) {
        setSelectedJobId(jobId);
        // CORRECTION : Charger le matching seulement si scoreType='job' ET matching='true'
        if (scoreTypeParam === 'job' && matching === 'true') {
          setMatchingParam(true);
          loadMatchingData(jobId);
        }
      }
    }
  }, [id]);

  const loadCandidateData = async () => {
    if (!id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      console.log(`Chargement candidat: ${id}`);
      
      const candidateData = await matchingService.getCandidateDetails(id);
      setCandidate(candidateData);
      console.log('Données candidat chargées:', candidateData);

    } catch (error) {
      console.error('Erreur chargement:', error);
      const errorMessage = error instanceof Error ? error.message : "Erreur lors du chargement";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMatchingData = async (jobId: string) => {
    if (!id || !candidate?.id) return;
    
    try {
      console.log(`Chargement matching avec job: ${jobId}`);
      const matchingResult = await matchingService.getMatchAnalysis(candidate.id, jobId);
      setMatchResult(matchingResult);
      console.log('Matching chargé:', matchingResult);
      
      toast.success("Analyse de matching chargée avec succès!");
    } catch (matchingError) {
      console.error('Erreur chargement matching:', matchingError);
      toast.warning("Matching détaillé non disponible. Affichage des informations de base.");
      setMatchResult(null);
    }
  };

  const handleContact = () => {
    if (candidate?.email) {
      window.location.href = `mailto:${candidate.email}?subject=Opportunité%20professionnelle&body=Bonjour%20${candidate.name},%0D%0A%0D%0A`;
      toast.info("Client email ouvert");
    } else {
      toast.warning("Email non disponible pour ce candidat");
    }
  };

  const handleViewJobDetails = (jobId: string) => {
    navigate(`/recruiter/jobs/${jobId}`);
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  const getLevelBadgeVariant = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'senior': return 'default';
      case 'expert': return 'destructive';
      case 'intermédiaire': return 'secondary';
      case 'débutant': return 'outline';
      default: return 'secondary';
    }
  };

  const getMatchQuality = (score: number) => {
    if (score >= 80) return { label: 'Excellent', color: 'text-green-500', bg: 'bg-green-500/10' };
    if (score >= 60) return { label: 'Bon', color: 'text-yellow-500', bg: 'bg-yellow-500/10' };
    if (score >= 40) return { label: 'Moyen', color: 'text-orange-500', bg: 'bg-orange-500/10' };
    return { label: 'Faible', color: 'text-red-500', bg: 'bg-red-500/10' };
  };

  if (isLoading) {
    return (
      <div className="min-h-screen mesh-gradient flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Chargement des informations du candidat...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen mesh-gradient p-6">
        <div className="max-w-4xl mx-auto">
          <Button onClick={() => navigate("/recruiter/dashboard")} variant="ghost" className="gap-2 mb-6">
            <ArrowLeft className="w-4 h-4" />
            Retour
          </Button>
          
          <Card className="glass-strong p-8 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
              <Loader2 className="w-8 h-8 text-destructive" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Erreur de chargement</h1>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={loadCandidateData}>Réessayer</Button>
          </Card>
        </div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="min-h-screen mesh-gradient p-6">
        <div className="max-w-4xl mx-auto">
          <Button onClick={() => navigate("/recruiter/dashboard")} variant="ghost" className="gap-2 mb-6">
            <ArrowLeft className="w-4 h-4" />
            Retour
          </Button>
          
          <Card className="glass-strong p-8 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Loader2 className="w-8 h-8 text-muted-foreground" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Candidat non trouvé</h1>
            <p className="text-muted-foreground mb-4">Le candidat avec l'ID {id} n'existe pas ou a été supprimé.</p>
            <Button onClick={() => navigate("/recruiter/dashboard")}>Retour au tableau de bord</Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen mesh-gradient">
      <header className="border-b border-border glass-strong">
        <div className="container mx-auto px-6 py-4">
          <Button onClick={() => navigate("/recruiter/dashboard")} variant="ghost" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Retour au tableau de bord
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-7xl">
        {/* CORRECTION : Afficher selon le scoreType */}
        {scoreType === 'search' ? (
          // SCORE BASÉ SUR LA RECHERCHE
          <Card className="glass-strong p-4 mb-6 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <div>
              
                  <p className="text-sm text-muted-foreground">
                    Ce candidat a été trouvé via une recherche avancée
                    {candidateScore !== null && ` • Score: ${candidateScore}%`}
                    {selectedJobId && !matchingParam && " (une offre est sélectionnée mais le matching n'est pas activé)"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {candidateScore !== null && (
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gradient">
                      {candidateScore}%
                    </div>
                    <div className={`text-xs font-medium ${getMatchQuality(candidateScore).color}`}>
                      {getMatchQuality(candidateScore).label}
                    </div>
                  </div>
                )}
                
              </div>
            </div>
            {selectedJobId && (
              <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
                Pour une analyse détaillée de matching avec cette offre, activez le "Matching" dans le tableau de bord.
              </div>
            )}
          </Card>
        ) : scoreType === 'job' && selectedJobId ? (
          // COMPARAISON AVEC OFFRE (MATCHING)
          <Card className={`glass-strong p-4 mb-6 ${matchResult ? 'bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border-blue-200 dark:border-blue-800' : 'bg-gradient-to-r from-gray-50 to-slate-50 dark:from-gray-900/20 dark:to-slate-900/20 border-gray-200 dark:border-gray-800'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {matchResult ? (
                  <Target className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                ) : (
                  <Search className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                )}
                <div>
                  <p className={`font-medium ${matchResult ? 'text-blue-800 dark:text-blue-300' : 'text-gray-800 dark:text-gray-300'}`}>
                    {matchResult ? 'Comparaison avec offre' : 'Matching en attente'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {matchResult ? 'Analyse de matching détaillée' : 'Chargement de l\'analyse de matching...'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {(matchResult?.totalScore || candidateScore !== null) && (
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gradient">
                      {matchResult?.totalScore || candidateScore}%
                    </div>
                    {(matchResult?.totalScore || candidateScore) && (
                      <div className={`text-xs font-medium ${getMatchQuality(matchResult?.totalScore || candidateScore!).color}`}>
                        {getMatchQuality(matchResult?.totalScore || candidateScore!).label}
                      </div>
                    )}
                  </div>
                )}
               
              </div>
            </div>
            {!matchResult && matchingParam && (
              <div className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                ⏳ L'analyse détaillée de matching est en cours de chargement...
              </div>
            )}
          </Card>
        ) : (
          // AUCUNE COMPARAISON
          <Card className="glass-strong p-4 mb-6 bg-gradient-to-r from-gray-50 to-slate-50 dark:from-gray-900/20 dark:to-slate-900/20 border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <div>
                <p className="font-medium text-gray-800 dark:text-gray-300">
                  Profil candidat seul
                </p>
                <p className="text-sm text-muted-foreground">
                  Aucune comparaison active. Sélectionnez une offre pour voir le matching.
                </p>
              </div>
            </div>
          </Card>
        )}

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Sidebar avec infos candidat */}
          <div className="space-y-6">
            <Card className="glass-strong p-6">
              <div className="flex flex-col items-center text-center mb-6">
                <Avatar className="w-24 h-24 mb-4">
                  <AvatarFallback className="text-2xl bg-gradient-to-br from-primary to-accent text-white">
                    {getInitials(candidate.name)}
                  </AvatarFallback>
                </Avatar>
                <h2 className="text-xl font-bold">{candidate.name}</h2>
                <p className="text-muted-foreground">{candidate.title}</p>
                <Badge 
                  variant={getLevelBadgeVariant(candidate.level)} 
                  className="mt-2"
                >
                  {candidate.level}
                </Badge>
              </div>

              <div className="space-y-3 text-sm">
                {candidate.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-primary" />
                    <span>{candidate.location}</span>
                  </div>
                )}
                
                {candidate.experience > 0 && (
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-primary" />
                    <span>{candidate.experience} ans d'expérience</span>
                  </div>
                )}
                
                {candidate.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-primary" />
                    <span className="truncate">{candidate.email}</span>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-primary" />
                  <span>CV {candidate.id.includes('CV') ? 'uploadé' : 'système'}</span>
                </div>
              </div>

              <div className="mt-6 space-y-2">
                <Button 
                  onClick={handleContact}
                  className="w-full bg-gradient-to-r from-primary to-accent gap-2"
                  disabled={!candidate.email}
                  title={candidate.email ? "Contacter par email" : "Email non disponible"}
                >
                  <MessageSquare className="w-4 h-4" />
                  Contacter
                </Button>
                
                {/* CORRECTION : Afficher seulement si on est en mode matching avec offre */}
                {scoreType === 'job' && selectedJobId && !matchResult && matchingParam && (
                  <Button 
                    variant="outline"
                    className="w-full gap-2"
                    onClick={() => loadMatchingData(selectedJobId)}
                  >
                    <Target className="w-4 h-4" />
                    Charger le matching détaillé
                  </Button>
                )}
              </div>
            </Card>

            {/* Section niveau détecté - seulement si matching disponible */}
            {matchResult?.level && (
              <LevelDetectionCard
                level={matchResult.level.level}
                confidence={matchResult.level.confidence}
                reasons={matchResult.level.reasons}
              />
            )}

            {/* Statistiques du profil */}
            <Card className="glass-strong p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Statistiques du profil
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground">Compétences</p>
                  <p className="text-lg font-semibold">{candidate.skills?.length || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Expérience</p>
                  <p className="text-lg font-semibold">{candidate.experience || 0} ans</p>
                </div>
                {(matchResult?.totalScore || candidateScore !== null) && (
                  <div>
                    <p className="text-sm text-muted-foreground">Score {scoreType === 'job' ? 'matching' : 'recherche'}</p>
                    <div className="flex items-center gap-2">
                      <p className="text-lg font-semibold text-primary">
                        {matchResult?.totalScore || candidateScore}%
                      </p>
                      <Badge className={`text-xs ${getMatchQuality(matchResult?.totalScore || candidateScore!).bg} ${getMatchQuality(matchResult?.totalScore || candidateScore!).color}`}>
                        {getMatchQuality(matchResult?.totalScore || candidateScore!).label}
                      </Badge>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Contenu principal */}
          <div className="lg:col-span-3 space-y-6">
            {/* En-tête avec score si matching disponible */}
            <Card className="glass-strong p-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h1 className="text-3xl font-bold text-gradient">Profil Candidat</h1>
                  {matchResult?.job && (
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-sm">
                        Comparaison avec: {matchResult.job.title}
                      </Badge>
                      <Badge variant="secondary" className="text-sm">
                        {matchResult.job.company}
                      </Badge>
                    </div>
                  )}
                  {scoreType === 'search' && (
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-sm bg-blue-100 text-blue-800 border-blue-300">
                        <BarChart3 className="w-3 h-3 mr-1" />
                        Score basé sur recherche
                      </Badge>
                      {candidateScore !== null && (
                        <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-sm">
                          {candidateScore}% correspondance
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
                {(matchResult?.totalScore || candidateScore !== null) && (
                  <div className="text-center">
                    <div className="text-5xl font-bold text-gradient animate-pulse-glow">
                      {matchResult?.totalScore || candidateScore}%
                    </div>
                    <div className={`text-sm font-medium mt-1 ${getMatchQuality(matchResult?.totalScore || candidateScore!).color}`}>
                      {getMatchQuality(matchResult?.totalScore || candidateScore!).label}
                    </div>
                  </div>
                )}
              </div>

              {/* Compétences */}
              <div className="mb-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Briefcase className="w-5 h-5" />
                  Compétences:
                </h3>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills?.length > 0 ? (
                    candidate.skills.map((skill: string) => (
                      <Badge key={skill} variant="secondary" className="text-sm">
                        {skill}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-muted-foreground italic">Aucune compétence spécifiée</p>
                  )}
                </div>
              </div>

              {/* Résumé CV */}
              <div>
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <GraduationCap className="w-5 h-5" />
                  Résumé CV:
                </h3>
                {candidate.cvSummary ? (
                  <div className="bg-surface/50 rounded-lg p-4">
                    <p className="text-muted-foreground whitespace-pre-line">{candidate.cvSummary}</p>
                  </div>
                ) : (
                  <p className="text-muted-foreground italic">Aucun résumé disponible</p>
                )}
              </div>
            </Card>

            {/* Section matching détaillée si disponible */}
            {matchResult ? (
              <>
                <ExplainableScoreBreakdown 
                  scoreBreakdown={matchResult.scoreBreakdown}
                  totalScore={matchResult.totalScore}
                />

                {matchResult.skillsData && matchResult.skillsData.length > 0 && (
                  <SkillRadarChart skillsData={matchResult.skillsData} />
                )}

                {matchResult.fitCriteria && matchResult.fitCriteria.length > 0 && (
                  <MatchHeatmap 
                    fitCriteria={matchResult.fitCriteria}
                    recommendation={matchResult.recommendation}
                  />
                )}

                {matchResult.missingSkills && matchResult.missingSkills.length > 0 && (
                  <SkillGapList missingSkills={matchResult.missingSkills} />
                )}
              </>
            ) : scoreType === 'job' && selectedJobId && matchingParam ? (
              <Card className="glass-strong p-6">
                <div className="text-center py-8">
                  <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
                    <Loader2 className="w-6 h-6 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Matching en cours de calcul</h3>
                  <p className="text-muted-foreground mb-4">
                    L'analyse détaillée de matching est en cours de chargement...
                  </p>
                  <div className="flex gap-3 justify-center">
                    <Button onClick={() => loadMatchingData(selectedJobId)}>
                      Recharger le matching
                    </Button>
                    <Button variant="outline" onClick={() => navigate(`/recruiter/jobs/${selectedJobId}`)}>
                      Voir l'offre
                    </Button>
                  </div>
                </div>
              </Card>
            ) : scoreType === 'search' ? (
              <Card className="glass-strong p-6">
                <div className="text-center py-8">
                  <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mb-4">
                    <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Score basé sur recherche</h3>
                  <p className="text-muted-foreground mb-4">
                    Ce candidat a été évalué selon vos critères de recherche.
                    {selectedJobId 
                      ? " Pour une analyse détaillée avec cette offre, activez le matching dans le tableau de bord." 
                      : " Pour une analyse détaillée avec une offre spécifique, sélectionnez une offre dans le tableau de bord."}
                  </p>
                  <div className="flex gap-3 justify-center">
                    <Button 
                      onClick={() => navigate("/recruiter/dashboard")} 
                      className="gap-2"
                    >
                      <Search className="w-4 h-4" />
                      Retour au tableau de bord
                    </Button>
                    {selectedJobId && (
                      <Button 
                        variant="outline"
                        onClick={() => {
                          // CORRECTION : Naviguer vers le dashboard avec les paramètres pour activer le matching
                          navigate(`/recruiter/dashboard?jobId=${selectedJobId}&activateMatching=true`);
                        }}
                      >
                        <Target className="w-4 h-4 mr-2" />
                        Activer le matching
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            ) : (
              // Cas où scoreType n'est ni 'job' ni 'search' (ne devrait pas arriver)
              <Card className="glass-strong p-6">
                <div className="text-center py-8">
                  <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-900 flex items-center justify-center mb-4">
                    <Users className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Aucune comparaison active</h3>
                  <p className="text-muted-foreground mb-4">
                    Pour voir le matching détaillé, sélectionnez une offre dans le tableau de bord.
                  </p>
                  <Button onClick={() => navigate("/recruiter/dashboard")} className="gap-2">
                    <Search className="w-4 h-4" />
                    Retour au tableau de bord
                  </Button>
                </div>
              </Card>
            )}

            {/* Section informations de matching si disponible */}
            {matchResult?.candidate && matchResult?.job && (
              <Card className="glass-strong p-6">
                <h3 className="font-semibold mb-4 text-lg">Synthèse du Matching</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-primary flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Points forts
                    </h4>
                    <ul className="space-y-2 text-sm">
                      {matchResult.fitCriteria
                        .filter(criteria => criteria.matchPercent >= 80)
                        .slice(0, 3)
                        .map((criteria, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <div className="w-2 h-2 rounded-full bg-green-500 mt-1.5 flex-shrink-0" />
                            <div>
                              <span className="font-medium">{criteria.name}: </span>
                              <span className="text-muted-foreground">{criteria.candidate}</span>
                              <Badge className="ml-2 text-xs bg-green-500/20 text-green-600">
                                {criteria.matchPercent}%
                              </Badge>
                            </div>
                          </li>
                        ))}
                    </ul>
                  </div>
                  <div className="space-y-4">
                    <h4 className="font-medium text-accent flex items-center gap-2">
                      <Target className="w-5 h-5" />
                      Détails de l'offre
                    </h4>
                    <div className="space-y-2 text-sm">
                      <p><span className="font-medium">Poste:</span> {matchResult.job.title}</p>
                      <p><span className="font-medium">Entreprise:</span> {matchResult.job.company}</p>
                      <p><span className="font-medium">Localisation:</span> {matchResult.job.location}</p>
                      <p><span className="font-medium">Expérience requise:</span> {matchResult.job.experience} ans</p>
                     
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}