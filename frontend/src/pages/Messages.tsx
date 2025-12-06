import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChatInterface } from "@/components/messaging/ChatInterface";
import { ArrowLeft, MessageSquare } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { AuthGuard } from "@/components/AuthGuard";
import { messagingApi } from "@/utils/api";
import { toast } from "sonner";

interface Conversation {
  id: string;
  participant_id: number;
  participant_name: string;
  participant_role: string;
  last_message: string;
  last_message_time: string;
  unread_count: number;
}

export default function Messages() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConv, setSelectedConv] = useState<number | null>(
    conversationId ? parseInt(conversationId) : null
  );
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const data = await messagingApi.getConversations();
      const transformedConversations = data.map((conv: any) => ({
        id: conv.participant_id.toString(),
        participant_id: conv.participant_id,
        participant_name: conv.participant_name,
        participant_role: conv.participant_role,
        last_message: conv.last_message,
        last_message_time: conv.last_message_time,
        unread_count: conv.unread_count
      }));
      
      setConversations(transformedConversations);
      
      // Sélectionner la première conversation si aucune n'est sélectionnée
      if (!selectedConv && transformedConversations.length > 0) {
        setSelectedConv(transformedConversations[0].participant_id);
      }
    } catch (error) {
      toast.error("Failed to load conversations");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = (participantId: number) => {
    setSelectedConv(participantId);
    navigate(`/messages/${participantId}`);
  };

  const getBackUrl = () => {
    if (user?.user_type === 'candidat') {
      return "/candidate/dashboard";
    } else {
      return "/recruiter/dashboard";
    }
  };

  return (
    <AuthGuard requireAuth>
      <div className="min-h-screen mesh-gradient">
        <header className="border-b border-border glass-strong">
          <div className="container mx-auto px-6 py-4">
            <Button 
              onClick={() => navigate(getBackUrl())} 
              variant="ghost" 
              className="gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </Button>
          </div>
        </header>

        <main className="container mx-auto px-6 py-8 max-w-7xl">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading conversations...</p>
            </div>
          ) : (
            <div className="grid lg:grid-cols-4 gap-6">
              <Card className="glass-strong p-4 h-[600px] overflow-y-auto">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-primary" />
                  Conversations
                </h2>
                
                <div className="space-y-2">
                  {conversations.length === 0 ? (
                    <p className="text-muted-foreground text-center py-4">No conversations yet</p>
                  ) : (
                    conversations.map((conv) => (
                      <Card
                        key={conv.id}
                        className={`p-4 cursor-pointer hover:scale-[1.02] transition-all ${
                          selectedConv === conv.participant_id ? 'bg-primary/20 border-primary' : 'glass-strong'
                        }`}
                        onClick={() => handleSelectConversation(conv.participant_id)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold">{conv.participant_name}</h3>
                          {conv.unread_count > 0 && (
                            <Badge variant="destructive" className="text-xs">
                              {conv.unread_count}
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mb-1">
                          {conv.participant_role === 'candidat' ? 'Candidate' : 'Recruiter'}
                        </p>
                        <p className="text-sm text-muted-foreground truncate">{conv.last_message}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(conv.last_message_time).toLocaleString()}
                        </p>
                      </Card>
                    ))
                  )}
                </div>
              </Card>

              <div className="lg:col-span-3">
                <Card className="glass-strong p-6">
                  {selectedConv ? (
                    <>
                      <div className="border-b border-border pb-4 mb-4">
                        <h2 className="text-xl font-bold">
                          {conversations.find(c => c.participant_id === selectedConv)?.participant_name}
                        </h2>
                        <p className="text-sm text-muted-foreground">
                          {conversations.find(c => c.participant_id === selectedConv)?.participant_role === 'candidat' ? 'Candidate' : 'Recruiter'}
                        </p>
                      </div>
                      <ChatInterface conversationId={selectedConv.toString()} />
                    </>
                  ) : (
                    <div className="h-[600px] flex items-center justify-center text-muted-foreground">
                      Select a conversation to start messaging
                    </div>
                  )}
                </Card>
              </div>
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}