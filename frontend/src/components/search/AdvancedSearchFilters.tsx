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
import { Search, ChevronDown, X, Plus, Sparkles } from "lucide-react";
import { SearchFilters } from "@/types";

interface AdvancedSearchFiltersProps {
  onSearch: (query: string, filters: SearchFilters) => void;
  placeholder?: string;
}

const LOCATIONS = ["San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA", "Remote", "Any"];
const COMMON_SKILLS = ["React", "TypeScript", "Node.js", "Python", "AWS", "Docker", "PostgreSQL", "Kubernetes"];
const SUGGESTIONS = [
  "React AND TypeScript",
  "Senior Developer OR Lead Engineer",
  "AWS AND (Docker OR Kubernetes)",
  "Python AND Machine Learning"
];

export function AdvancedSearchFilters({ onSearch, placeholder = "Search..." }: AdvancedSearchFiltersProps) {
  const [query, setQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    location: "Any",
    experience: [0, 10],
    salary: [50, 200],
    skills: [],
    booleanOperator: "AND",
    remote: false
  });
  const [skillInput, setSkillInput] = useState("");

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (query || filters.skills.length > 0) {
        onSearch(query, filters);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query, filters]);

  const addSkill = (skill: string) => {
    if (skill && !filters.skills.includes(skill)) {
      setFilters({ ...filters, skills: [...filters.skills, skill] });
      setSkillInput("");
    }
  };

  const removeSkill = (skill: string) => {
    setFilters({ ...filters, skills: filters.skills.filter(s => s !== skill) });
  };

  const handleReset = () => {
    setQuery("");
    setFilters({
      location: "Any",
      experience: [0, 10],
      salary: [50, 200],
      skills: [],
      booleanOperator: "AND",
      remote: false
    });
    onSearch("", {
      location: "Any",
      experience: [0, 10],
      salary: [50, 200],
      skills: [],
      booleanOperator: "AND",
      remote: false
    });
  };

  const applySuggestion = (suggestion: string) => {
    setQuery(suggestion);
    onSearch(suggestion, filters);
  };

  return (
    <Card className="glass-strong p-6">
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="pl-10 bg-surface border-border"
        />
      </div>

      {query && (
        <div className="mb-4 flex flex-wrap gap-2">
          <span className="text-sm text-muted-foreground flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-accent" />
            Smart suggestions:
          </span>
          {SUGGESTIONS.map((suggestion) => (
            <Button
              key={suggestion}
              variant="outline"
              size="sm"
              onClick={() => applySuggestion(suggestion)}
              className="text-xs"
            >
              {suggestion}
            </Button>
          ))}
        </div>
      )}

      <Collapsible open={showFilters} onOpenChange={setShowFilters}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-between mb-4">
            <span>Advanced Filters</span>
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="space-y-6">
          <div>
            <Label>Location</Label>
            <Select value={filters.location} onValueChange={(value) => setFilters({ ...filters, location: value })}>
              <SelectTrigger className="bg-surface">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LOCATIONS.map((loc) => (
                  <SelectItem key={loc} value={loc}>{loc}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Experience (years): {filters.experience[0]} - {filters.experience[1]}</Label>
            <Slider
              value={filters.experience}
              onValueChange={(value) => setFilters({ ...filters, experience: value })}
              min={0}
              max={10}
              step={1}
              className="mt-2"
            />
          </div>

          <div>
            <Label>Salary Range (k$): {filters.salary[0]} - {filters.salary[1]}</Label>
            <Slider
              value={filters.salary}
              onValueChange={(value) => setFilters({ ...filters, salary: value })}
              min={50}
              max={200}
              step={10}
              className="mt-2"
            />
          </div>

          <div>
            <Label>Boolean Skills Query</Label>
            <div className="flex gap-2 mb-2 mt-2">
              <Select 
                value={filters.booleanOperator} 
                onValueChange={(value: "AND" | "OR") => setFilters({ ...filters, booleanOperator: value })}
              >
                <SelectTrigger className="w-24 bg-surface">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="AND">AND</SelectItem>
                  <SelectItem value="OR">OR</SelectItem>
                </SelectContent>
              </Select>
              <Select value={skillInput} onValueChange={(value) => addSkill(value)}>
                <SelectTrigger className="flex-1 bg-surface">
                  <SelectValue placeholder="Select skill..." />
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
                disabled={!skillInput}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {filters.skills.map((skill, index) => (
                <Badge key={skill} variant="secondary" className="gap-1">
                  {index > 0 && (
                    <span className="text-xs text-primary mr-1">{filters.booleanOperator}</span>
                  )}
                  {skill}
                  <X
                    className="w-3 h-3 cursor-pointer hover:text-destructive"
                    onClick={() => removeSkill(skill)}
                  />
                </Badge>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="remote">Remote Only</Label>
            <Switch
              id="remote"
              checked={filters.remote}
              onCheckedChange={(checked) => setFilters({ ...filters, remote: checked })}
            />
          </div>

          <div className="flex gap-2">
            <Button 
              onClick={() => onSearch(query, filters)} 
              className="flex-1 bg-gradient-to-r from-primary to-accent"
            >
              Apply Filters
            </Button>
            <Button onClick={handleReset} variant="outline">
              Reset
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
