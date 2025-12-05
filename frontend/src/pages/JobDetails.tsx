import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkillRadarChart } from "@/components/charts/SkillRadarChart";
import { ExplainableScoreBreakdown } from "@/components/charts/ExplainableScoreBreakdown";
import { SkillGapList } from "@/components/matching/SkillGapList";
import { ArrowLeft, Briefcase, MapPin, DollarSign, Clock } from "lucide-react";
import { mockJobs, mockMatchResult } from "@/utils/mockData";
import { toast } from "sonner";

export default function JobDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const job = mockJobs.find(j => j.id === id);

  if (!job) {
    return <div>Job not found</div>;
  }

  const handleApply = () => {
    toast.success("Application submitted successfully!");
    navigate("/candidate/dashboard");
  };

  return (
    <div className="min-h-screen mesh-gradient">
      <header className="border-b border-border glass-strong">
        <div className="container mx-auto px-6 py-4">
          <Button onClick={() => navigate("/candidate/dashboard")} variant="ghost" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Jobs
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-6xl">
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="glass-strong p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h1 className="text-3xl font-bold mb-2 text-gradient">{job.title}</h1>
                  <p className="text-xl text-muted-foreground">{job.company}</p>
                </div>
                <div className="text-5xl font-bold text-gradient animate-pulse-glow">
                  {mockMatchResult.totalScore}%
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-primary" />
                  <span>{job.location}</span>
                  {job.remote && <Badge variant="outline">Remote</Badge>}
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-primary" />
                  <span>${job.salary.min / 1000}k - ${job.salary.max / 1000}k</span>
                </div>
                <div className="flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-primary" />
                  <span>{job.experience}+ years experience</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  <span>Posted {job.posted}</span>
                </div>
              </div>

              <div className="mb-6">
                <h3 className="font-semibold mb-3">Required Skills:</h3>
                <div className="flex flex-wrap gap-2">
                  {job.skills.map((skill) => (
                    <Badge key={skill} className="bg-gradient-to-r from-primary to-accent">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-3">Job Description:</h3>
                <p className="text-muted-foreground">{job.description}</p>
              </div>
            </Card>

            <ExplainableScoreBreakdown 
              scoreBreakdown={mockMatchResult.scoreBreakdown}
              totalScore={mockMatchResult.totalScore}
            />

            <SkillRadarChart skillsData={mockMatchResult.skillsData} />

            <SkillGapList missingSkills={mockMatchResult.missingSkills} />
          </div>

          <div className="space-y-6">
            <Card className="glass-strong p-6 sticky top-6">
              <h3 className="font-bold text-lg mb-4">Ready to apply?</h3>
              <p className="text-sm text-muted-foreground mb-6">
                Your profile matches {mockMatchResult.totalScore}% of the requirements for this position.
              </p>
              <Button 
                onClick={handleApply}
                className="w-full bg-gradient-to-r from-primary to-accent hover:scale-[1.02] transition-all"
              >
                Apply Now
              </Button>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
