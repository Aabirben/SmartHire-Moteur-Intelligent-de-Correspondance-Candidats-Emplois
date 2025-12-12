import { Card } from "@/components/ui/card";

interface ScoreBreakdownItem {
  category: string;
  score: number;
  contribution: number;
  detail: string;
}

interface ExplainableScoreBreakdownProps {
  scoreBreakdown: ScoreBreakdownItem[];
  totalScore: number;
}

export function ExplainableScoreBreakdown({ scoreBreakdown, totalScore }: ExplainableScoreBreakdownProps) {
  return (
    <Card className="glass-strong p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gradient">Détail du Score</h3>
        <div className="text-4xl font-bold text-gradient animate-pulse-glow">
          {totalScore}%
        </div>
      </div>

      <div className="space-y-4">
        {scoreBreakdown.map((item, index) => (
          <div key={index} className="glass-strong rounded-lg p-4 hover:scale-[1.02] transition-all duration-300">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="font-semibold">{item.category}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">
                  {item.contribution}% poids
                </span>
                <span className="font-bold text-accent">{item.score}%</span>
              </div>
            </div>

            <div className="relative h-2 bg-surface rounded-full overflow-hidden mb-2">
              <div
                className="absolute h-full bg-gradient-to-r from-primary to-accent transition-all duration-1000 ease-out"
                style={{ width: `${item.score}%` }}
              />
            </div>
            
            <p className="text-sm text-muted-foreground mt-2">{item.detail}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}