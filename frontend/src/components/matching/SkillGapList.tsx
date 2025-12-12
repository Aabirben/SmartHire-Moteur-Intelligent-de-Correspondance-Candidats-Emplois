import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowUp, Lightbulb } from "lucide-react";
import { toast } from "sonner";

interface SkillGap {
  name: string;
  requiredLevel: number;
  currentLevel: number;
  impactPercent: number;
  suggestions: string[];
}

interface SkillGapListProps {
  missingSkills: SkillGap[];
}

export function SkillGapList({ missingSkills }: SkillGapListProps) {
  if (!missingSkills || missingSkills.length === 0) {
    return null;
  }

  const handleGeneratePlan = () => {
    toast.success("Plan de formation généré! Consultez vos emails.");
  };

  return (
    <Card className="glass-strong p-6">
      <h3 className="text-xl font-bold mb-6 text-gradient">Compétences à Développer</h3>
      
      <div className="space-y-4">
        {missingSkills.map((skill, index) => (
          <Card key={index} className="glass-strong p-4 hover:scale-[1.02] hover:glow-primary transition-all duration-300">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-semibold flex items-center gap-2">
                  {skill.name}
                  <span className="text-xs text-destructive">
                    -{skill.impactPercent}% impact
                  </span>
                </h4>
                <div className="flex items-center gap-4 mt-2 text-sm">
                  <span className="text-muted-foreground">
                    Requis: {skill.requiredLevel}%
                  </span>
                  <span className="text-accent">
                    Actuel: {skill.currentLevel}%
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

            
          </Card>
        ))}
      </div>

      
    </Card>
  );
}