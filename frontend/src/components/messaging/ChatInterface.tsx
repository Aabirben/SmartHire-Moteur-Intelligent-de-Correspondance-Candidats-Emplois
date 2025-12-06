import { useState, useEffect, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, CheckCheck } from "lucide-react";
import { Message } from "@/types";
import { messagingApi } from "@/utils/api";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";

interface ChatInterfaceProps {
  conversationId: string;
}

export function ChatInterface({ conversationId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

  useEffect(() => {
    if (conversationId) {
      loadMessages(parseInt(conversationId));
    }
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadMessages = async (otherUserId: number) => {
    try {
      const data = await messagingApi.getMessages(otherUserId);
      const transformedMessages = data.map((msg: any) => ({
        id: msg.id.toString(),
        senderId: msg.sender_id.toString(),
        senderName: msg.sender_name,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        read: msg.read
      }));
      setMessages(transformedMessages);
    } catch (error) {
      toast.error("Failed to load messages");
    }
  };

  const handleSend = async () => {
    if (!newMessage.trim() || !conversationId) {
      toast.error("Please enter a message");
      return;
    }

    try {
      const response = await messagingApi.sendMessage(
        parseInt(conversationId),
        newMessage
      );

      const newMsg: Message = {
        id: response.id.toString(),
        senderId: user?.id.toString() || '',
        senderName: `${user?.prenom} ${user?.nom}`,
        content: newMessage,
        timestamp: new Date(response.timestamp),
        read: false
      };

      setMessages([...messages, newMsg]);
      setNewMessage("");
      toast.success("Message sent!");
    } catch (error) {
      toast.error("Failed to send message");
    }
  };

  return (
    <div className="flex flex-col h-[600px]">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => {
          const isOwn = message.senderId === user?.id.toString();
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