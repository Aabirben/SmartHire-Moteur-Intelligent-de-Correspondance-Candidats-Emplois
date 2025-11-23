import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FitCriterion } from "@/types";

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
      <h3 className="text-xl font-bold mb-6 text-gradient">Candidate Fit Analysis</h3>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-3 px-4 font-semibold">Criterion</th>
              <th className="text-left py-3 px-4 font-semibold">Required</th>
              <th className="text-left py-3 px-4 font-semibold">Candidate</th>
              <th className="text-right py-3 px-4 font-semibold">Match</th>
            </tr>
          </thead>
          <tbody>
            {fitCriteria.map((item, index) => {
              const Icon = item.icon;
              return (
                <tr 
                  key={index} 
                  className="border-b border-border/50 hover:bg-surface/50 transition-colors"
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-primary" />
                      <span className="font-medium">{item.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-muted-foreground">{item.required}</td>
                  <td className="py-3 px-4">{item.candidate}</td>
                  <td className="py-3 px-4 text-right">
                    <Badge className={getMatchColor(item.matchPercent)}>
                      {item.matchPercent}%
                    </Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 p-4 glass-strong rounded-lg border-l-4 border-accent">
        <h4 className="font-semibold mb-2 flex items-center gap-2">
          <span className="text-accent">●</span>
          Recommendation
        </h4>
        <p className="text-sm text-muted-foreground">{recommendation}</p>
      </div>
    </Card>
  );
}
