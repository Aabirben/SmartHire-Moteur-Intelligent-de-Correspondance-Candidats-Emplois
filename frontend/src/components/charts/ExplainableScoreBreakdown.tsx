import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronUp } from "lucide-react";
import { ScoreBreakdown } from "@/types";

interface ExplainableScoreBreakdownProps {
  scoreBreakdown: ScoreBreakdown[];
  totalScore: number;
}

export function ExplainableScoreBreakdown({ scoreBreakdown, totalScore }: ExplainableScoreBreakdownProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  return (
    <Card className="glass-strong p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gradient">Match Score Breakdown</h3>
        <div className="text-4xl font-bold text-gradient animate-pulse-glow">
          {totalScore}%
        </div>
      </div>

      <div className="space-y-4">
        {scoreBreakdown.map((item, index) => {
          const Icon = item.icon;
          const isExpanded = expandedIndex === index;

          return (
            <Collapsible
              key={item.category}
              open={isExpanded}
              onOpenChange={() => setExpandedIndex(isExpanded ? null : index)}
            >
              <div className="glass-strong rounded-lg p-4 hover:scale-[1.02] transition-all duration-300">
                <CollapsibleTrigger className="w-full">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <Icon className="w-5 h-5 text-primary" />
                      <span className="font-semibold">{item.category}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted-foreground">
                        {item.contribution}% weight
                      </span>
                      <span className="font-bold text-accent">{item.score}%</span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </div>

                  <div className="relative h-2 bg-surface rounded-full overflow-hidden">
                    <div
                      className="absolute h-full bg-gradient-to-r from-primary to-accent transition-all duration-1000 ease-out"
                      style={{ width: `${item.score}%` }}
                    />
                  </div>
                </CollapsibleTrigger>

                <CollapsibleContent className="mt-3 pt-3 border-t border-border">
                  <p className="text-sm text-muted-foreground">{item.detail}</p>
                </CollapsibleContent>
              </div>
            </Collapsible>
          );
        })}
      </div>
    </Card>
  );
}
