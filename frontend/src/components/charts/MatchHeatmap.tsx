import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface FitCriterion {
  name: string;
  required: string;
  candidate: string;
  matchPercent: number;
}

interface MatchHeatmapProps {
  fitCriteria: FitCriterion[];
  recommendation: string;
}

export function MatchHeatmap({ fitCriteria, recommendation }: MatchHeatmapProps) {
  const getMatchColor = (percent: number) => {
    if (percent >= 80) return "bg-accent/20 text-accent border-accent";
    if (percent >= 60) return "bg-primary/20 text-primary border-primary";
    return "bg-destructive/20 text-destructive border-destructive";
  };

  return (
    <Card className="glass-strong p-6">
      <h3 className="text-xl font-bold mb-6 text-gradient">Analyse d'Adéquation</h3>
      
      <div className="space-y-3">
        {fitCriteria.map((item, index) => (
          <div 
            key={index}
            className="flex items-center justify-between p-4 glass-strong rounded-lg hover:scale-[1.01] transition-all"
          >
            <div className="flex-1">
              <div className="font-semibold mb-1">{item.name}</div>
              <div className="text-sm text-muted-foreground">
                <span className="text-primary">Requis:</span> {item.required} 
                <span className="mx-2">•</span>
                <span className="text-accent">Candidat:</span> {item.candidate}
              </div>
            </div>
            <Badge className={getMatchColor(item.matchPercent)}>
              {item.matchPercent}%
            </Badge>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 glass-strong rounded-lg border-l-4 border-accent">
        <h4 className="font-semibold mb-2 flex items-center gap-2">
          <span className="text-accent">●</span>
          Recommandation
        </h4>
        <p className="text-sm text-muted-foreground">{recommendation}</p>
      </div>
    </Card>
  );
}