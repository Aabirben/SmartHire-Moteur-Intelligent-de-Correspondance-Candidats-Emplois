import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileText, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { cvService } from "@/services/cvService";

interface CVUploadProps {
  onUploadSuccess: (skills: string[], cvId: number) => void;
  onHealthCheck?: (health: any) => void;
}

export function CVUpload({ onUploadSuccess, onHealthCheck }: CVUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [uploadStats, setUploadStats] = useState<any>(null);

  // Vérifier l'état des services
  const checkHealth = useCallback(async () => {
    try {
      const health = await cvService.healthCheck();
      setHealthStatus(health);
      
      if (onHealthCheck) {
        onHealthCheck(health);
      }
      
      if (health.status === 'degraded') {
        toast.warning('Certains services sont dégradés', {
          description: 'Vérifiez la console pour plus de détails',
        });
        console.log('Health check details:', health);
      }
      
      return health;
    } catch (error) {
      console.error('Health check failed:', error);
      toast.error('Impossible de vérifier les services');
      return null;
    }
  }, [onHealthCheck]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const validation = cvService.validateFile(droppedFile);
      if (validation.valid) {
        setFile(droppedFile);
        toast.success('Fichier prêt pour upload');
      } else {
        validation.errors.forEach(error => toast.error(error));
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const validation = cvService.validateFile(selectedFile);
      if (validation.valid) {
        setFile(selectedFile);
        toast.success('Fichier sélectionné');
      } else {
        validation.errors.forEach(error => toast.error(error));
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("Veuillez sélectionner un fichier PDF");
      return;
    }

    setIsProcessing(true);
    toast.info('Début du traitement du CV...');
    
    try {
      // Vérifier les services d'abord
      const health = await checkHealth();
      if (!health || health.status === 'degraded') {
        toast.warning('Upload en mode dégradé. Certaines fonctionnalités peuvent être limitées.');
      }

      // Upload le fichier
      const result = await cvService.uploadCV(file);
      
      setUploadStats({
        nb_competences: result.stats.nb_competences,
        annees_experience: result.stats.annees_experience,
        has_skills_section: result.stats.has_skills_section,
      });
      
      toast.success("CV uploadé et analysé avec succès!", {
        description: `${result.stats.nb_competences} compétences détectées`,
      });
      
      // Appeler le callback avec les compétences et l'ID du CV
      onUploadSuccess(result.skills, result.cv_id);
      
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error("Erreur lors de l'upload", {
        description: error.message || 'Veuillez réessayer',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setUploadStats(null);
    toast.info('Fichier retiré');
  };

  const handleAnalyzeExistingCV = async () => {
    try {
      setIsProcessing(true);
      const cvInfo = await cvService.getCVInfo();
      
      if (cvInfo.exists) {
        toast.success('CV trouvé', {
          description: `${cvInfo.competences.length} compétences détectées`,
        });
        
        // Appeler le callback avec les compétences existantes
        onUploadSuccess(cvInfo.competences, cvInfo.id);
        
        setUploadStats({
          nb_competences: cvInfo.competences.length,
          annees_experience: cvInfo.annees_experience,
          indexed_in_whoosh: cvInfo.indexed_in_whoosh,
        });
      } else {
        toast.info('Aucun CV trouvé', {
          description: 'Uploader un nouveau CV',
        });
      }
    } catch (error: any) {
      toast.error('Erreur', {
        description: error.message,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeleteCV = async () => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer votre CV ?')) {
      return;
    }
    
    try {
      const result = await cvService.deleteCV();
      toast.success(result.message);
      setFile(null);
      setUploadStats(null);
    } catch (error: any) {
      toast.error('Erreur', {
        description: error.message,
      });
    }
  };

  return (
    <Card className="glass-strong p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gradient">Uploader Votre CV</h2>
        
      </div>
      
      
      
      {/* Zone de drop */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
          isDragging ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-border'
        }`}
      >
        {file ? (
          <div className="flex flex-col items-center gap-4">
            <FileText className="w-16 h-16 text-accent" />
            <div>
              <p className="font-semibold">{file.name}</p>
              <p className="text-sm text-muted-foreground">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleRemoveFile}
                size="sm"
              >
                Retirer
              </Button>
              {uploadStats && (
                <Button
                  variant="outline"
                  onClick={handleDeleteCV}
                  size="sm"
                  className="text-destructive"
                >
                  Supprimer CV
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <Upload className="w-16 h-16 text-muted-foreground" />
            <div>
              <p className="font-semibold mb-2">Déposez votre CV ici ou cliquez pour parcourir</p>
              <p className="text-sm text-muted-foreground">PDF uniquement, max 5MB</p>
            </div>
            <label htmlFor="cv-upload">
              <Button variant="outline" asChild>
                <span>Parcourir les fichiers</span>
              </Button>
            </label>
            <input
              id="cv-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        )}
      </div>
      
      {/* Statistiques d'upload */}
      {uploadStats && (
        <div className="mt-4 p-4 bg-primary/5 rounded-lg">
          <h4 className="font-semibold mb-2">Résultats de l'analyse</h4>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <p className="text-2xl font-bold">{uploadStats.nb_competences}</p>
              <p className="text-muted-foreground">Compétences</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">{uploadStats.annees_experience}</p>
              <p className="text-muted-foreground">Années exp.</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">
                {uploadStats.indexed_in_whoosh ? '✅' : '⚠️'}
              </p>
              <p className="text-muted-foreground">Indexé</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Boutons d'action */}
      <div className="flex gap-3 mt-6">
        <Button
          onClick={handleUpload}
          disabled={!file || isProcessing}
          className="flex-1 bg-gradient-to-r from-primary to-accent hover:scale-[1.02] transition-all glow-primary"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Traitement du CV...
            </>
          ) : (
            "Uploader & Analyser"
          )}
        </Button>
        
        <Button
          variant="outline"
          onClick={handleAnalyzeExistingCV}
          disabled={isProcessing}
          className="flex-1"
        >
          Vérifier CV existant
        </Button>
      </div>
      
      
    </Card>
  );
}