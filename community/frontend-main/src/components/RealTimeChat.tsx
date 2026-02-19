import { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Hash, Users, Circle } from "lucide-react";
import { useWebSocket, ChatMessage, UserPresence } from "@/contexts/WebSocketContext";
import { useAuth } from "@/hooks/useAuth";

interface RealTimeChatProps {
  channelId: string;
  channelName: string;
  className?: string;
}

export default function RealTimeChat({ channelId, channelName, className }: RealTimeChatProps) {
  const { user } = useAuth();
  const { socket, isConnected, joinChannel, leaveChannel, sendMessage, onlineUsers } = useWebSocket();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Mock initial messages for demo
  useEffect(() => {
    const mockMessages: ChatMessage[] = [
      {
        id: '1',
        channel_id: channelId,
        channel_name: channelName,
        user_id: 'user1',
        username: 'adebayo_olumide',
        message: `Welcome to the ${channelName} channel! 🎉`,
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        message_type: 'text'
      },
      {
        id: '2',
        channel_id: channelId,
        channel_name: channelName,
        user_id: 'user2',
        username: 'folake_martins',
        message: 'Great to be here! Looking forward to collaborating on language preservation.',
        timestamp: new Date(Date.now() - 3000000).toISOString(),
        message_type: 'text'
      },
      {
        id: '3',
        channel_id: channelId,
        channel_name: channelName,
        user_id: 'user3',
        username: 'kofi_asante',
        message: 'Just submitted some traditional proverbs. Anyone interested in validation?',
        timestamp: new Date(Date.now() - 1800000).toISOString(),
        message_type: 'text'
      }
    ];
    setMessages(mockMessages);
  }, [channelId, channelName]);

  // Join channel when component mounts
  useEffect(() => {
    if (isConnected && channelId) {
      joinChannel(channelId);
      return () => {
        leaveChannel(channelId);
      };
    }
  }, [isConnected, channelId, joinChannel, leaveChannel]);

  // Listen for real-time messages
  useEffect(() => {
    if (!socket) return;

    const handleNewMessage = (message: ChatMessage) => {
      if (message.channel_id === channelId) {
        setMessages(prev => [...prev, message]);
      }
    };

    const handleTypingStart = (data: { user_id: string; username: string; channel_id: string }) => {
      if (data.channel_id === channelId && data.user_id !== user?.id) {
        setTypingUsers(prev => [...prev.filter(u => u !== data.username), data.username]);
      }
    };

    const handleTypingStop = (data: { user_id: string; username: string; channel_id: string }) => {
      if (data.channel_id === channelId) {
        setTypingUsers(prev => prev.filter(u => u !== data.username));
      }
    };

    socket.on('new_message', handleNewMessage);
    socket.on('typing_start', handleTypingStart);
    socket.on('typing_stop', handleTypingStop);

    return () => {
      socket.off('new_message', handleNewMessage);
      socket.off('typing_start', handleTypingStart);
      socket.off('typing_stop', handleTypingStop);
    };
  }, [socket, channelId, user?.id]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    if (newMessage.trim() && isConnected) {
      const messageObj: ChatMessage = {
        id: Date.now().toString(),
        channel_id: channelId,
        channel_name: channelName,
        user_id: user?.id || 'anonymous',
        username: user?.email?.split('@')[0] || 'Anonymous',
        message: newMessage.trim(),
        timestamp: new Date().toISOString(),
        message_type: 'text'
      };

      setMessages(prev => [...prev, messageObj]);
      sendMessage(channelId, newMessage.trim());
      setNewMessage("");
      handleTypingStop();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTypingStart = () => {
    if (!isTyping && socket && isConnected) {
      setIsTyping(true);
      socket.emit('typing_start', { channel_id: channelId });
    }
  };

  const handleTypingStop = () => {
    if (isTyping && socket && isConnected) {
      setIsTyping(false);
      socket.emit('typing_stop', { channel_id: channelId });
    }
  };

  const formatMessageTime = (timestamp: string) => {
    const time = new Date(timestamp);
    return time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getChannelOnlineUsers = () => {
    return onlineUsers.filter(user =>
      user.status === 'online' &&
      (user.current_channel === channelId || user.current_channel === channelName)
    );
  };

  const getUserInitials = (username: string) => {
    return username.split('_').map(part => part[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Hash className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">{channelName}</CardTitle>
            <Badge
              variant={isConnected ? "secondary" : "destructive"}
              className="text-xs"
            >
              <Circle className={`w-2 h-2 mr-1 ${isConnected ? 'fill-green-500' : 'fill-red-500'}`} />
              {isConnected ? 'Live' : 'Offline'}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {getChannelOnlineUsers().length} online
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Messages Area */}
        <ScrollArea className="h-64 w-full border rounded-lg p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className="flex gap-3">
                <Avatar className="h-8 w-8 flex-shrink-0">
                  <AvatarImage src={message.user_avatar} />
                  <AvatarFallback className="text-xs">
                    {getUserInitials(message.username)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">{message.username}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatMessageTime(message.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm break-words">{message.message}</p>
                </div>
              </div>
            ))}

            {/* Typing indicators */}
            {typingUsers.length > 0 && (
              <div className="flex gap-3">
                <div className="h-8 w-8 flex-shrink-0 flex items-center justify-center">
                  <div className="flex gap-1">
                    <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
                <div className="text-sm text-muted-foreground italic">
                  {typingUsers.length === 1
                    ? `${typingUsers[0]} is typing...`
                    : `${typingUsers.slice(0, -1).join(', ')} and ${typingUsers[typingUsers.length - 1]} are typing...`
                  }
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Message Input */}
        <div className="flex gap-2">
          <Input
            placeholder={isConnected ? "Type your message..." : "Connect to chat..."}
            value={newMessage}
            onChange={(e) => {
              setNewMessage(e.target.value);
              if (e.target.value && !isTyping) {
                handleTypingStart();
              } else if (!e.target.value && isTyping) {
                handleTypingStop();
              }
            }}
            onKeyPress={handleKeyPress}
            onBlur={handleTypingStop}
            disabled={!isConnected}
            className="flex-1"
          />
          <Button
            size="icon"
            onClick={handleSendMessage}
            disabled={!newMessage.trim() || !isConnected}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* Connection Status */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Circle className={`w-2 h-2 ${isConnected ? 'fill-green-500' : 'fill-red-500'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          <div className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            <span>{getChannelOnlineUsers().length} online</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}