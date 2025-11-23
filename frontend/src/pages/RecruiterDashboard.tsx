import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdvancedSearchFilters } from "@/components/search/AdvancedSearchFilters";
import { JobPostForm } from "@/components/recruiter/JobPostForm";
import { LogOut, User, MessageSquare, Plus } from "lucide-react";
import { getStoredUser, clearStoredUser, mockCandidates, getStoredJobs, setStoredJobs } from "@/utils/mockData";
import { Candidate, SearchFilters, Job } from "@/types";
import { toast } from "sonner";

export default function RecruiterDashboard() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const [candidates, setCandidates] = useState<Candidate[]>(mockCandidates);
  const [filteredCandidates, setFilteredCandidates] = useState<Candidate[]>(mockCandidates);
  const [jobs, setJobs] = useState<Job[]>(getStoredJobs());

  useEffect(() => {
    if (!user || user.role !== "recruiter") {
      navigate("/");
    }
  }, [user, navigate]);

  const handleLogout = () => {
    clearStoredUser();
    toast.success("Logged out successfully");
    navigate("/");
  };

  const handleSearch = (query: string, filters: SearchFilters) => {
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

  const handleJobPosted = (newJob: Job) => {
    const updatedJobs = [...jobs, newJob];
    setJobs(updatedJobs);
    setStoredJobs(updatedJobs);
  };

  return (
    <div className="min-h-screen mesh-gradient">
      <header className="border-b border-border glass-strong">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gradient">Recruiter Dashboard</h1>
            <p className="text-sm text-muted-foreground">Welcome back, {user?.name}!</p>
          </div>
          <div className="flex items-center gap-4">
            <Button onClick={() => navigate("/messages/conv-1")} variant="outline" className="gap-2">
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
                    {candidate.matchScore && (
                      <Badge className="mb-3 bg-gradient-to-r from-primary to-accent">
                        {candidate.matchScore}% Match
                      </Badge>
                    )}
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
              
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {jobs.map((job) => (
                  <Card key={job.id} className="glass-strong p-6">
                    <h3 className="font-bold text-lg mb-2">{job.title}</h3>
                    <p className="text-muted-foreground mb-4">{job.company}</p>
                    
                    <div className="space-y-2 text-sm mb-4">
                      <div>{job.location}</div>
                      <div>${job.salary.min / 1000}k - ${job.salary.max / 1000}k</div>
                      <div>{job.experience}+ years exp</div>
                    </div>

                    <Button variant="outline" className="w-full">
                      View Applicants (0)
                    </Button>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
