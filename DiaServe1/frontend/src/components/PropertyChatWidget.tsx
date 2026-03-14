/**
 * Property Chat Widget Component.
 *
 * AI-powered chat widget for property inquiries.
 */

import { useState, useRef, useEffect } from "react";
import { MessageSquare, Send, Loader2, X, Sparkles, Info, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { usePropertyChat } from "@/hooks/use-property-chat";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";

export interface PropertyChatWidgetProps {
  propertyId: string;
  propertyName?: string;
  className?: string;
}

/**
 * Property Chat Widget.
 *
 * Displays an AI chat interface for property inquiries with:
 * - Message history
 * - Suggested questions
 * - Source attribution
 * - Confidence indicators
 */
export function PropertyChatWidget({
  propertyId,
  propertyName = "this property",
  className,
}: PropertyChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();

  const {
    messages,
    sendMessage,
    isLoading,
    error,
    lastResponse,
    clearMessages,
    retry,
  } = usePropertyChat({ propertyId });

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = () => {
    if (!inputValue.trim() || isLoading) return;
    sendMessage(inputValue);
    setInputValue("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInputValue(question);
  };

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        size="lg"
        className={cn(
          "fixed z-50 rounded-full shadow-lg gap-2",
          isMobile ? "bottom-4 right-4" : "bottom-6 right-6",
          className
        )}
        variant="accent"
      >
        <MessageSquare className="h-5 w-5" />
        <span className="hidden sm:inline">Ask AI about {propertyName}</span>
        <span className="sm:hidden">AI Chat</span>
      </Button>
    );
  }

  const chatHeader = (
    <div className="flex items-center justify-between pb-4 border-b">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-accent" />
        <div>
          <h3 className="text-lg font-semibold">AI Assistant</h3>
          <p className="text-xs text-muted-foreground">Ask me about {propertyName}</p>
        </div>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(false)}
        className="h-8 w-8"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );

  const chatContent = (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">Ask me anything about this property!</p>
            <p className="text-xs mt-2">
              I can help with pricing, features, location, and more.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={cn(
              "flex",
              message.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "rounded-lg px-4 py-2 max-w-[80%]",
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground"
              )}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-lg px-4 py-2 bg-secondary text-secondary-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <div className="rounded-lg px-4 py-3 bg-destructive/10 text-destructive text-sm flex items-center gap-2">
              <span>AI assistant is temporarily unavailable. Please try again later.</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={retry}
                disabled={isLoading}
                className="h-7 px-2 text-destructive hover:text-destructive"
              >
                <RotateCcw className="h-3 w-3 mr-1" />
                Retry
              </Button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
    </div>
  );

  const chatSuggestions = lastResponse && lastResponse.suggested_questions.length > 0 && (
    <div className="flex-shrink-0 px-4 py-2 border-t bg-secondary/30">
      <p className="text-xs text-muted-foreground mb-2">Suggested questions:</p>
      <div className="flex flex-wrap gap-2">
        {lastResponse.suggested_questions.map((question, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            onClick={() => handleSuggestedQuestion(question)}
            className="text-xs h-7"
            disabled={isLoading}
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  );

  const chatMetadata = lastResponse && (
    <div className="flex-shrink-0 px-4 py-2 border-t bg-muted/50">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <Info className="h-3 w-3" />
          <span className="text-muted-foreground">
            Confidence: {Math.round(lastResponse.confidence * 100)}%
          </span>
        </div>
        <Badge variant="muted" className="text-xs">
          {lastResponse.question_category.replace("_", " ")}
        </Badge>
      </div>
    </div>
  );

  const chatInput = (
    <div className="flex-shrink-0 p-4 border-t">
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question..."
          disabled={isLoading}
          className="flex-1"
        />
        <Button
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || isLoading}
          size="icon"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-2 text-center">
        Powered by AI • Responses may vary
      </p>
    </div>
  );

  // Mobile: Sheet (full screen)
  if (isMobile) {
    return (
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent side="bottom" className="h-[90vh] p-0 flex flex-col">
          <div className="p-4">
            {chatHeader}
          </div>
          {chatContent}
          {chatSuggestions}
          {chatMetadata}
          {chatInput}
        </SheetContent>
      </Sheet>
    );
  }

  // Desktop: Card (fixed position)
  return (
    <Card className={cn("fixed bottom-6 right-6 w-96 h-[600px] shadow-2xl flex flex-col z-50", className)}>
      <CardHeader className="flex-shrink-0">
        {chatHeader}
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        {chatContent}
      </CardContent>
      {chatSuggestions}
      {chatMetadata}
      {chatInput}
    </Card>
  );
}
