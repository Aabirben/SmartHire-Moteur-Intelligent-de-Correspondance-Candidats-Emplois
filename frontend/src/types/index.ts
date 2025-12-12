import { LucideIcon } from "lucide-react";

export interface User {
  id: string;
  email: string;
  name: string;
  role: "candidate" | "recruiter";
  cvUploaded?: boolean;
  company?: string;
}

export interface SkillData {
  skill: string;
  required: number;
  user: number;
  candidateSkills: string[];
  requiredSkills: string[];
  matchedSkills: string[];
  missingSkills: string[];
}

export interface ScoreBreakdown {
  category: string;
  icon: LucideIcon;
  score: number;
  contribution: number;
  detail: string;
  skills: number;
  experience: number;
  location: number;
  level: number;
}

export interface SkillGap {
  name: string;
  requiredLevel: number;
  currentLevel: number;
  impactPercent: number;
  suggestions: string[];
}

export interface FitCriterion {
  name: string;
  icon: LucideIcon;
  required: string;
  candidate: string;
  matchPercent: number;
  criteria: string;
  value: string;
  status: 'good' | 'warning' | 'critical';
}

export interface ScoreBreakdownItem {
  category: string;
  score: number;
  contribution: number;
  icon: React.ComponentType<{ className?: string }>;
  detail: string;
}

export interface FitCriterionItem {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  required: string;
  candidate: string;
  matchPercent: number;
}

export interface SkillDataItem {
  skill: string;
  required: number;
  user: number;
}

// Types pour les détails offres
export interface JobMatchAnalysis {
  totalScore: number;
  scoreBreakdown: {
    skills: number;
    experience: number;
    location: number;
    description: number;
  };
  skillsData: {
    candidateSkills: string[];
    requiredSkills: string[];
    matchedSkills: string[];
    missingSkills: string[];
  };
  missingSkills: string[];
  strengths: string[];
  weaknesses: string[];
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  salary: { min: number; max: number };
  experience: number;
  skills: string[];
  description: string;
  posted: string;
  matchScore?: number;
}

export interface Candidate {
  id: string;
  name: string;
  email: string;
  title: string;
  location: string;
  experience: number;
  skills: string[];
  level: string;
  cvSummary: string;
  matchScore?: number;
}

export interface Message {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: Date;
  read: boolean;
}

export interface Conversation {
  id: string;
  participantId: string;
  participantName: string;
  participantRole: "candidate" | "recruiter";
  lastMessage: string;
  lastMessageTime: Date;
  unreadCount: number;
  jobTitle?: string;
}

export interface Application {
  id: string;
  jobId: string;
  jobTitle: string;
  company: string;
  appliedDate: Date;
  status: "pending" | "reviewing" | "interview" | "accepted" | "rejected";
  matchScore: number;
}

export interface MatchResult {
  skillsData: SkillData[];
  scoreBreakdown: ScoreBreakdown[];
  totalScore: number;
  missingSkills: SkillGap[];
  fitCriteria: FitCriterion[];
  level: string;
  confidence: number;
  reasons: string[];
  recommendation: string;
}

// CORRECTION : Interface SearchFilters sans salary
export interface SearchFilters {
  location: string;
  experience: [number, number];
  skills: string[];
  booleanOperator: "AND" | "OR";
  remote: boolean;
}

export interface SearchState {
  query: string;
  filters: SearchFilters;
  mode: "auto" | "boolean" | "vectoriel" | "hybrid";
  isLoading: boolean;
}

// Interface pour gérer l'état global de recherche
export interface SearchContextType {
  searchState: SearchState;
  setSearchQuery: (query: string) => void;
  setSearchFilters: (filters: SearchFilters) => void;
  setSearchMode: (mode: "auto" | "boolean" | "vectoriel" | "hybrid") => void;
  executeSearch: () => Promise<void>;
  resetSearch: () => void;
}

// Fonction utilitaire pour créer des filtres par défaut
export const createDefaultSearchFilters = (): SearchFilters => ({
  location: "Any",
  experience: [0, 10],
  skills: [],
  booleanOperator: "AND",
  remote: false
});