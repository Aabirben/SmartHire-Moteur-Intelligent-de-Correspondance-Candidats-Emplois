import { Card } from "@/components/ui/card";
import { TrendingUp, CheckCircle } from "lucide-react";

interface LevelDetectionCardProps {
  level: string;
  confidence: number;
  reasons: string[];
}

export function LevelDetectionCard({ level, confidence, reasons }: LevelDetectionCardProps) {
  return (
    <Card className="glass-strong p-6 hover:glow-accent transition-all duration-300">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
          <TrendingUp className="w-6 h-6" />
        </div>
        <div>
          <h4 className="font-semibold text-lg">{level} Level</h4>
          <p className="text-sm text-muted-foreground">Auto-detected</p>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Confidence</span>
          <span className="text-sm font-bold text-accent">{confidence}%</span>
        </div>
        <div className="relative h-2 bg-surface rounded-full overflow-hidden">
          <div
            className="absolute h-full bg-gradient-to-r from-primary to-accent transition-all duration-1000"
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      <div className="space-y-2">
        <h5 className="text-sm font-semibold">Detection Factors:</h5>
        <ul className="space-y-2">
          {reasons.map((reason, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
              <CheckCircle className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}
