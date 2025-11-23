import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowUp, Lightbulb } from "lucide-react";
import { SkillGap } from "@/types";
import { toast } from "sonner";

interface SkillGapListProps {
  missingSkills: SkillGap[];
}

export function SkillGapList({ missingSkills }: SkillGapListProps) {
  if (missingSkills.length === 0) {
    return null;
  }

  const handleGeneratePlan = () => {
    toast.success("Learning plan generated! Check your email for details.");
  };

  return (
    <Card className="glass-strong p-6">
      <h3 className="text-xl font-bold mb-6 text-gradient">Skill Gaps to Close</h3>
      
      <div className="space-y-4">
        {missingSkills.map((skill, index) => (
          <Card key={index} className="glass-strong p-4 hover:scale-[1.02] hover:glow-primary transition-all duration-300">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-semibold flex items-center gap-2">
                  {skill.name}
                  <span className="text-xs text-destructive">
                    -{skill.impactPercent}% impact on match
                  </span>
                </h4>
                <div className="flex items-center gap-4 mt-2 text-sm">
                  <span className="text-muted-foreground">
                    Required: {skill.requiredLevel}%
                  </span>
                  <span className="text-accent">
                    Current: {skill.currentLevel}%
                  </span>
                  <span className="text-destructive flex items-center gap-1">
                    <ArrowUp className="w-3 h-3" />
                    Gap: {skill.requiredLevel - skill.currentLevel}%
                  </span>
                </div>
              </div>
            </div>

            <div className="relative h-2 bg-surface rounded-full overflow-hidden mb-4">
              <div
                className="absolute h-full bg-accent transition-all duration-1000"
                style={{ width: `${skill.currentLevel}%` }}
              />
              <div
                className="absolute h-full border-2 border-primary border-dashed"
                style={{ width: `${skill.requiredLevel}%` }}
              />
            </div>

            <div className="space-y-2">
              <h5 className="text-sm font-semibold flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-accent" />
                Suggestions to improve:
              </h5>
              <ul className="space-y-1 text-sm text-muted-foreground">
                {skill.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        ))}
      </div>

      <Button 
        onClick={handleGeneratePlan}
        className="w-full mt-6 bg-gradient-to-r from-primary to-accent hover:scale-[1.02] transition-all"
      >
        Generate Personalized Learning Plan
      </Button>
    </Card>
  );
}
