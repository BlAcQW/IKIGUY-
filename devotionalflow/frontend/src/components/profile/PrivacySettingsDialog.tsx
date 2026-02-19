import { useState, useEffect } from "react";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
	DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Loader2, Lock, Eye, EyeOff, Mail, Activity, MessageSquare } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";

interface PrivacySettingsDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	onSettingsUpdated?: () => void;
}

interface PrivacySettings {
	profile_visibility: "public" | "private";
	show_reading_history: boolean;
	show_bookmarks: boolean;
	show_email: boolean;
	show_activity: boolean;
	allow_comments_on_activity: boolean;
	marketing_emails: boolean;
	announcement_emails: boolean;
	notifications_enabled: boolean;
}

export const PrivacySettingsDialog = ({
	open,
	onOpenChange,
	onSettingsUpdated,
}: PrivacySettingsDialogProps) => {
	const { user, refreshUser } = useAuth();
	const { toast } = useToast();
	const [isLoading, setIsLoading] = useState(false);

	// Form state
	const [settings, setSettings] = useState<PrivacySettings>({
		profile_visibility: "public",
		show_reading_history: true,
		show_bookmarks: true,
		show_email: false,
		show_activity: true,
		allow_comments_on_activity: true,
		marketing_emails: true,
		announcement_emails: true,
		notifications_enabled: true,
	});

	// Load user privacy settings when dialog opens
	useEffect(() => {
		if (open && user?.privacy_settings) {
			setSettings({
				profile_visibility: user.privacy_settings.profile_visibility || "public",
				show_reading_history: user.privacy_settings.show_reading_history ?? true,
				show_bookmarks: user.privacy_settings.show_bookmarks ?? true,
				show_email: user.privacy_settings.show_email ?? false,
				show_activity: user.privacy_settings.show_activity ?? true,
				allow_comments_on_activity: user.privacy_settings.allow_comments_on_activity ?? true,
				marketing_emails: user.privacy_settings.marketing_emails ?? true,
				announcement_emails: user.privacy_settings.announcement_emails ?? true,
				notifications_enabled: user.privacy_settings.notifications_enabled ?? true,
			});
		}
	}, [open, user]);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setIsLoading(true);

		try {
			await apiClient.updateProfile({
				privacy_settings: settings,
			});

			// Refresh user data
			if (refreshUser) {
				await refreshUser();
			}

			toast({
				title: "Privacy settings updated",
				description: "Your privacy preferences have been saved successfully",
			});

			onOpenChange(false);

			// Call callback if provided
			if (onSettingsUpdated) {
				onSettingsUpdated();
			}
		} catch (error: any) {
			console.error("Failed to update privacy settings:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to update privacy settings",
				variant: "destructive",
			});
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-[550px] max-h-[90vh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle className="flex items-center gap-2">
						<Lock className="w-5 h-5" />
						Privacy Settings
					</DialogTitle>
					<DialogDescription>
						Control who can see your information and activity on FreshManna
					</DialogDescription>
				</DialogHeader>

				<form onSubmit={handleSubmit} className="space-y-6">
					{/* Profile Visibility */}
					<div className="space-y-4">
						<div className="flex items-center gap-2 text-sm font-semibold">
							<Eye className="w-4 h-4" />
							<span>Profile Visibility</span>
						</div>

						<div className="space-y-2 pl-6">
							<Label htmlFor="profile_visibility">Who can see your profile</Label>
							<Select
								value={settings.profile_visibility}
								onValueChange={(value: "public" | "private") =>
									setSettings({ ...settings, profile_visibility: value })
								}
								disabled={isLoading}
							>
								<SelectTrigger id="profile_visibility">
									<SelectValue />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="public">
										<div className="flex items-center gap-2">
											<Eye className="w-4 h-4" />
											<div>
												<div className="font-medium">Public</div>
												<div className="text-xs text-muted-foreground">
													Anyone can view your profile
												</div>
											</div>
										</div>
									</SelectItem>
									<SelectItem value="private">
										<div className="flex items-center gap-2">
											<EyeOff className="w-4 h-4" />
											<div>
												<div className="font-medium">Private</div>
												<div className="text-xs text-muted-foreground">
													Only you can view your profile
												</div>
											</div>
										</div>
									</SelectItem>
								</SelectContent>
							</Select>
						</div>
					</div>

					{/* Activity Privacy */}
					<div className="space-y-4 border-t pt-4">
						<div className="flex items-center gap-2 text-sm font-semibold">
							<Activity className="w-4 h-4" />
							<span>Activity Privacy</span>
						</div>

						<div className="space-y-4 pl-6">
							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="show_reading_history">Show Reading History</Label>
									<p className="text-xs text-muted-foreground">
										Let others see which devotionals you've read
									</p>
								</div>
								<Switch
									id="show_reading_history"
									checked={settings.show_reading_history}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, show_reading_history: checked })
									}
									disabled={isLoading}
								/>
							</div>

							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="show_bookmarks">Show Bookmarks</Label>
									<p className="text-xs text-muted-foreground">
										Let others see your saved devotionals
									</p>
								</div>
								<Switch
									id="show_bookmarks"
									checked={settings.show_bookmarks}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, show_bookmarks: checked })
									}
									disabled={isLoading}
								/>
							</div>

							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="show_activity">Show Activity Status</Label>
									<p className="text-xs text-muted-foreground">
										Let others see when you're active
									</p>
								</div>
								<Switch
									id="show_activity"
									checked={settings.show_activity}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, show_activity: checked })
									}
									disabled={isLoading}
								/>
							</div>
						</div>
					</div>

					{/* Contact & Interaction */}
					<div className="space-y-4 border-t pt-4">
						<div className="flex items-center gap-2 text-sm font-semibold">
							<MessageSquare className="w-4 h-4" />
							<span>Contact & Interaction</span>
						</div>

						<div className="space-y-4 pl-6">
							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="show_email">Show Email Address</Label>
									<p className="text-xs text-muted-foreground">
										Display your email on your public profile
									</p>
								</div>
								<Switch
									id="show_email"
									checked={settings.show_email}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, show_email: checked })
									}
									disabled={isLoading}
								/>
							</div>

							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="allow_comments">Allow Comments on Activity</Label>
									<p className="text-xs text-muted-foreground">
										Let others comment on your devotional posts
									</p>
								</div>
								<Switch
									id="allow_comments"
									checked={settings.allow_comments_on_activity}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, allow_comments_on_activity: checked })
									}
									disabled={isLoading}
								/>
							</div>
						</div>
					</div>

					{/* Email Preferences */}
					<div className="space-y-4 border-t pt-4">
						<div className="flex items-center gap-2 text-sm font-semibold">
							<Mail className="w-4 h-4" />
							<span>Email Preferences</span>
						</div>

						<div className="space-y-4 pl-6">
							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="marketing_emails">Marketing Emails</Label>
									<p className="text-xs text-muted-foreground">
										Receive newsletters and promotional content
									</p>
								</div>
								<Switch
									id="marketing_emails"
									checked={settings.marketing_emails}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, marketing_emails: checked })
									}
									disabled={isLoading}
								/>
							</div>

							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="announcement_emails">Announcement Emails</Label>
									<p className="text-xs text-muted-foreground">
										Receive important platform updates
									</p>
								</div>
								<Switch
									id="announcement_emails"
									checked={settings.announcement_emails}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, announcement_emails: checked })
									}
									disabled={isLoading}
								/>
							</div>

							<div className="flex items-center justify-between">
								<div className="space-y-0.5">
									<Label htmlFor="notifications_enabled">All Notifications</Label>
									<p className="text-xs text-muted-foreground">
										Master switch for all email notifications
									</p>
								</div>
								<Switch
									id="notifications_enabled"
									checked={settings.notifications_enabled}
									onCheckedChange={(checked) =>
										setSettings({ ...settings, notifications_enabled: checked })
									}
									disabled={isLoading}
								/>
							</div>
						</div>
					</div>

					<DialogFooter className="border-t pt-4">
						<Button
							type="button"
							variant="outline"
							onClick={() => onOpenChange(false)}
							disabled={isLoading}
						>
							Cancel
						</Button>
						<Button type="submit" disabled={isLoading}>
							{isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
							Save Privacy Settings
						</Button>
					</DialogFooter>
				</form>
			</DialogContent>
		</Dialog>
	);
};
