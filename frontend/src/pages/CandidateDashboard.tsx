import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AdvancedSearchFilters } from "@/components/search/AdvancedSearchFilters";
import { CVUpload } from "@/components/candidate/CVUpload";
import { LogOut, Briefcase, MessageSquare, Upload } from "lucide-react";
import { getStoredUser, clearStoredUser, mockJobs, getCVUploaded, setCVUploaded } from "@/utils/mockData";
import { Job, SearchFilters } from "@/types";
import { toast } from "sonner";

export default function CandidateDashboard() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const [jobs, setJobs] = useState<Job[]>(mockJobs);
  const [filteredJobs, setFilteredJobs] = useState<Job[]>(mockJobs);
  const [cvUploaded, setCvUploadedState] = useState(getCVUploaded());
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    if (!user || user.role !== "candidate") {
      navigate("/");
    }
  }, [user, navigate]);

  const handleLogout = () => {
    clearStoredUser();
    toast.success("Logged out successfully");
    navigate("/");
  };

  const handleSearch = (query: string, filters: SearchFilters) => {
    let filtered = [...jobs];

    if (query) {
      filtered = filtered.filter(job =>
        job.title.toLowerCase().includes(query.toLowerCase()) ||
        job.company.toLowerCase().includes(query.toLowerCase())
      );
    }

    if (filters.location && filters.location !== "Any") {
      filtered = filtered.filter(job => job.location === filters.location);
    }

    if (filters.experience) {
      filtered = filtered.filter(job =>
        job.experience >= filters.experience[0] && job.experience <= filters.experience[1]
      );
    }

    if (filters.salary) {
      filtered = filtered.filter(job =>
        (job.salary.min / 1000) >= filters.salary[0] && (job.salary.max / 1000) <= filters.salary[1]
      );
    }

    if (filters.skills.length > 0) {
      filtered = filtered.filter(job => {
        if (filters.booleanOperator === "AND") {
          return filters.skills.every(skill => job.skills.includes(skill));
        } else {
          return filters.skills.some(skill => job.skills.includes(skill));
        }
      });
    }

    if (filters.remote) {
      filtered = filtered.filter(job => job.remote);
    }

    setFilteredJobs(filtered);
  };

  const handleCVUploadSuccess = (skills: string[]) => {
    setCvUploadedState(true);
    setCVUploaded(true);
    setShowUpload(false);
    
    // Show personalized matches based on skills
    const matched = jobs.map(job => {
      const matchedSkills = job.skills.filter(s => skills.includes(s)).length;
      const matchScore = Math.round((matchedSkills / job.skills.length) * 100);
      return { ...job, matchScore };
    }).sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0));

    setFilteredJobs(matched);
    toast.success("Found personalized job matches!");
  };

  if (showUpload) {
    return (
      <div className="min-h-screen p-6 mesh-gradient">
        <div className="max-w-2xl mx-auto">
          <Button onClick={() => setShowUpload(false)} variant="ghost" className="mb-4">
            ← Back to Dashboard
          </Button>
          <CVUpload onUploadSuccess={handleCVUploadSuccess} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen mesh-gradient">
      <header className="border-b border-border glass-strong">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gradient">Candidate Dashboard</h1>
            <p className="text-sm text-muted-foreground">Welcome back, {user?.name}!</p>
          </div>
          <div className="flex items-center gap-4">
            {!cvUploaded && (
              <Button onClick={() => setShowUpload(true)} variant="outline" className="gap-2">
                <Upload className="w-4 h-4" />
                Upload CV
              </Button>
            )}
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
        {!cvUploaded && (
          <Card className="glass-strong p-6 mb-6 border-l-4 border-primary">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold mb-2">🚀 Get Better Matches!</h3>
                <p className="text-sm text-muted-foreground">
                  Upload your CV to get personalized job recommendations with AI-powered matching
                </p>
              </div>
              <Button onClick={() => setShowUpload(true)} className="bg-gradient-to-r from-primary to-accent">
                Upload Now
              </Button>
            </div>
          </Card>
        )}

        <AdvancedSearchFilters 
          onSearch={handleSearch} 
          placeholder="Search jobs by title, company, or skills..."
        />

        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">
            {cvUploaded ? "Personalized Matches" : "Available Jobs"} 
            <Badge variant="secondary" className="ml-2">{filteredJobs.length}</Badge>
          </h2>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredJobs.map((job) => (
              <Card 
                key={job.id}
                className="glass-strong p-6 hover:scale-[1.02] hover:glow-primary transition-all cursor-pointer"
                onClick={() => navigate(`/candidate/job/${job.id}`)}
              >
                {job.matchScore && (
                  <Badge className="mb-3 bg-gradient-to-r from-primary to-accent">
                    {job.matchScore}% Match
                  </Badge>
                )}
                <h3 className="font-bold text-lg mb-2">{job.title}</h3>
                <p className="text-muted-foreground mb-4">{job.company}</p>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-primary" />
                    <span>{job.location}</span>
                    {job.remote && <Badge variant="outline">Remote</Badge>}
                  </div>
                  <div className="text-muted-foreground">
                    ${job.salary.min / 1000}k - ${job.salary.max / 1000}k
                  </div>
                  <div className="text-muted-foreground">
                    {job.experience}+ years exp
                  </div>
                </div>

                <div className="flex flex-wrap gap-1 mt-4">
                  {job.skills.slice(0, 3).map((skill) => (
                    <Badge key={skill} variant="secondary" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                  {job.skills.length > 3 && (
                    <Badge variant="secondary" className="text-xs">
                      +{job.skills.length - 3}
                    </Badge>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
