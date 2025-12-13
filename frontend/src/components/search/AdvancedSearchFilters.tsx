import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, ChevronDown, X, Plus, Sparkles, Loader2 } from "lucide-react";
import { SearchFilters } from "@/types";
import { searchService } from "@/services/searchService";

interface AdvancedSearchFiltersProps {
  onSearch: (query: string, filters: SearchFilters, mode?: "auto" | "boolean" | "vectoriel" | "hybrid") => void;
  placeholder?: string;
  target?: 'jobs' | 'cvs';
  isLoading?: boolean;
  showSuggestions?: boolean;
  initialQuery?: string;
  initialFilters?: SearchFilters;
}

const MOROCCAN_CITIES = [
  "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", 
  "Agadir", "Meknès", "Oujda", "Kénitra", "Tétouan",
  "Safi", "Mohammedia", "El Jadida", "Béni Mellal", 
  "Nador", "Taza", "Settat", "Khouribga", "Laâyoune",
  "Dakhla", "Any", "Remote"
];

const COMMON_SKILLS = ["React", "TypeScript", "Node.js", "Python", "AWS", "Docker", "PostgreSQL", "Kubernetes", "Java", "JavaScript", "MongoDB", "Git"];

const SEARCH_MODES = [
  { value: "auto", label: "Auto", description: "Le système choisit automatiquement" },
  { value: "boolean", label: "Boolean", description: "Recherche par mots-clés exacts" },
  { value: "vectoriel", label: "Vectoriel", description: "Recherche sémantique intelligente" },
  { value: "hybrid", label: "Hybride", description: "Combine boolean et vectoriel" }
];

