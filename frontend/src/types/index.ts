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
}

export interface ScoreBreakdown {
  category: string;
  icon: LucideIcon;
  score: number;
  contribution: number;
  detail: string;
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

export interface SearchFilters {
  location: string;
  experience: number[];
  salary: number[];
  skills: string[];
  booleanOperator: "AND" | "OR";
  remote: boolean;
}
