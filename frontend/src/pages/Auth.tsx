import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";
import { setStoredUser } from "@/utils/mockData";

export default function Auth() {
  const navigate = useNavigate();
  const [role, setRole] = useState<"candidate" | "recruiter">("candidate");
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [signupData, setSignupData] = useState({ name: "", email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!loginData.email) newErrors.email = "Email is required";
    else if (!validateEmail(loginData.email)) newErrors.email = "Invalid email format";
    if (!loginData.password) newErrors.password = "Password is required";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Mock login validation
    const storedUsers = JSON.parse(localStorage.getItem("smarthire_users") || "[]");
    const user = storedUsers.find((u: any) => u.email === loginData.email && u.password === loginData.password);

    if (!user) {
      toast.error("Invalid credentials");
      return;
    }

    setStoredUser(user);
    toast.success("Login successful!");
    navigate(user.role === "candidate" ? "/candidate/dashboard" : "/recruiter/dashboard");
  };

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!signupData.name) newErrors.name = "Name is required";
    if (!signupData.email) newErrors.email = "Email is required";
    else if (!validateEmail(signupData.email)) newErrors.email = "Invalid email format";
    if (!signupData.password) newErrors.password = "Password is required";
    else if (signupData.password.length < 8) newErrors.password = "Password must be at least 8 characters";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    const user = {
      id: `user-${Date.now()}`,
      ...signupData,
      role
    };

    const storedUsers = JSON.parse(localStorage.getItem("smarthire_users") || "[]");
    storedUsers.push(user);
    localStorage.setItem("smarthire_users", JSON.stringify(storedUsers));
    
    setStoredUser(user);
    toast.success("Account created successfully!");
    navigate(role === "candidate" ? "/candidate/dashboard" : "/recruiter/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 mesh-gradient">
      <Card className="w-full max-w-md glass-strong p-8">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-bold text-gradient">SmartHire</h1>
          </div>
          <p className="text-muted-foreground">AI-Powered Job Matching Platform</p>
        </div>

        <div className="flex gap-2 mb-6">
          <Badge
            variant={role === "candidate" ? "default" : "outline"}
            className="flex-1 py-2 justify-center cursor-pointer transition-all hover:scale-[1.02]"
            onClick={() => setRole("candidate")}
          >
            I'm a Candidate
          </Badge>
          <Badge
            variant={role === "recruiter" ? "default" : "outline"}
            className="flex-1 py-2 justify-center cursor-pointer transition-all hover:scale-[1.02]"
            onClick={() => setRole("recruiter")}
          >
            I'm a Recruiter
          </Badge>
        </div>

        <Tabs defaultValue="login">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="signup">Sign Up</TabsTrigger>
          </TabsList>

          <TabsContent value="login">
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="login-email">Email</Label>
                <Input
                  id="login-email"
                  type="email"
                  value={loginData.email}
                  onChange={(e) => {
                    setLoginData({ ...loginData, email: e.target.value });
                    setErrors({ ...errors, email: "" });
                  }}
                  className={`bg-surface ${errors.email ? 'border-destructive' : ''}`}
                />
                {errors.email && <p className="text-xs text-destructive mt-1">{errors.email}</p>}
              </div>

              <div>
                <Label htmlFor="login-password">Password</Label>
                <Input
                  id="login-password"
                  type="password"
                  value={loginData.password}
                  onChange={(e) => {
                    setLoginData({ ...loginData, password: e.target.value });
                    setErrors({ ...errors, password: "" });
                  }}
                  className={`bg-surface ${errors.password ? 'border-destructive' : ''}`}
                />
                {errors.password && <p className="text-xs text-destructive mt-1">{errors.password}</p>}
              </div>

              <Button type="submit" className="w-full bg-gradient-to-r from-primary to-accent">
                Login as {role === "candidate" ? "Candidate" : "Recruiter"}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="signup">
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <Label htmlFor="signup-name">Full Name</Label>
                <Input
                  id="signup-name"
                  value={signupData.name}
                  onChange={(e) => {
                    setSignupData({ ...signupData, name: e.target.value });
                    setErrors({ ...errors, name: "" });
                  }}
                  className={`bg-surface ${errors.name ? 'border-destructive' : ''}`}
                />
                {errors.name && <p className="text-xs text-destructive mt-1">{errors.name}</p>}
              </div>

              <div>
                <Label htmlFor="signup-email">Email</Label>
                <Input
                  id="signup-email"
                  type="email"
                  value={signupData.email}
                  onChange={(e) => {
                    setSignupData({ ...signupData, email: e.target.value });
                    setErrors({ ...errors, email: "" });
                  }}
                  className={`bg-surface ${errors.email ? 'border-destructive' : ''}`}
                />
                {errors.email && <p className="text-xs text-destructive mt-1">{errors.email}</p>}
              </div>

              <div>
                <Label htmlFor="signup-password">Password</Label>
                <Input
                  id="signup-password"
                  type="password"
                  value={signupData.password}
                  onChange={(e) => {
                    setSignupData({ ...signupData, password: e.target.value });
                    setErrors({ ...errors, password: "" });
                  }}
                  className={`bg-surface ${errors.password ? 'border-destructive' : ''}`}
                />
                {errors.password && <p className="text-xs text-destructive mt-1">{errors.password}</p>}
              </div>

              <Button type="submit" className="w-full bg-gradient-to-r from-primary to-accent">
                Create {role === "candidate" ? "Candidate" : "Recruiter"} Account
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