export function AdvancedSearchFilters({ 
  onSearch, 
  placeholder = "Rechercher...", 
  target = 'jobs',
  isLoading = false,
  showSuggestions = true,
  initialQuery = "",
  initialFilters
}: AdvancedSearchFiltersProps) {
  const [query, setQuery] = useState(initialQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>(
    initialFilters || {
      location: "Any",
      experience: [0, 10],
      skills: [],
      booleanOperator: "AND",
      remote: false,
    }
  );
  const [skillInput, setSkillInput] = useState("");
  const [searchMode, setSearchMode] = useState<"auto" | "boolean" | "vectoriel" | "hybrid">("auto");
  const [autoSuggestions, setAutoSuggestions] = useState<string[]>([]);
  const [activeFiltersCount, setActiveFiltersCount] = useState(0);

  // Calculer le nombre de filtres actifs
  useEffect(() => {
    let count = 0;
    if (filters.location !== "Any") count++;
    if (filters.skills.length > 0) count++;
    if (filters.remote) count++;
    if (filters.experience[0] > 0 || filters.experience[1] < 10) count++;
    setActiveFiltersCount(count);
  }, [filters]);

  // Autocomplétion seulement quand l'utilisateur tape
  useEffect(() => {
    if (query.length >= 2) {
      fetchAutocomplete();
    } else {
      setAutoSuggestions([]);
    }
  }, [query]);

  const fetchAutocomplete = async () => {
    try {
      const response = await searchService.autocomplete(query);
      setAutoSuggestions(response.suggestions);
    } catch (error) {
      console.error('Erreur autocomplétion:', error);
    }
  };

  // Fonction principale de recherche - appelée uniquement manuellement
  const handleSearchClick = () => {
    onSearch(query, filters, searchMode);
  };

  const addSkill = (skill: string) => {
    const trimmedSkill = skill.trim();
    if (trimmedSkill && !filters.skills.includes(trimmedSkill)) {
      const newSkills = [...filters.skills, trimmedSkill];
      setFilters({ ...filters, skills: newSkills });
      setSkillInput("");
    }
  };

  const removeSkill = (skill: string) => {
    const newSkills = filters.skills.filter(s => s !== skill);
    setFilters({ ...filters, skills: newSkills });
  };

  const handleReset = () => {
    setQuery("");
    setFilters({
      location: "Any",
      experience: [0, 10],
      skills: [],
      booleanOperator: "AND",
      remote: false,
    });
    setSearchMode("auto");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearchClick();
    }
  };

  const handleSkillKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault();
      addSkill(skillInput);
    }
  };

  const applyQuickSearch = (quickQuery: string, quickSkills: string[] = []) => {
    setQuery(quickQuery);
    if (quickSkills.length > 0) {
      setFilters({ ...filters, skills: quickSkills, booleanOperator: "OR" });
    }
  };

  return (
    <Card className="glass-strong p-6">
      {/* Section 1 : Barre de recherche principale */}
      <div className="mb-6">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="pl-10 pr-24 bg-surface border-border"
            disabled={isLoading}
          />
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
            <Button 
              onClick={handleSearchClick}
              size="sm"
              className="gap-1"
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              Chercher
            </Button>
          </div>
        </div>

        {/* Suggestions d'autocomplétion */}
        {autoSuggestions.length > 0 && (
          <div className="mb-4 p-2 bg-background/50 rounded-lg border border-border">
            <p className="text-xs text-muted-foreground mb-1">Suggestions:</p>
            <div className="flex flex-wrap gap-1">
              {autoSuggestions.map((suggestion, index) => (
                <Badge 
                  key={index} 
                  variant="outline" 
                  className="cursor-pointer hover:bg-primary/10"
                  onClick={() => {
                    setQuery(suggestion);
                    setAutoSuggestions([]);
                  }}
                >
                  {suggestion}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Section 2 : Mode de recherche */}
      <div className="mb-6 p-4 border rounded-lg bg-background/50">
        <Label className="text-sm font-medium mb-2 block">Mode de Recherche</Label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {SEARCH_MODES.map((mode) => (
            <Button
              key={mode.value}
              type="button"
              variant={searchMode === mode.value ? "default" : "outline"}
              onClick={() => setSearchMode(mode.value as any)}
              className="text-xs h-auto py-2"
            >
              {mode.label}
            </Button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {SEARCH_MODES.find(m => m.value === searchMode)?.description}
        </p>
      </div>

      {/* Section 3 : Filtres avancés */}
      <Collapsible open={showFilters} onOpenChange={setShowFilters}>
        <CollapsibleTrigger asChild>
          <Button 
            variant="outline" 
            className="w-full justify-between mb-4"
            disabled={isLoading}
          >
            <div className="flex items-center gap-2">
              <span>Filtres avancés</span>
              {activeFiltersCount > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {activeFiltersCount}
                </Badge>
              )}
            </div>
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="space-y-4 pt-4 border-t">
          {/* Localisation */}
          <div>
            <Label>Localisation</Label>
            <Select 
              value={filters.location} 
              onValueChange={(value) => setFilters({ ...filters, location: value })}
              disabled={isLoading}
            >
              <SelectTrigger className="bg-surface border-border">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MOROCCAN_CITIES.map((loc) => (
                  <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Expérience */}
          <div>
            <Label>Expérience: {filters.experience[0]} - {filters.experience[1]} ans</Label>
            <Slider
              value={filters.experience}
              onValueChange={(value) => {
                // Convertir number[] en [number, number]
                const tupleValue: [number, number] = [value[0], value[1]];
                setFilters({ ...filters, experience: tupleValue });
              }}
              min={0}
              max={10}
              step={1}
              className="mt-2"
              disabled={isLoading}
            />
          </div>

          {/* Compétences */}
          <div>
            <Label>Compétences requises</Label>
            <div className="flex gap-2 mt-2 mb-3">
              <Select 
                value={skillInput} 
                onValueChange={(value) => {
                  setSkillInput(value);
                  addSkill(value);
                }}
                disabled={isLoading}
              >
                <SelectTrigger className="flex-1 bg-surface border-border">
                  <SelectValue placeholder="Sélectionner une compétence..." />
                </SelectTrigger>
                <SelectContent>
                  {COMMON_SKILLS.map((skill) => (
                    <SelectItem key={skill} value={skill}>{skill}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                size="icon"
                variant="outline"
                onClick={() => addSkill(skillInput)}
                disabled={!skillInput.trim() || isLoading}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            
            {/* Saisie manuelle */}
            <div className="flex gap-2 mb-2">
              <Input
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyPress={handleSkillKeyPress}
                placeholder="Taper une compétence et appuyer sur Entrée..."
                className="flex-1"
                disabled={isLoading}
              />
            </div>
            
            {/* Opérateur booléen */}
            {filters.skills.length > 0 && (
              <div className="mb-3">
                <Label className="text-sm">Relation entre compétences:</Label>
                <div className="flex gap-2 mt-1">
                  <Button
                    type="button"
                    variant={filters.booleanOperator === "AND" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setFilters({ ...filters, booleanOperator: "AND" })}
                  >
                    ET (toutes les compétences)
                  </Button>
                  <Button
                    type="button"
                    variant={filters.booleanOperator === "OR" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setFilters({ ...filters, booleanOperator: "OR" })}
                  >
                    OU (au moins une compétence)
                  </Button>
                </div>
              </div>
            )}
            
            {/* Badges des compétences */}
            <div className="flex flex-wrap gap-2 mt-2 min-h-10">
              {filters.skills.map((skill, index) => (
                <Badge key={skill} variant="secondary" className="gap-1 px-3 py-1">
                  {index > 0 && (
                    <span className="text-xs text-primary mr-1">{filters.booleanOperator}</span>
                  )}
                  {skill}
                  <X
                    className="w-3 h-3 cursor-pointer hover:text-destructive ml-1"
                    onClick={() => !isLoading && removeSkill(skill)}
                  />
                </Badge>
              ))}
              {filters.skills.length === 0 && (
                <p className="text-sm text-muted-foreground italic">
                  Aucune compétence ajoutée
                </p>
              )}
            </div>
          </div>

          

          {/* Boutons d'action */}
          <div className="flex gap-2 pt-4 border-t">
            <Button 
              onClick={handleSearchClick}
              className="flex-1"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Recherche en cours...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Appliquer les filtres et chercher
                </>
              )}
            </Button>
            <Button 
              onClick={handleReset} 
              variant="outline"
              disabled={isLoading}
            >
              Réinitialiser
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>

     

     
    </Card>
  );
}