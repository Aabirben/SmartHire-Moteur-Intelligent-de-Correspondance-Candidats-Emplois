import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdvancedSearchFilters } from "@/components/search/AdvancedSearchFilters";
import { JobPostForm } from "@/components/recruiter/JobPostForm";
import { LogOut, User, MessageSquare, Plus } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import { AuthGuard } from "@/components/AuthGuard";
import { jobsApi } from "@/utils/api";
import { Candidate, SearchFilters, Job } from "@/types";

// Mock data temporaire - À remplacer par l'API réelle
const mockCandidates: Candidate[] = [
  {
    id: "cand-1",
    name: "Alex Johnson",
    email: "alex@example.com",
    title: "Full Stack Developer",
    location: "San Francisco, CA",
    experience: 5,
    skills: ["React", "Node.js", "TypeScript", "MongoDB", "AWS"],
    level: "Senior",
    cvSummary: "Experienced full-stack developer...",
    matchScore: 92
  }
];

export default function RecruiterDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [candidates, setCandidates] = useState<Candidate[]>(mockCandidates);
  const [filteredCandidates, setFilteredCandidates] = useState<Candidate[]>(mockCandidates);
  const [jobs, setJobs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const data = await jobsApi.getRecruiterJobs();
      setJobs(data);
    } catch (error) {
      toast.error("Failed to load jobs");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    toast.success("Logged out successfully");
  };

  const handleSearch = (query: string, filters: SearchFilters) => {
    // Temporaire - À intégrer avec l'API
    let filtered = [...candidates];

    if (query) {
      filtered = filtered.filter(cand =>
        cand.name.toLowerCase().includes(query.toLowerCase()) ||
        cand.title.toLowerCase().includes(query.toLowerCase())
      );
    }

    if (filters.location && filters.location !== "Any") {
      filtered = filtered.filter(cand => cand.location === filters.location);
    }

    if (filters.experience) {
      filtered = filtered.filter(cand =>
        cand.experience >= filters.experience[0] && cand.experience <= filters.experience[1]
      );
    }

    if (filters.skills.length > 0) {
      filtered = filtered.filter(cand => {
        if (filters.booleanOperator === "AND") {
          return filters.skills.every(skill => cand.skills.includes(skill));
        } else {
          return filters.skills.some(skill => cand.skills.includes(skill));
        }
      });
    }

    setFilteredCandidates(filtered);
  };

  const handleJobPosted = async (newJob: any) => {
    try {
      const response = await jobsApi.createJob(newJob);
      toast.success("Job posted successfully!");
      fetchJobs(); // Recharger la liste
    } catch (error) {
      toast.error("Failed to post job");
    }
  };

  return (
    <AuthGuard requireAuth requireRole="recruteur">
      <div className="min-h-screen mesh-gradient">
        <header className="border-b border-border glass-strong">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gradient">Recruiter Dashboard</h1>
              <p className="text-sm text-muted-foreground">Welcome back, {user?.prenom}!</p>
            </div>
            <div className="flex items-center gap-4">
              <Button onClick={() => navigate("/messages")} variant="outline" className="gap-2">
                <MessageSquare className="w-4 h-4" />
                Messages
              </Button>
              <Button onClick={handleLogout} variant="ghost" className="gap-2">
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-8">
          <Tabs defaultValue="search" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="search">Search Candidates</TabsTrigger>
              <TabsTrigger value="post">Post Job</TabsTrigger>
              <TabsTrigger value="jobs">My Jobs</TabsTrigger>
            </TabsList>

            <TabsContent value="search" className="space-y-6">
              <AdvancedSearchFilters 
                onSearch={handleSearch} 
                placeholder="Search candidates by name, title, or skills..."
              />

              <div>
                <h2 className="text-xl font-bold mb-4">
                  Candidates
                  <Badge variant="secondary" className="ml-2">{filteredCandidates.length}</Badge>
                </h2>
                
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {filteredCandidates.map((candidate) => (
                    <Card 
                      key={candidate.id}
                      className="glass-strong p-6 hover:scale-[1.02] hover:glow-accent transition-all cursor-pointer"
                      onClick={() => navigate(`/recruiter/candidate/${candidate.id}`)}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                          <User className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="font-bold">{candidate.name}</h3>
                          <p className="text-sm text-muted-foreground">{candidate.title}</p>
                        </div>
                      </div>
                      
                      <div className="space-y-2 text-sm mb-4">
                        <div className="text-muted-foreground">{candidate.location}</div>
                        <div className="text-muted-foreground">{candidate.experience} years exp</div>
                        <Badge variant="outline">{candidate.level}</Badge>
                      </div>

                      <div className="flex flex-wrap gap-1">
                        {candidate.skills.slice(0, 3).map((skill) => (
                          <Badge key={skill} variant="secondary" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                        {candidate.skills.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{candidate.skills.length - 3}
                          </Badge>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="post">
              <JobPostForm onJobPosted={handleJobPosted} />
            </TabsContent>

            <TabsContent value="jobs">
              <div>
                <h2 className="text-xl font-bold mb-4">
                  Published Jobs
                  <Badge variant="secondary" className="ml-2">{jobs.length}</Badge>
                </h2>
                
                {isLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">Loading jobs...</p>
                  </div>
                ) : jobs.length === 0 ? (
                  <Card className="glass-strong p-8 text-center">
                    <p className="text-muted-foreground">No jobs posted yet. Create your first job!</p>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {jobs.map((job) => (
                      <Card key={job.id} className="glass-strong p-6">
                        <h3 className="font-bold text-lg mb-2">{job.titre}</h3>
                        <p className="text-muted-foreground mb-4">{job.entreprise}</p>
                        
                        <div className="space-y-2 text-sm mb-4">
                          <div>{job.localisation}</div>
                          <div>{job.experience_min}+ years exp</div>
                          <Badge variant={job.est_active ? "default" : "outline"}>
                            {job.est_active ? "Active" : "Inactive"}
                          </Badge>
                        </div>

                        <Button variant="outline" className="w-full">
                          View Applicants (0)
                        </Button>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </AuthGuard>
  );
}