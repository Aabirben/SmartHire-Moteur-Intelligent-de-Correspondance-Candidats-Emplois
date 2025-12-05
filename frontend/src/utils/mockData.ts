import { 
  Job, 
  Candidate, 
  Conversation, 
  Application, 
  MatchResult,
  Message 
} from "@/types";
import { 
  Code, 
  Lightbulb, 
  Users, 
  Target, 
  TrendingUp,
  MapPin,
  Award,
  Briefcase,
  GraduationCap 
} from "lucide-react";

export const mockJobs: Job[] = [
  {
    id: "job-1",
    title: "Senior Full Stack Developer",
    company: "TechCorp Inc",
    location: "San Francisco, CA",
    remote: true,
    salary: { min: 120000, max: 180000 },
    experience: 5,
    skills: ["React", "Node.js", "TypeScript", "PostgreSQL", "AWS", "Docker"],
    description: "Join our team to build scalable web applications...",
    posted: "2024-01-15",
    matchScore: 92
  },
  {
    id: "job-2",
    title: "Frontend Engineer",
    company: "StartupXYZ",
    location: "New York, NY",
    remote: false,
    salary: { min: 100000, max: 140000 },
    experience: 3,
    skills: ["React", "TypeScript", "CSS", "Jest", "Figma"],
    description: "Build beautiful user interfaces for our platform...",
    posted: "2024-01-18",
    matchScore: 85
  },
  {
    id: "job-3",
    title: "DevOps Engineer",
    company: "CloudScale",
    location: "Austin, TX",
    remote: true,
    salary: { min: 110000, max: 160000 },
    experience: 4,
    skills: ["Kubernetes", "Docker", "AWS", "Terraform", "Python", "CI/CD"],
    description: "Manage and scale our cloud infrastructure...",
    posted: "2024-01-20",
    matchScore: 78
  },
  {
    id: "job-4",
    title: "Machine Learning Engineer",
    company: "AI Innovations",
    location: "Seattle, WA",
    remote: true,
    salary: { min: 140000, max: 200000 },
    experience: 4,
    skills: ["Python", "TensorFlow", "PyTorch", "SQL", "AWS", "MLOps"],
    description: "Develop cutting-edge ML models...",
    posted: "2024-01-22",
    matchScore: 72
  }
];

export const mockCandidates: Candidate[] = [
  {
    id: "cand-1",
    name: "Alex Johnson",
    email: "alex@example.com",
    title: "Full Stack Developer",
    location: "San Francisco, CA",
    experience: 5,
    skills: ["React", "Node.js", "TypeScript", "MongoDB", "AWS"],
    level: "Senior",
    cvSummary: "Experienced full-stack developer with 5+ years building scalable web applications...",
    matchScore: 92
  },
  {
    id: "cand-2",
    name: "Sarah Chen",
    email: "sarah@example.com",
    title: "Frontend Developer",
    location: "New York, NY",
    experience: 3,
    skills: ["React", "TypeScript", "CSS", "Redux", "Jest"],
    level: "Mid-level",
    cvSummary: "Creative frontend developer passionate about user experience...",
    matchScore: 88
  },
  {
    id: "cand-3",
    name: "Michael Brown",
    email: "michael@example.com",
    title: "DevOps Engineer",
    location: "Austin, TX",
    experience: 4,
    skills: ["Docker", "Kubernetes", "AWS", "Python", "Jenkins"],
    level: "Mid-level",
    cvSummary: "DevOps specialist with strong automation and cloud expertise...",
    matchScore: 85
  }
];

export const mockConversations: Conversation[] = [
  {
    id: "conv-1",
    participantId: "cand-1",
    participantName: "Alex Johnson",
    participantRole: "candidate",
    lastMessage: "Thank you for considering my application!",
    lastMessageTime: new Date("2024-01-20T14:30:00"),
    unreadCount: 2,
    jobTitle: "Senior Full Stack Developer"
  },
  {
    id: "conv-2",
    participantId: "rec-1",
    participantName: "Emily Davis",
    participantRole: "recruiter",
    lastMessage: "We'd like to schedule an interview...",
    lastMessageTime: new Date("2024-01-19T10:15:00"),
    unreadCount: 0,
    jobTitle: "Frontend Engineer"
  }
];

export const mockMessages: Record<string, Message[]> = {
  "conv-1": [
    {
      id: "msg-1",
      senderId: "rec-1",
      senderName: "Emily Davis",
      content: "Hi Alex, we reviewed your application and are impressed with your experience!",
      timestamp: new Date("2024-01-20T10:00:00"),
      read: true
    },
    {
      id: "msg-2",
      senderId: "cand-1",
      senderName: "Alex Johnson",
      content: "Thank you for considering my application!",
      timestamp: new Date("2024-01-20T14:30:00"),
      read: false
    }
  ],
  "conv-2": [
    {
      id: "msg-3",
      senderId: "rec-1",
      senderName: "Emily Davis",
      content: "We'd like to schedule an interview...",
      timestamp: new Date("2024-01-19T10:15:00"),
      read: true
    }
  ]
};

