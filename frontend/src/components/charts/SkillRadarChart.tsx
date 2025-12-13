import { Card } from "@/components/ui/card";

interface SkillData {
  skill: string;
  required: number;
  user: number;
}

interface SkillRadarChartProps {
  skillsData: SkillData[];
}

export function SkillRadarChart({ skillsData }: SkillRadarChartProps) {
  return (
    <Card className="glass-strong p-6">
      <h3 className="text-xl font-bold mb-6 text-gradient">Compétences Techniques</h3>
      <div className="space-y-4">
        {skillsData.map((skill, index) => (
          <div key={index}>
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">{skill.skill}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground">
                  Requis: {skill.required}%
                </span>
                <span className="text-sm font-bold text-accent">
                  Vous: {skill.user}%
                </span>
              </div>
            </div>
            <div className="relative h-3 bg-surface rounded-full overflow-hidden">
              <div
                className="absolute h-full bg-muted-foreground/30"
                style={{ width: `${skill.required}%` }}
              />
              <div
                className="absolute h-full bg-gradient-to-r from-primary to-accent transition-all duration-1000"
                style={{ width: `${skill.user}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}