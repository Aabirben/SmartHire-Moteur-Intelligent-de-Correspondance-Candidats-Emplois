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
import { useAuth } from "@/hooks/useAuth";

export default function Auth() {
  const navigate = useNavigate();
  const { login: authLogin, register: authRegister } = useAuth();
  const [role, setRole] = useState<"candidat" | "recruteur">("candidat");
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [signupData, setSignupData] = useState({ 
    nom: "", 
    prenom: "", 
    email: "", 
    password: "", 
    entreprise: "", 
    telephone: "" 
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!loginData.email) newErrors.email = "Email is required";
    else if (!validateEmail(loginData.email)) newErrors.email = "Invalid email format";
    if (!loginData.password) newErrors.password = "Password is required";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);
    try {
      const result = await authLogin(loginData.email, loginData.password);
      
      if (result.success) {
        // ✅ VÉRIFICATION DU RÔLE - EMPÊCHE LA CONNEXION AVEC MAUVAIS BOUTON
        if (result.user?.user_type !== role) {
          toast.error(`Wrong account type selected`, {
            description: `You clicked "${role === 'candidat' ? "I'm a Candidate" : "I'm a Recruiter"}" but this account is a ${result.user?.user_type}.`,
            action: {
              label: `Switch to ${result.user?.user_type === 'candidat' ? 'Candidate' : 'Recruiter'}`,
              onClick: () => {
                setRole(result.user?.user_type === 'candidat' ? 'candidat' : 'recruteur');
                // Réessayer automatiquement
                setTimeout(() => {
                  handleLogin(e);
                }, 100);
              }
            },
            duration: 5000,
          });
          setIsLoading(false);
          return;
        }
        
        toast.success("Login successful!");
        navigate(result.user?.user_type === "candidat" ? "/candidate/dashboard" : "/recruiter/dashboard");
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!signupData.nom) newErrors.nom = "Last name is required";
    if (!signupData.prenom) newErrors.prenom = "First name is required";
    if (!signupData.email) newErrors.email = "Email is required";
    else if (!validateEmail(signupData.email)) newErrors.email = "Invalid email format";
    if (!signupData.password) newErrors.password = "Password is required";
    else if (signupData.password.length < 8) newErrors.password = "Password must be at least 8 characters";

    if (role === "recruteur" && !signupData.entreprise) {
      newErrors.entreprise = "Company name is required for recruiters";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);
    try {
      const result = await authRegister({
        email: signupData.email,
        password: signupData.password,
        user_type: role,
        nom: signupData.nom,
        prenom: signupData.prenom,
        entreprise: signupData.entreprise,
        telephone: signupData.telephone
      });

      if (result.success) {
        toast.success("Account created successfully!");
        navigate(role === "candidat" ? "/candidate/dashboard" : "/recruiter/dashboard");
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Registration failed");
    } finally {
      setIsLoading(false);
    }
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
            variant={role === "candidat" ? "default" : "outline"}
            className="flex-1 py-2 justify-center cursor-pointer transition-all hover:scale-[1.02]"
            onClick={() => setRole("candidat")}
          >
            I'm a Candidate
          </Badge>
          <Badge
            variant={role === "recruteur" ? "default" : "outline"}
            className="flex-1 py-2 justify-center cursor-pointer transition-all hover:scale-[1.02]"
            onClick={() => setRole("recruteur")}
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
                  disabled={isLoading}
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
                  disabled={isLoading}
                />
                {errors.password && <p className="text-xs text-destructive mt-1">{errors.password}</p>}
              </div>

              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-primary to-accent"
                disabled={isLoading}
              >
                {isLoading ? "Logging in..." : `Login as ${role === "candidat" ? "Candidate" : "Recruiter"}`}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="signup">
            <form onSubmit={handleSignup} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="signup-nom">Last Name *</Label>
                  <Input
                    id="signup-nom"
                    value={signupData.nom}
                    onChange={(e) => {
                      setSignupData({ ...signupData, nom: e.target.value });
                      setErrors({ ...errors, nom: "" });
                    }}
                    className={`bg-surface ${errors.nom ? 'border-destructive' : ''}`}
                    disabled={isLoading}
                  />
                  {errors.nom && <p className="text-xs text-destructive mt-1">{errors.nom}</p>}
                </div>

                <div>
                  <Label htmlFor="signup-prenom">First Name *</Label>
                  <Input
                    id="signup-prenom"
                    value={signupData.prenom}
                    onChange={(e) => {
                      setSignupData({ ...signupData, prenom: e.target.value });
                      setErrors({ ...errors, prenom: "" });
                    }}
                    className={`bg-surface ${errors.prenom ? 'border-destructive' : ''}`}
                    disabled={isLoading}
                  />
                  {errors.prenom && <p className="text-xs text-destructive mt-1">{errors.prenom}</p>}
                </div>
              </div>

              <div>
                <Label htmlFor="signup-email">Email *</Label>
                <Input
                  id="signup-email"
                  type="email"
                  value={signupData.email}
                  onChange={(e) => {
                    setSignupData({ ...signupData, email: e.target.value });
                    setErrors({ ...errors, email: "" });
                  }}
                  className={`bg-surface ${errors.email ? 'border-destructive' : ''}`}
                  disabled={isLoading}
                />
                {errors.email && <p className="text-xs text-destructive mt-1">{errors.email}</p>}
              </div>

              <div>
                <Label htmlFor="signup-password">Password *</Label>
                <Input
                  id="signup-password"
                  type="password"
                  value={signupData.password}
                  onChange={(e) => {
                    setSignupData({ ...signupData, password: e.target.value });
                    setErrors({ ...errors, password: "" });
                  }}
                  className={`bg-surface ${errors.password ? 'border-destructive' : ''}`}
                  disabled={isLoading}
                />
                {errors.password && <p className="text-xs text-destructive mt-1">{errors.password}</p>}
              </div>

              {role === "recruteur" && (
                <div>
                  <Label htmlFor="signup-entreprise">Company *</Label>
                  <Input
                    id="signup-entreprise"
                    value={signupData.entreprise}
                    onChange={(e) => {
                      setSignupData({ ...signupData, entreprise: e.target.value });
                      setErrors({ ...errors, entreprise: "" });
                    }}
                    className={`bg-surface ${errors.entreprise ? 'border-destructive' : ''}`}
                    disabled={isLoading}
                  />
                  {errors.entreprise && <p className="text-xs text-destructive mt-1">{errors.entreprise}</p>}
                </div>
              )}

              <div>
                <Label htmlFor="signup-telephone">Phone (optional)</Label>
                <Input
                  id="signup-telephone"
                  type="tel"
                  value={signupData.telephone}
                  onChange={(e) => setSignupData({ ...signupData, telephone: e.target.value })}
                  className="bg-surface"
                  disabled={isLoading}
                />
              </div>

              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-primary to-accent"
                disabled={isLoading}
              >
                {isLoading ? "Creating account..." : `Create ${role === "candidat" ? "Candidate" : "Recruiter"} Account`}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}