import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChatInterface } from "@/components/messaging/ChatInterface";
import { ArrowLeft, MessageSquare } from "lucide-react";
import { mockConversations, getStoredUser } from "@/utils/mockData";

export default function Messages() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const user = getStoredUser();
  const [selectedConv, setSelectedConv] = useState(conversationId || mockConversations[0]?.id);

  const currentConversation = mockConversations.find(c => c.id === selectedConv);

  return (
    <div className="min-h-screen mesh-gradient">
      <header className="border-b border-border glass-strong">
        <div className="container mx-auto px-6 py-4">
          <Button 
            onClick={() => navigate(user?.role === "candidate" ? "/candidate/dashboard" : "/recruiter/dashboard")} 
            variant="ghost" 
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 max-w-7xl">
        <div className="grid lg:grid-cols-4 gap-6">
          <Card className="glass-strong p-4 h-[600px] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-primary" />
              Conversations
            </h2>
            
            <div className="space-y-2">
              {mockConversations.map((conv) => (
                <Card
                  key={conv.id}
                  className={`p-4 cursor-pointer hover:scale-[1.02] transition-all ${
                    selectedConv === conv.id ? 'bg-primary/20 border-primary' : 'glass-strong'
                  }`}
                  onClick={() => setSelectedConv(conv.id)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold">{conv.participantName}</h3>
                    {conv.unreadCount > 0 && (
                      <Badge variant="destructive" className="text-xs">
                        {conv.unreadCount}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mb-1">{conv.jobTitle}</p>
                  <p className="text-sm text-muted-foreground truncate">{conv.lastMessage}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {conv.lastMessageTime.toLocaleString()}
                  </p>
                </Card>
              ))}
            </div>
          </Card>

          <div className="lg:col-span-3">
            <Card className="glass-strong p-6">
              {currentConversation ? (
                <>
                  <div className="border-b border-border pb-4 mb-4">
                    <h2 className="text-xl font-bold">{currentConversation.participantName}</h2>
                    <p className="text-sm text-muted-foreground">{currentConversation.jobTitle}</p>
                  </div>
                  <ChatInterface conversationId={selectedConv} currentUserId={user?.id || "current-user"} />
                </>
              ) : (
                <div className="h-[600px] flex items-center justify-center text-muted-foreground">
                  Select a conversation to start messaging
                </div>
              )}
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
