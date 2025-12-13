import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { X, Plus, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { Job } from "@/types";
import { jobService, JobData } from "@/services/jobService";

interface JobPostFormProps {
  onJobPosted: (job: Job) => void;
}

// Liste des villes marocaines avec option de télétravail
const LOCATION_OPTIONS = [
  { value: "remote", label: "🌍 Télétravail / Remote", isRemote: true },
  { value: "Casablanca", label: "Casablanca" },
  { value: "Rabat", label: "Rabat" },
  { value: "Marrakech", label: "Marrakech" },
  { value: "Fès", label: "Fès" },
  { value: "Tanger", label: "Tanger" },
  { value: "Agadir", label: "Agadir" },
  { value: "Meknès", label: "Meknès" },
  { value: "Oujda", label: "Oujda" },
  { value: "Kenitra", label: "Kenitra" },
  { value: "Tétouan", label: "Tétouan" },
  { value: "Safi", label: "Safi" },
  { value: "Mohammédia", label: "Mohammédia" },
  { value: "Khouribga", label: "Khouribga" },
  { value: "El Jadida", label: "El Jadida" },
  { value: "Nador", label: "Nador" },
  { value: "Béni Mellal", label: "Béni Mellal" },
  { value: "Taza", label: "Taza" },
  { value: "Essaouira", label: "Essaouira" },
  { value: "Larache", label: "Larache" },
  { value: "Khemisset", label: "Khemisset" },
  { value: "Guelmim", label: "Guelmim" },
  { value: "Errachidia", label: "Errachidia" },
  { value: "Taroudant", label: "Taroudant" },
  { value: "Berrechid", label: "Berrechid" },
  { value: "Sidi Slimane", label: "Sidi Slimane" },
  { value: "Sidi Kacem", label: "Sidi Kacem" },
  { value: "Azrou", label: "Azrou" },
  { value: "Midelt", label: "Midelt" },
  { value: "Settat", label: "Settat" },
  { value: "Al Hoceïma", label: "Al Hoceïma" },
  { value: "Tiznit", label: "Tiznit" },
  { value: "Dakhla", label: "Dakhla" },
  { value: "Laâyoune", label: "Laâyoune" },
  { value: "Chefchaouen", label: "Chefchaouen" },
  { value: "Ifrane", label: "Ifrane" }
];

export function JobPostForm({ onJobPosted }: JobPostFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(false);
  const [isRecruiter, setIsRecruiter] = useState<boolean | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    company: "",
    location: "",
    remote: false,
    experience: "",
    description: "",
    skills: [] as string[],
  });
  const [skillInput, setSkillInput] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  // Utiliser useEffect pour le chargement initial
  useEffect(() => {
    checkRecruiterAuth();
  }, []);

  const checkRecruiterAuth = async () => {
    setIsCheckingAuth(true);
    console.log('[JobPostForm] Vérification de l\'authentification du recruteur...');
    
    try {
      const recruiterStatus = await jobService.checkRecruiterAuth();
      setIsRecruiter(recruiterStatus);
      
      console.log('[JobPostForm] Résultat de la vérification d\'authentification:', recruiterStatus);
      
      if (!recruiterStatus) {
        toast.warning('Veuillez vous connecter en tant que recruteur pour publier des offres d\'emploi', {
          description: 'Redirection vers la page de connexion...',
        });
      }
    } catch (error) {
      console.error('[JobPostForm] Échec de la vérification d\'authentification:', error);
      setIsRecruiter(false);
      toast.error('Impossible de vérifier votre statut');
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const validateField = (name: string, value: any): string => {
    switch (name) {
      case "title":
        if (!value.trim()) return "Le titre du poste est requis";
        return value.length < 5 ? "Le titre doit comporter au moins 5 caractères" : "";
      
      case "company":
        return !value.trim() ? "Le nom de l'entreprise est requis" : "";
      
      case "description":
        if (!value.trim()) return "La description est requise";
        return value.length < 50 ? "La description doit comporter au moins 50 caractères" : "";
      
      case "skills":
        return value.length < 3 ? "Veuillez ajouter au moins 3 compétences" : "";
      
      case "experience":
        if (!value.trim()) return "L'année d'expérience est requise";
        if (isNaN(Number(value)) || Number(value) < 0) return "Veuillez entrer un nombre valide";
        return "";
      
      case "location":
        return !value.trim() ? "Veuillez sélectionner une localisation" : "";
      
      default:
        return !value ? "Ce champ est requis" : "";
    }
  };

  const validateAllFields = () => {
    const newErrors: Record<string, string> = {};
    
    const fieldsToValidate = ['title', 'company', 'location', 'experience', 'description', 'skills'];
    
    fieldsToValidate.forEach((key) => {
      const error = validateField(key, formData[key as keyof typeof formData]);
      if (error) newErrors[key] = error;
    });
    
    return newErrors;
  };

  const handleChange = (name: string, value: any) => {
    setFormData({ ...formData, [name]: value });
    
    // Effacer l'erreur pour ce champ lorsque l'utilisateur tape
    if (errors[name]) {
      setErrors({ ...errors, [name]: "" });
    }
    setServerError(null);
    setSuccessMessage(null);
  };

  const handleLocationChange = (value: string) => {
    const isRemote = value === "remote";
    setFormData({ 
      ...formData, 
      location: isRemote ? "Télétravail" : value,
      remote: isRemote
    });
    
    // Effacer l'erreur de localisation
    if (errors.location) {
      setErrors({ ...errors, location: "" });
    }
  };

  const addSkill = () => {
    const trimmedSkill = skillInput.trim();
    if (trimmedSkill && !formData.skills.includes(trimmedSkill)) {
      const newSkills = [...formData.skills, trimmedSkill];
      handleChange("skills", newSkills);
      setSkillInput("");
      
      // Effacer l'erreur des compétences
      if (errors.skills) {
        setErrors({ ...errors, skills: "" });
      }
    }
  };

  const removeSkill = (skill: string) => {
    const newSkills = formData.skills.filter(s => s !== skill);
    handleChange("skills", newSkills);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);
    setSuccessMessage(null);
    setShowSuccess(false);

    // Vérifier l'authentification
    if (!isRecruiter) {
      toast.error('Seuls les recruteurs peuvent publier des offres d\'emploi');
      await checkRecruiterAuth();
      return;
    }

    // Valider tous les champs
    const newErrors = validateAllFields();

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      
      const errorFields = Object.keys(newErrors);
      const errorMessage = `Veuillez corriger les erreurs suivantes:\n${errorFields.map(field => {
        const fieldName = field === 'skills' ? 'compétences (au moins 3 requises)' : field;
        return `• ${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)}: ${newErrors[field]}`;
      }).join('\n')}`;
      
      toast.error("Échec de la validation du formulaire", {
        description: errorMessage,
        duration: 5000,
      });
      return;
    }

    // Préparer les données pour l'API
    const jobData: JobData = {
      title: formData.title,
      company: formData.company,
      location: formData.location,
      remote: formData.remote,
      salaryMin: 0, // Valeur par défaut
      salaryMax: 0, // Valeur par défaut
      experience: Number(formData.experience),
      description: formData.description,
      skills: formData.skills,
    };

    // Validation par le service
    const validation = jobService.validateJobData(jobData);
    if (!validation.valid) {
      validation.errors.forEach(error => toast.error(error));
      return;
    }

    console.log('[JobPostForm] Soumission des données de l\'offre:', {
      ...jobData,
      skillsCount: jobData.skills.length,
      timestamp: new Date().toISOString()
    });

    setIsSubmitting(true);

    try {
      // Envoyer au backend
      const result = await jobService.createJob(jobData);
      
      // Extraire l'ID de l'offre de la réponse
      const jobId = result.id || result.job_id || result.id_offre;
      
      console.log('[JobPostForm] Offre créée avec succès:', {
        jobId: jobId,
        response: result,
        timestamp: new Date().toISOString()
      });

      // Créer l'objet Job pour le frontend
      const newJob: Job = {
        id: `job-${jobId}`,
        title: result.titre,
        company: result.entreprise || formData.company,
        location: result.localisation,
        remote: result.type_contrat === 'télétravail',
        salary: { 
          min: 0, 
          max: 0 
        },
        experience: result.experience_min,
        skills: result.competences_requises || jobData.skills,
        description: result.description,
        posted: result.date_publication ? result.date_publication.split('T')[0] : new Date().toISOString().split('T')[0],
      };

      // Appeler le callback
      onJobPosted(newJob);
      
      // Définir le message de succès
      const successMsg = `L'offre "${formData.title}" a été publiée avec succès !`;
      setSuccessMessage(successMsg);
      setShowSuccess(true);
      
      // Afficher le toast
      toast.success(successMsg, {
        duration: 3000,
      });

      // Réinitialiser le formulaire après un délai
      setTimeout(() => {
        setFormData({
          title: "",
          company: "",
          location: "",
          remote: false,
          experience: "",
          description: "",
          skills: [],
        });
        setErrors({});
        setSkillInput("");
        setSuccessMessage(null);
        setShowSuccess(false);
      }, 2000);
      
    } catch (error: any) {
      console.error('[JobPostForm] Erreur de soumission:', {
        error: error.message,
        jobData,
        timestamp: new Date().toISOString()
      });
      
      setServerError(error.message || 'Une erreur est survenue lors de la soumission');
      toast.error("Erreur lors de la publication de l'offre", {
        description: error.message || 'Veuillez réessayer',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Si la vérification d'authentification est toujours en cours
  if (isCheckingAuth) {
    return (
      <Card className="glass-strong p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 mr-2 animate-spin" />
          <p>Vérification de votre statut...</p>
        </div>
      </Card>
    );
  }

  // Si l'utilisateur n'est pas recruteur
  if (isRecruiter === false) {
    return (
      <Card className="glass-strong p-6">
        <div className="text-center space-y-4">
          <AlertCircle className="w-16 h-16 mx-auto text-destructive" />
          <h2 className="text-2xl font-bold">Réservé aux recruteurs</h2>
          <p className="text-muted-foreground">
            Vous devez être connecté en tant que recruteur pour publier des offres d'emploi.
          </p>
          <Button 
            onClick={checkRecruiterAuth}
            variant="outline"
            className="mt-4"
          >
            <Loader2 className={`w-4 h-4 mr-2 ${isCheckingAuth ? 'animate-spin' : ''}`} />
            Vérifier à nouveau le statut
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="glass-strong p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gradient">Publier une nouvelle offre</h2>
        {isRecruiter && (
          <div className="flex items-center gap-2 text-sm text-green-600">
            <CheckCircle className="w-4 h-4" />
            <span>Connecté en tant que recruteur</span>
          </div>
        )}
      </div>
      
      {/* Message de succès */}
      {showSuccess && successMessage && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span className="font-semibold text-green-800">{successMessage}</span>
          </div>
        </div>
      )}

      {/* Erreur serveur */}
      {serverError && (
        <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-destructive" />
            <span className="font-semibold text-destructive">Erreur serveur</span>
          </div>
          <p className="text-sm">{serverError}</p>
        </div>
      )}

      {/* Résumé des erreurs de validation */}
      {Object.keys(errors).length > 0 && (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-yellow-600" />
            <span className="font-semibold text-yellow-800">Erreurs de validation</span>
          </div>
          <ul className="text-sm text-yellow-700 list-disc list-inside space-y-1">
            {Object.entries(errors).map(([field, error]) => (
              <li key={field}>
                <span className="font-medium">{field}:</span> {error}
              </li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="title">Titre du poste *</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => handleChange("title", e.target.value)}
            placeholder="ex: Développeur Full Stack Senior"
            className={`bg-surface ${errors.title ? 'border-destructive' : ''}`}
          />
          {errors.title && <p className="text-xs text-destructive mt-1">{errors.title}</p>}
        </div>

        <div>
          <Label htmlFor="company">Entreprise *</Label>
          <Input
            id="company"
            value={formData.company}
            onChange={(e) => handleChange("company", e.target.value)}
            placeholder="Nom de votre entreprise"
            className={`bg-surface ${errors.company ? 'border-destructive' : ''}`}
          />
          {errors.company && <p className="text-xs text-destructive mt-1">{errors.company}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="location">Localisation *</Label>
            <Select 
              value={formData.location === "Télétravail" ? "remote" : formData.location}
              onValueChange={handleLocationChange}
            >
              <SelectTrigger className={`bg-surface ${errors.location ? 'border-destructive' : ''}`}>
                <SelectValue placeholder="Sélectionner une localisation" />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                {LOCATION_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.location && <p className="text-xs text-destructive mt-1">{errors.location}</p>}
          </div>

          <div>
            <Label htmlFor="experience">Années d'expérience *</Label>
            <Select 
              value={formData.experience.toString()} 
              onValueChange={(value) => handleChange("experience", value)}
            >
              <SelectTrigger className={`bg-surface ${errors.experience ? 'border-destructive' : ''}`}>
                <SelectValue placeholder="Sélectionner" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">0-1 an (Junior)</SelectItem>
                <SelectItem value="1">1-2 ans</SelectItem>
                <SelectItem value="2">2-3 ans</SelectItem>
                <SelectItem value="3">3-5 ans (Intermédiaire)</SelectItem>
                <SelectItem value="5">5-8 ans (Senior)</SelectItem>
                <SelectItem value="8">8-10 ans</SelectItem>
                <SelectItem value="10">10+ ans (Expert)</SelectItem>
              </SelectContent>
            </Select>
            {errors.experience && <p className="text-xs text-destructive mt-1">{errors.experience}</p>}
          </div>
        </div>

        <div>
          <Label htmlFor="description">Description du poste *</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => handleChange("description", e.target.value)}
            placeholder="Décrivez le rôle, les responsabilités et les exigences..."
            rows={4}
            className={`bg-surface ${errors.description ? 'border-destructive' : ''}`}
          />
          <div className="text-xs text-muted-foreground mt-1">
            {formData.description.length}/50 caractères minimum
          </div>
          {errors.description && <p className="text-xs text-destructive mt-1">{errors.description}</p>}
        </div>

        <div>
          <Label>Compétences requises * (au moins 3)</Label>
          <div className="flex gap-2 mt-2">
            <Input
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
              placeholder="Ajouter une compétence..."
              className="bg-surface"
            />
            <Button type="button" onClick={addSkill} size="icon" variant="outline">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <div className="mt-2 text-sm text-muted-foreground">
            Suggestions : React, Python, Node.js, Java, AWS, Docker, PHP, Angular, Vue.js
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {formData.skills.map((skill) => (
              <Badge key={skill} variant="secondary" className="gap-1 pl-3 pr-2">
                {skill}
                <X
                  className="w-3 h-3 cursor-pointer hover:text-destructive"
                  onClick={() => removeSkill(skill)}
                />
              </Badge>
            ))}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {formData.skills.length} compétence(s) ajoutée(s)
          </div>
          {errors.skills && <p className="text-xs text-destructive mt-1">{errors.skills}</p>}
        </div>

        <div className="pt-4 border-t">
          <Button
            type="submit"
            disabled={isSubmitting || !isRecruiter}
            className="w-full bg-gradient-to-r from-primary to-accent hover:scale-[1.02] transition-all"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Publication en cours...
              </>
            ) : (
              "Publier l'offre"
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}