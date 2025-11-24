import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";
 
interface CVUploadProps {
  onUploadSuccess: (skills: string[]) => void;
}
 
export function CVUpload({ onUploadSuccess }: CVUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
 
  const validateFile = (file: File): boolean => {
    if (file.type !== "application/pdf") {
      toast.error("Please upload a PDF file only");
      return false;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error("File size must be less than 5MB");
      return false;
    }
    return true;
  };
 
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
   
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile);
    }
  }, []);
 
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };
 
  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a PDF file");
      return;
    }
 
    setIsProcessing(true);
   
    // Simulate processing
    await new Promise(resolve => setTimeout(resolve, 2500));
   
    // Mock extracted skills
    const extractedSkills = ["React", "TypeScript", "Node.js", "PostgreSQL", "AWS"];
   
    setIsProcessing(false);
    toast.success("CV uploaded and processed successfully!");
    onUploadSuccess(extractedSkills);
  };
 
  return (
    <Card className="glass-strong p-8">
      <h2 className="text-2xl font-bold mb-6 text-gradient">Upload Your CV</h2>
     
      <div
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
          isDragging ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-border'
        }`}
      >
        {file ? (
          <div className="flex flex-col items-center gap-4">
            <FileText className="w-16 h-16 text-accent" />
            <div>
              <p className="font-semibold">{file.name}</p>
              <p className="text-sm text-muted-foreground">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setFile(null)}
              size="sm"
            >
              Remove
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <Upload className="w-16 h-16 text-muted-foreground" />
            <div>
              <p className="font-semibold mb-2">Drop your CV here or click to browse</p>
              <p className="text-sm text-muted-foreground">PDF only, max 5MB</p>
            </div>
            <label htmlFor="cv-upload">
              <Button variant="outline" asChild>
                <span>Browse Files</span>
              </Button>
            </label>
            <input
              id="cv-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        )}
      </div>
 
      <Button
        onClick={handleUpload}
        disabled={!file || isProcessing}
        className="w-full mt-6 bg-gradient-to-r from-primary to-accent hover:scale-[1.02] transition-all glow-primary"
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Processing CV...
          </>
        ) : (
          "Upload & Analyze"
        )}
      </Button>
    </Card>
  );
}