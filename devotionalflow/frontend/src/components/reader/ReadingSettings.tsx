import { useState, useEffect } from "react";
import { Settings, Type, Moon, Sun, AlignLeft, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export type FontSize = "small" | "medium" | "large";
export type Theme = "light" | "sepia" | "dark";
export type LineHeight = "compact" | "normal" | "relaxed";

interface ReadingSettingsProps {
  fontSize: FontSize;
  theme: Theme;
  lineHeight: LineHeight;
  onFontSizeChange: (size: FontSize) => void;
  onThemeChange: (theme: Theme) => void;
  onLineHeightChange: (height: LineHeight) => void;
}

export const ReadingSettings = ({
  fontSize,
  theme,
  lineHeight,
  onFontSizeChange,
  onThemeChange,
  onLineHeightChange,
}: ReadingSettingsProps) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isSaving, setIsSaving] = useState(false);

  // Save preferences to backend when they change
  useEffect(() => {
    if (!user) return;

    const savePreferences = async () => {
      setIsSaving(true);
      try {
        await apiClient.updateReadingPreferences({
          font_size: fontSize,
          theme: theme,
          line_height: lineHeight,
        });
      } catch (error) {
        console.error("Failed to save reading preferences:", error);
      } finally {
        setIsSaving(false);
      }
    };

    // Debounce saves
    const timeoutId = setTimeout(savePreferences, 1000);
    return () => clearTimeout(timeoutId);
  }, [fontSize, theme, lineHeight, user]);

  const fontSizeOptions: { value: FontSize; label: string; preview: string }[] = [
    { value: "small", label: "Small", preview: "Aa" },
    { value: "medium", label: "Medium", preview: "Aa" },
    { value: "large", label: "Large", preview: "Aa" },
  ];

  const themeOptions: { value: Theme; label: string; icon: any; colors: string }[] = [
    { value: "light", label: "Light", icon: Sun, colors: "bg-white border-gray-200" },
    { value: "sepia", label: "Sepia", icon: Sun, colors: "bg-[#f8f6f3] border-[#e8e6e3]" },
    { value: "dark", label: "Dark", icon: Moon, colors: "bg-gray-900 border-gray-700" },
  ];

  const lineHeightOptions: { value: LineHeight; label: string; description: string }[] = [
    { value: "compact", label: "Compact", description: "Less spacing" },
    { value: "normal", label: "Normal", description: "Balanced" },
    { value: "relaxed", label: "Relaxed", description: "More spacing" },
  ];

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" title="Reading settings">
          <Settings className="w-5 h-5" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Reading Settings
            </h4>
            <p className="text-xs text-muted-foreground">
              Customize your reading experience
            </p>
          </div>

          <Separator />

          {/* Font Size */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Type className="w-4 h-4" />
              Font Size
            </Label>
            <div className="grid grid-cols-3 gap-2">
              {fontSizeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => onFontSizeChange(option.value)}
                  className={`
                    relative p-3 rounded-lg border-2 transition-all
                    ${fontSize === option.value
                      ? "border-secondary bg-secondary/10"
                      : "border-border hover:border-secondary/50"
                    }
                  `}
                >
                  {fontSize === option.value && (
                    <Check className="absolute top-1 right-1 w-3 h-3 text-secondary" />
                  )}
                  <div
                    className={`
                      font-semibold text-center mb-1
                      ${option.value === "small" ? "text-base" : ""}
                      ${option.value === "medium" ? "text-lg" : ""}
                      ${option.value === "large" ? "text-xl" : ""}
                    `}
                  >
                    {option.preview}
                  </div>
                  <div className="text-xs text-muted-foreground">{option.label}</div>
                </button>
              ))}
            </div>
          </div>

          <Separator />

          {/* Theme */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Sun className="w-4 h-4" />
              Theme
            </Label>
            <div className="grid grid-cols-3 gap-2">
              {themeOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <button
                    key={option.value}
                    onClick={() => onThemeChange(option.value)}
                    className={`
                      relative p-3 rounded-lg border-2 transition-all
                      ${theme === option.value
                        ? "border-secondary bg-secondary/10"
                        : "border-border hover:border-secondary/50"
                      }
                    `}
                  >
                    {theme === option.value && (
                      <Check className="absolute top-1 right-1 w-3 h-3 text-secondary" />
                    )}
                    <div className={`w-full h-8 rounded ${option.colors} mb-2 flex items-center justify-center`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="text-xs text-muted-foreground">{option.label}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <Separator />

          {/* Line Height */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <AlignLeft className="w-4 h-4" />
              Line Spacing
            </Label>
            <div className="space-y-2">
              {lineHeightOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => onLineHeightChange(option.value)}
                  className={`
                    w-full p-3 rounded-lg border-2 transition-all text-left
                    ${lineHeight === option.value
                      ? "border-secondary bg-secondary/10"
                      : "border-border hover:border-secondary/50"
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm">{option.label}</div>
                      <div className="text-xs text-muted-foreground">{option.description}</div>
                    </div>
                    {lineHeight === option.value && (
                      <Check className="w-4 h-4 text-secondary" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {isSaving && (
            <div className="text-xs text-muted-foreground text-center">
              Saving preferences...
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
};