export const mockApplications: Application[] = [
  {
    id: "app-1",
    jobId: "job-1",
    jobTitle: "Senior Full Stack Developer",
    company: "TechCorp Inc",
    appliedDate: new Date("2024-01-15"),
    status: "reviewing",
    matchScore: 92
  },
  {
    id: "app-2",
    jobId: "job-2",
    jobTitle: "Frontend Engineer",
    company: "StartupXYZ",
    appliedDate: new Date("2024-01-18"),
    status: "interview",
    matchScore: 85
  }
];

export const mockMatchResult: MatchResult = {
  skillsData: [
    { skill: "React", required: 90, user: 95 },
    { skill: "TypeScript", required: 85, user: 88 },
    { skill: "Node.js", required: 80, user: 75 },
    { skill: "PostgreSQL", required: 70, user: 60 },
    { skill: "AWS", required: 75, user: 70 },
    { skill: "Docker", required: 65, user: 50 }
  ],
  scoreBreakdown: [
    {
      category: "Skills Match",
      icon: Code,
      score: 85,
      contribution: 40,
      detail: "Strong alignment in core technologies. React and TypeScript proficiency excellent. Minor gaps in PostgreSQL and Docker."
    },
    {
      category: "Experience Level",
      icon: TrendingUp,
      score: 90,
      contribution: 25,
      detail: "5 years experience matches requirements perfectly. Demonstrated senior-level capabilities."
    },
    {
      category: "Domain Knowledge",
      icon: Lightbulb,
      score: 88,
      contribution: 20,
      detail: "Strong background in web development and cloud technologies."
    },
    {
      category: "Team Fit",
      icon: Users,
      score: 82,
      contribution: 15,
      detail: "Communication skills and collaborative experience align with team culture."
    }
  ],
  totalScore: 92,
  missingSkills: [
    {
      name: "PostgreSQL",
      requiredLevel: 70,
      currentLevel: 60,
      impactPercent: 8,
      suggestions: [
        "Complete PostgreSQL certification course",
        "Build a project with complex database schema",
        "Study advanced SQL optimization techniques"
      ]
    },
    {
      name: "Docker",
      requiredLevel: 65,
      currentLevel: 50,
      impactPercent: 5,
      suggestions: [
        "Learn container orchestration with Docker Compose",
        "Containerize existing projects",
        "Study Docker best practices and security"
      ]
    }
  ],
  fitCriteria: [
    {
      name: "Location",
      icon: MapPin,
      required: "San Francisco, CA",
      candidate: "San Francisco, CA",
      matchPercent: 100
    },
    {
      name: "Experience",
      icon: Briefcase,
      required: "5+ years",
      candidate: "5 years",
      matchPercent: 100
    },
    {
      name: "Education",
      icon: GraduationCap,
      required: "Bachelor's in CS",
      candidate: "Bachelor's in CS",
      matchPercent: 100
    },
    {
      name: "Certifications",
      icon: Award,
      required: "AWS Certified",
      candidate: "None",
      matchPercent: 50
    },
    {
      name: "Salary Range",
      icon: Target,
      required: "$120k-$180k",
      candidate: "$130k-$160k",
      matchPercent: 90
    }
  ],
  level: "Senior",
  confidence: 92,
  reasons: [
    "5+ years of relevant experience in full-stack development",
    "Strong proficiency in React and TypeScript (95% and 88% respectively)",
    "Proven track record with Node.js and modern web technologies",
    "Experience with cloud platforms (AWS) and containerization"
  ],
  recommendation: "Strong candidate with excellent technical skills and experience level. Minor skill gaps in PostgreSQL and Docker can be addressed through on-the-job learning. Recommended for interview."
};

export const getStoredUser = (): any | null => {
  const userStr = localStorage.getItem("smarthire_user");
  return userStr ? JSON.parse(userStr) : null;
};

export const setStoredUser = (user: any) => {
  localStorage.setItem("smarthire_user", JSON.stringify(user));
};

export const clearStoredUser = () => {
  localStorage.removeItem("smarthire_user");
};

export const getStoredJobs = (): Job[] => {
  const jobsStr = localStorage.getItem("smarthire_jobs");
  return jobsStr ? JSON.parse(jobsStr) : mockJobs;
};

export const setStoredJobs = (jobs: Job[]) => {
  localStorage.setItem("smarthire_jobs", JSON.stringify(jobs));
};

export const getCVUploaded = (): boolean => {
  return localStorage.getItem("smarthire_cv_uploaded") === "true";
};

export const setCVUploaded = (uploaded: boolean) => {
  localStorage.setItem("smarthire_cv_uploaded", uploaded.toString());
};
