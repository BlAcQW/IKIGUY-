import { useState } from "react";
import { BookOpen, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

interface ReadingPreferences {
	font_size: "small" | "medium" | "large";
	theme: "light" | "sepia" | "dark";
	line_height: "compact" | "normal" | "relaxed";
}

export function ReadingSettingsSection() {
	const { user, updateUser } = useAuth();
	const { toast } = useToast();
	const [saving, setSaving] = useState(false);

	// Initialize preferences from user or defaults
	const [preferences, setPreferences] = useState<ReadingPreferences>({
		font_size: user?.reading_preferences?.font_size || "medium",
		theme: user?.reading_preferences?.theme || "light",
		line_height: user?.reading_preferences?.line_height || "normal",
	});

	const handleSave = async () => {
		setSaving(true);
		try {
			// Update user profile with new preferences
			await updateUser({
				reading_preferences: preferences,
			});

			toast({
				title: "Settings saved",
				description: "Your reading preferences have been updated",
			});
		} catch (error) {
			console.error("Failed to save reading preferences:", error);
			toast({
				title: "Error",
				description: "Failed to save reading preferences",
				variant: "destructive",
			});
		} finally {
			setSaving(false);
		}
	};

	return (
		<div className="bg-card rounded-xl p-4 md:p-6 border border-border">
			<div className="flex items-center gap-3 mb-6">
				<div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center">
					<BookOpen className="w-5 h-5 text-secondary" />
				</div>
				<div>
					<h3 className="font-semibold text-foreground">Reading Settings</h3>
					<p className="text-sm text-muted-foreground">
						Customize your reading experience
					</p>
				</div>
			</div>

			<div className="space-y-6">
				{/* Font Size */}
				<div className="space-y-3">
					<Label className="text-base font-medium">Font Size</Label>
					<div className="grid grid-cols-3 gap-3">
						{(["small", "medium", "large"] as const).map((size) => (
							<button
								key={size}
								onClick={() => setPreferences({ ...preferences, font_size: size })}
								className={`p-4 rounded-lg border-2 transition-all ${
									preferences.font_size === size
										? "border-secondary bg-secondary/10"
										: "border-border hover:border-secondary/50"
								}`}
							>
								<p
									className={`font-medium ${
										size === "small"
											? "text-sm"
											: size === "medium"
											? "text-base"
											: "text-lg"
									}`}
								>
									Aa
								</p>
								<p className="text-xs text-muted-foreground mt-1 capitalize">
									{size}
								</p>
							</button>
						))}
					</div>
				</div>

				{/* Theme */}
				<div className="space-y-3">
					<Label className="text-base font-medium">Theme</Label>
					<div className="grid grid-cols-3 gap-3">
						{(["light", "sepia", "dark"] as const).map((theme) => (
							<button
								key={theme}
								onClick={() => setPreferences({ ...preferences, theme })}
								className={`p-4 rounded-lg border-2 transition-all ${
									preferences.theme === theme
										? "border-secondary bg-secondary/10"
										: "border-border hover:border-secondary/50"
								}`}
							>
								<div
									className={`w-full h-12 rounded-md mb-2 ${
										theme === "light"
											? "bg-white border border-gray-300"
											: theme === "sepia"
											? "bg-[#f8f6f3] border border-[#e8e6e3]"
											: "bg-gray-900 border border-gray-700"
									}`}
								/>
								<p className="text-xs text-muted-foreground capitalize">{theme}</p>
							</button>
						))}
					</div>
				</div>

				{/* Line Height */}
				<div className="space-y-3">
					<Label className="text-base font-medium">Line Height</Label>
					<div className="grid grid-cols-3 gap-3">
						{(["compact", "normal", "relaxed"] as const).map((height) => (
							<button
								key={height}
								onClick={() =>
									setPreferences({ ...preferences, line_height: height })
								}
								className={`p-4 rounded-lg border-2 transition-all ${
									preferences.line_height === height
										? "border-secondary bg-secondary/10"
										: "border-border hover:border-secondary/50"
								}`}
							>
								<div className="space-y-0.5 mb-2">
									<div
										className={`h-0.5 bg-current ${
											height === "compact" ? "my-0.5" : height === "normal" ? "my-1" : "my-1.5"
										}`}
									/>
									<div
										className={`h-0.5 bg-current ${
											height === "compact" ? "my-0.5" : height === "normal" ? "my-1" : "my-1.5"
										}`}
									/>
									<div
										className={`h-0.5 bg-current ${
											height === "compact" ? "my-0.5" : height === "normal" ? "my-1" : "my-1.5"
										}`}
									/>
								</div>
								<p className="text-xs text-muted-foreground capitalize">{height}</p>
							</button>
						))}
					</div>
				</div>

				{/* Preview */}
				<div className="pt-4 border-t border-border">
					<Label className="text-sm font-medium mb-3 block">Preview</Label>
					<div
						className={`p-6 rounded-lg border ${
							preferences.theme === "light"
								? "bg-white text-gray-900 border-gray-200"
								: preferences.theme === "sepia"
								? "bg-[#f8f6f3] text-[#2a2a2a] border-[#e8e6e3]"
								: "bg-gray-900 text-gray-100 border-gray-700"
						}`}
					>
						<p
							className={`${
								preferences.font_size === "small"
									? "text-sm"
									: preferences.font_size === "medium"
									? "text-base"
									: "text-lg"
							} ${
								preferences.line_height === "compact"
									? "leading-snug"
									: preferences.line_height === "normal"
									? "leading-normal"
									: "leading-relaxed"
							}`}
						>
							"Trust in the LORD with all your heart and lean not on your own
							understanding; in all your ways submit to him, and he will make your
							paths straight."
						</p>
						<p className="text-sm opacity-70 mt-2">— Proverbs 3:5-6</p>
					</div>
				</div>

				{/* Save Button */}
				<Button onClick={handleSave} disabled={saving} className="w-full gap-2">
					<Save className="w-4 h-4" />
					{saving ? "Saving..." : "Save Reading Preferences"}
				</Button>
			</div>
		</div>
	);
}
