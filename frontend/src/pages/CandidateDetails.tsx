import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { SkillRadarChart } from "@/components/charts/SkillRadarChart";
import { ExplainableScoreBreakdown } from "@/components/charts/ExplainableScoreBreakdown";
import { MatchHeatmap } from "@/components/charts/MatchHeatmap";
import { LevelDetectionCard } from "@/components/matching/LevelDetectionCard";
import { ArrowLeft, User, MapPin, Briefcase, MessageSquare, FileText } from "lucide-react";
import { mockCandidates, mockMatchResult } from "@/utils/mockData";

export default function CandidateDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const candidate = mockCandidates.find(c => c.id === id);

  if (!candidate) {
    return <div>Candidate not found</div>;
  }

  return (
    <div className="min-h-screen mesh-gradient">
      <header className="border-b border-border glass-strong">
        <div className="container mx-auto px-6 py-4">
          <Button onClick={() => navigate("/recruiter/dashboard")} variant="ghost" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-7xl">
        <div className="grid lg:grid-cols-4 gap-6">
          <div className="space-y-6">
            <Card className="glass-strong p-6">
              <div className="flex flex-col items-center text-center mb-6">
                <Avatar className="w-24 h-24 mb-4">
                  <AvatarFallback className="text-2xl bg-gradient-to-br from-primary to-accent">
                    {candidate.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                <h2 className="text-xl font-bold">{candidate.name}</h2>
                <p className="text-muted-foreground">{candidate.title}</p>
                <Badge variant="outline" className="mt-2">{candidate.level}</Badge>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-primary" />
                  <span>{candidate.location}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-primary" />
                  <span>{candidate.experience} years experience</span>
                </div>
              </div>

              <div className="mt-6 space-y-2">
                <Button 
                  onClick={() => navigate(`/messages/${candidate.id}`)}
                  className="w-full bg-gradient-to-r from-primary to-accent gap-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  Send Message
                </Button>
                <Button variant="outline" className="w-full gap-2">
                  <FileText className="w-4 h-4" />
                  View Full CV
                </Button>
              </div>
            </Card>

            <LevelDetectionCard
              level={mockMatchResult.level}
              confidence={mockMatchResult.confidence}
              reasons={mockMatchResult.reasons}
            />
          </div>

          <div className="lg:col-span-3 space-y-6">
            <Card className="glass-strong p-8">
              <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-bold text-gradient">Candidate Match Analysis</h1>
                <div className="text-5xl font-bold text-gradient animate-pulse-glow">
                  {mockMatchResult.totalScore}%
                </div>
              </div>

              <div className="mb-6">
                <h3 className="font-semibold mb-3">Skills:</h3>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills.map((skill) => (
                    <Badge key={skill} className="bg-gradient-to-r from-primary to-accent">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-3">CV Summary:</h3>
                <p className="text-muted-foreground">{candidate.cvSummary}</p>
              </div>
            </Card>

            <ExplainableScoreBreakdown 
              scoreBreakdown={mockMatchResult.scoreBreakdown}
              totalScore={mockMatchResult.totalScore}
            />

            <SkillRadarChart skillsData={mockMatchResult.skillsData} />

            <MatchHeatmap 
              fitCriteria={mockMatchResult.fitCriteria}
              recommendation={mockMatchResult.recommendation}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
