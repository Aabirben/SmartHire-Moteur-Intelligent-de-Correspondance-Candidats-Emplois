import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { X, Plus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Job } from "@/types";

interface JobPostFormProps {
  onJobPosted: (job: Job) => void;
}

export function JobPostForm({ onJobPosted }: JobPostFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    company: "",
    location: "",
    remote: false,
    salaryMin: "",
    salaryMax: "",
    experience: "",
    description: "",
    skills: [] as string[],
  });
  const [skillInput, setSkillInput] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateField = (name: string, value: any): string => {
    switch (name) {
      case "title":
        return value.length < 5 ? "Title must be at least 5 characters" : "";
      case "description":
        return value.length < 50 ? "Description must be at least 50 characters" : "";
      case "skills":
        return value.length < 3 ? "Please add at least 3 skills" : "";
      case "salaryMin":
      case "salaryMax":
        return !value || isNaN(Number(value)) ? "Please enter a valid number" : "";
      case "experience":
        return !value || isNaN(Number(value)) ? "Please enter a valid number" : "";
      default:
        return !value ? "This field is required" : "";
    }
  };

  const handleChange = (name: string, value: any) => {
    setFormData({ ...formData, [name]: value });
    const error = validateField(name, value);
    setErrors({ ...errors, [name]: error });
  };

  const addSkill = () => {
    if (skillInput && !formData.skills.includes(skillInput)) {
      const newSkills = [...formData.skills, skillInput];
      handleChange("skills", newSkills);
      setSkillInput("");
    }
  };

  const removeSkill = (skill: string) => {
    const newSkills = formData.skills.filter(s => s !== skill);
    handleChange("skills", newSkills);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const newErrors: Record<string, string> = {};
    Object.keys(formData).forEach((key) => {
      const error = validateField(key, formData[key as keyof typeof formData]);
      if (error) newErrors[key] = error;
    });

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      toast.error("Please fill in all fields correctly");
      return;
    }

    setIsSubmitting(true);
    await new Promise(resolve => setTimeout(resolve, 1000));

    const newJob: Job = {
      id: `job-${Date.now()}`,
      title: formData.title,
      company: formData.company,
      location: formData.location,
      remote: formData.remote,
      salary: { 
        min: Number(formData.salaryMin) * 1000, 
        max: Number(formData.salaryMax) * 1000 
      },
      experience: Number(formData.experience),
      skills: formData.skills,
      description: formData.description,
      posted: new Date().toISOString().split('T')[0],
    };

    onJobPosted(newJob);
    setIsSubmitting(false);
    toast.success("Job posted successfully!");

    // Reset form
    setFormData({
      title: "",
      company: "",
      location: "",
      remote: false,
      salaryMin: "",
      salaryMax: "",
      experience: "",
      description: "",
      skills: [],
    });
    setErrors({});
  };

  return (
    <Card className="glass-strong p-6">
      <h2 className="text-2xl font-bold mb-6 text-gradient">Post New Job</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="title">Job Title *</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => handleChange("title", e.target.value)}
            placeholder="e.g., Senior Full Stack Developer"
            className={`bg-surface ${errors.title ? 'border-destructive' : ''}`}
          />
          {errors.title && <p className="text-xs text-destructive mt-1">{errors.title}</p>}
        </div>

        <div>
          <Label htmlFor="company">Company *</Label>
          <Input
            id="company"
            value={formData.company}
            onChange={(e) => handleChange("company", e.target.value)}
            placeholder="Your company name"
            className={`bg-surface ${errors.company ? 'border-destructive' : ''}`}
          />
          {errors.company && <p className="text-xs text-destructive mt-1">{errors.company}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="location">Location *</Label>
            <Select value={formData.location} onValueChange={(value) => handleChange("location", value)}>
              <SelectTrigger className={`bg-surface ${errors.location ? 'border-destructive' : ''}`}>
                <SelectValue placeholder="Select location" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="San Francisco, CA">San Francisco, CA</SelectItem>
                <SelectItem value="New York, NY">New York, NY</SelectItem>
                <SelectItem value="Austin, TX">Austin, TX</SelectItem>
                <SelectItem value="Seattle, WA">Seattle, WA</SelectItem>
                <SelectItem value="Remote">Remote</SelectItem>
              </SelectContent>
            </Select>
            {errors.location && <p className="text-xs text-destructive mt-1">{errors.location}</p>}
          </div>

          <div>
            <Label htmlFor="experience">Experience (years) *</Label>
            <Input
              id="experience"
              type="number"
              value={formData.experience}
              onChange={(e) => handleChange("experience", e.target.value)}
              placeholder="e.g., 5"
              className={`bg-surface ${errors.experience ? 'border-destructive' : ''}`}
            />
            {errors.experience && <p className="text-xs text-destructive mt-1">{errors.experience}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="salaryMin">Min Salary (k$) *</Label>
            <Input
              id="salaryMin"
              type="number"
              value={formData.salaryMin}
              onChange={(e) => handleChange("salaryMin", e.target.value)}
              placeholder="e.g., 120"
              className={`bg-surface ${errors.salaryMin ? 'border-destructive' : ''}`}
            />
            {errors.salaryMin && <p className="text-xs text-destructive mt-1">{errors.salaryMin}</p>}
          </div>

          <div>
            <Label htmlFor="salaryMax">Max Salary (k$) *</Label>
            <Input
              id="salaryMax"
              type="number"
              value={formData.salaryMax}
              onChange={(e) => handleChange("salaryMax", e.target.value)}
              placeholder="e.g., 180"
              className={`bg-surface ${errors.salaryMax ? 'border-destructive' : ''}`}
            />
            {errors.salaryMax && <p className="text-xs text-destructive mt-1">{errors.salaryMax}</p>}
          </div>
        </div>

        <div>
          <Label htmlFor="description">Job Description *</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => handleChange("description", e.target.value)}
            placeholder="Describe the role, responsibilities, and requirements..."
            rows={4}
            className={`bg-surface ${errors.description ? 'border-destructive' : ''}`}
          />
          {errors.description && <p className="text-xs text-destructive mt-1">{errors.description}</p>}
        </div>

        <div>
          <Label>Required Skills * (at least 3)</Label>
          <div className="flex gap-2 mt-2">
            <Input
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
              placeholder="Add a skill..."
              className="bg-surface"
            />
            <Button type="button" onClick={addSkill} size="icon" variant="outline">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {formData.skills.map((skill) => (
              <Badge key={skill} variant="secondary" className="gap-1">
                {skill}
                <X
                  className="w-3 h-3 cursor-pointer hover:text-destructive"
                  onClick={() => removeSkill(skill)}
                />
              </Badge>
            ))}
          </div>
          {errors.skills && <p className="text-xs text-destructive mt-1">{errors.skills}</p>}
        </div>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-gradient-to-r from-primary to-accent hover:scale-[1.02] transition-all"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Posting...
            </>
          ) : (
            "Post Job"
          )}
        </Button>
      </form>
    </Card>
  );
}
