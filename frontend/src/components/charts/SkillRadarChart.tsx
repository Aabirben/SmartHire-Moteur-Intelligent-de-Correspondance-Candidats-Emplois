import { Card } from "@/components/ui/card";
import { 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  ResponsiveContainer,
  Legend,
  Tooltip
} from "recharts";
import { SkillData } from "@/types";

interface SkillRadarChartProps {
  skillsData: SkillData[];
  showLegend?: boolean;
}

export function SkillRadarChart({ skillsData, showLegend = true }: SkillRadarChartProps) {
  return (
    <Card className="glass-strong p-6">
      <h3 className="text-xl font-bold mb-6 text-gradient">Skill Comparison Radar</h3>
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={skillsData}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis 
            dataKey="skill" 
            tick={{ fill: 'hsl(var(--foreground))', fontSize: 12 }}
          />
          <PolarRadiusAxis 
            angle={90} 
            domain={[0, 100]}
            tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
          />
          <Radar
            name="Required"
            dataKey="required"
            stroke="hsl(var(--primary))"
            fill="hsl(var(--primary))"
            fillOpacity={0.3}
            className="glow-primary"
          />
          <Radar
            name="Your Level"
            dataKey="user"
            stroke="hsl(var(--accent))"
            fill="hsl(var(--accent))"
            fillOpacity={0.5}
            className="glow-accent"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--surface))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem',
              backdropFilter: 'blur(30px)',
            }}
            labelStyle={{ color: 'hsl(var(--foreground))' }}
          />
          {showLegend && (
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="circle"
            />
          )}
        </RadarChart>
      </ResponsiveContainer>
    </Card>
  );
}
