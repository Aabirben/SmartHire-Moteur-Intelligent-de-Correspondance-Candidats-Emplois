import { useState, useEffect, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, CheckCheck } from "lucide-react";
import { Message } from "@/types";
import { mockMessages } from "@/utils/mockData";
import { toast } from "sonner";

interface ChatInterfaceProps {
  conversationId: string;
  currentUserId: string;
}

export function ChatInterface({ conversationId, currentUserId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(mockMessages[conversationId] || []);
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!newMessage.trim()) {
      toast.error("Please enter a message");
      return;
    }

    const message: Message = {
      id: `msg-${Date.now()}`,
      senderId: currentUserId,
      senderName: "You",
      content: newMessage,
      timestamp: new Date(),
      read: false
    };

    setMessages([...messages, message]);
    setNewMessage("");
    toast.success("Message sent!");

    // Simulate response after 2s
    setTimeout(() => {
      const response: Message = {
        id: `msg-${Date.now()}`,
        senderId: "other-user",
        senderName: "Recruiter",
        content: "Thank you for your message. I'll get back to you soon!",
        timestamp: new Date(),
        read: false
      };
      setMessages(prev => [...prev, response]);
    }, 2000);
  };

  return (
    <div className="flex flex-col h-[600px]">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => {
          const isOwn = message.senderId === currentUserId;
          return (
            <div key={message.id} className={`flex gap-3 ${isOwn ? 'flex-row-reverse' : ''}`}>
              <Avatar className="h-10 w-10 flex-shrink-0">
                <AvatarFallback className="bg-gradient-to-br from-primary to-accent">
                  {message.senderName[0]}
                </AvatarFallback>
              </Avatar>
              
              <div className={`flex-1 max-w-[70%] ${isOwn ? 'items-end' : ''}`}>
                <div className={`glass-strong rounded-lg p-3 ${
                  isOwn ? 'bg-primary/20' : ''
                } transition-all duration-300 hover:scale-[1.02]`}>
                  <p className="text-sm font-medium mb-1">{message.senderName}</p>
                  <p className="text-sm">{message.content}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {isOwn && <CheckCheck className="w-3 h-3" />}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <Card className="glass-strong p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            className="bg-surface"
          />
          <Button 
            onClick={handleSend}
            size="icon"
            className="bg-gradient-to-r from-primary to-accent"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </Card>
    </div>
  );
}
