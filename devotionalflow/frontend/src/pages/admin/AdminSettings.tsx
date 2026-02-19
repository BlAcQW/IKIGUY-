import { useState } from "react";
import {
	Settings,
	Bell,
	Globe,
	Mail,
	Database,
	AlertTriangle,
	Save,
	X,
	CheckCircle,
	Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
	SidebarProvider,
	SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { useToast } from "@/hooks/use-toast";

export default function AdminSettings() {
	const { toast } = useToast();
	const [saving, setSaving] = useState(false);

	// Platform settings
	const [platformName, setPlatformName] = useState("FreshManna");
	const [platformDescription, setPlatformDescription] = useState("Daily Devotionals Platform");
	const [contactEmail, setContactEmail] = useState("admin@freshmanna.com");
	const [supportEmail, setSupportEmail] = useState("support@freshmanna.com");

	// Features
	const [enableComments, setEnableComments] = useState(true);
	const [enableLikes, setEnableLikes] = useState(true);
	const [enableSharing, setEnableSharing] = useState(true);
	const [enableBookmarks, setEnableBookmarks] = useState(true);
	const [enableAudioPlayback, setEnableAudioPlayback] = useState(true);
	const [enableAI, setEnableAI] = useState(true);

	// Moderation
	const [autoModeration, setAutoModeration] = useState(true);
	const [requireApproval, setRequireApproval] = useState(false);
	const [contentFiltering, setContentFiltering] = useState(true);
	const [spamDetection, setSpamDetection] = useState(true);

	// Email notifications
	const [welcomeEmails, setWelcomeEmails] = useState(true);
	const [digestEmails, setDigestEmails] = useState(true);
	const [moderationAlerts, setModerationAlerts] = useState(true);
	const [systemAlerts, setSystemAlerts] = useState(true);
	
	// Subscription drip feed settings
	const [enableSubscriptionDripFeed, setEnableSubscriptionDripFeed] = useState(true);
	const [subscriptionDripFeedTime, setSubscriptionDripFeedTime] = useState("08:00");

	const handleSaveGeneral = async () => {
		setSaving(true);
		await new Promise(resolve => setTimeout(resolve, 1000));
		setSaving(false);
		toast({
			title: "Settings saved",
			description: "General platform settings have been updated successfully.",
		});
	};

	const handleSaveFeatures = async () => {
		setSaving(true);
		await new Promise(resolve => setTimeout(resolve, 1000));
		setSaving(false);
		toast({
			title: "Features updated",
			description: "Platform features have been configured successfully.",
		});
	};

	const handleSaveModeration = async () => {
		setSaving(true);
		await new Promise(resolve => setTimeout(resolve, 1000));
		setSaving(false);
		toast({
			title: "Moderation settings saved",
			description: "Content moderation rules have been updated.",
		});
	};

	const handleSaveEmail = async () => {
		setSaving(true);
		await new Promise(resolve => setTimeout(resolve, 1000));
		setSaving(false);
		toast({
			title: "Email settings saved",
			description: "Email notification preferences have been updated.",
		});
	};

	return (
		<SidebarProvider>
			<div className="flex min-h-screen w-full bg-background">
				<AdminSidebar />

				<main className="flex-1 overflow-auto">
					{/* Header */}
					<header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
						<div className="flex h-16 items-center gap-4 px-6">
							<SidebarTrigger className="md:hidden" />
							<div className="flex-1">
								<h1 className="text-xl font-serif font-bold text-foreground">Platform Settings</h1>
								<p className="text-sm text-muted-foreground">Configure platform-wide settings and preferences</p>
							</div>
							<Button variant="outline" size="icon">
								<Bell className="w-4 h-4" />
							</Button>
						</div>
					</header>

					{/* Content */}
					<div className="p-6 max-w-5xl mx-auto">
						<Tabs defaultValue="general" className="space-y-6">
							<TabsList className="grid w-full grid-cols-5">
								<TabsTrigger value="general">
									<Globe className="w-4 h-4 mr-2" />
									General
								</TabsTrigger>
								<TabsTrigger value="features">
									<CheckCircle className="w-4 h-4 mr-2" />
									Features
								</TabsTrigger>
								<TabsTrigger value="moderation">
									<Shield className="w-4 h-4 mr-2" />
									Moderation
								</TabsTrigger>
								<TabsTrigger value="email">
									<Mail className="w-4 h-4 mr-2" />
									Email
								</TabsTrigger>
								<TabsTrigger value="advanced">
									<Settings className="w-4 h-4 mr-2" />
									Advanced
								</TabsTrigger>
							</TabsList>

							{/* General Settings */}
							<TabsContent value="general" className="space-y-6">
								<Card>
									<CardHeader>
										<CardTitle>General Platform Settings</CardTitle>
										<CardDescription>
											Basic platform information and contact details
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-4">
										<div className="space-y-2">
											<Label htmlFor="platformName">Platform Name</Label>
											<Input
												id="platformName"
												value={platformName}
												onChange={(e) => setPlatformName(e.target.value)}
											/>
										</div>

										<div className="space-y-2">
											<Label htmlFor="platformDescription">Description</Label>
											<Textarea
												id="platformDescription"
												value={platformDescription}
												onChange={(e) => setPlatformDescription(e.target.value)}
												rows={3}
											/>
										</div>

										<div className="grid grid-cols-2 gap-4">
											<div className="space-y-2">
												<Label htmlFor="contactEmail">Contact Email</Label>
												<Input
													id="contactEmail"
													type="email"
													value={contactEmail}
													onChange={(e) => setContactEmail(e.target.value)}
												/>
											</div>

											<div className="space-y-2">
												<Label htmlFor="supportEmail">Support Email</Label>
												<Input
													id="supportEmail"
													type="email"
													value={supportEmail}
													onChange={(e) => setSupportEmail(e.target.value)}
												/>
											</div>
										</div>

										<div className="flex gap-2 pt-4">
											<Button onClick={handleSaveGeneral} disabled={saving}>
												<Save className="w-4 h-4 mr-2" />
												{saving ? "Saving..." : "Save Changes"}
											</Button>
											<Button variant="outline">
												<X className="w-4 h-4 mr-2" />
												Cancel
											</Button>
										</div>
									</CardContent>
								</Card>
							</TabsContent>

							{/* Features */}
							<TabsContent value="features" className="space-y-6">
								<Card>
									<CardHeader>
										<CardTitle>Platform Features</CardTitle>
										<CardDescription>
											Enable or disable platform-wide features
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-6">
										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Comments</Label>
												<p className="text-sm text-muted-foreground">
													Allow users to comment on devotionals
												</p>
											</div>
											<Switch checked={enableComments} onCheckedChange={setEnableComments} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Likes & Reactions</Label>
												<p className="text-sm text-muted-foreground">
													Enable likes and reactions on content
												</p>
											</div>
											<Switch checked={enableLikes} onCheckedChange={setEnableLikes} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Social Sharing</Label>
												<p className="text-sm text-muted-foreground">
													Allow users to share devotionals on social media
												</p>
											</div>
											<Switch checked={enableSharing} onCheckedChange={setEnableSharing} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Bookmarks</Label>
												<p className="text-sm text-muted-foreground">
													Let users bookmark favorite devotionals
												</p>
											</div>
											<Switch checked={enableBookmarks} onCheckedChange={setEnableBookmarks} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Audio Playback</Label>
												<p className="text-sm text-muted-foreground">
													Enable text-to-speech audio for devotionals
												</p>
											</div>
											<Switch checked={enableAudioPlayback} onCheckedChange={setEnableAudioPlayback} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>AI Features</Label>
												<p className="text-sm text-muted-foreground">
													Enable AI-powered content suggestions and generation
												</p>
											</div>
											<Switch checked={enableAI} onCheckedChange={setEnableAI} />
										</div>

										<div className="flex gap-2 pt-4">
											<Button onClick={handleSaveFeatures} disabled={saving}>
												<Save className="w-4 h-4 mr-2" />
												{saving ? "Saving..." : "Save Features"}
											</Button>
										</div>
									</CardContent>
								</Card>
							</TabsContent>

							{/* Moderation */}
							<TabsContent value="moderation" className="space-y-6">
								<Card>
									<CardHeader>
										<CardTitle>Content Moderation</CardTitle>
										<CardDescription>
											Configure automatic content moderation and safety features
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-6">
										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Automatic Moderation</Label>
												<p className="text-sm text-muted-foreground">
													Use AI to automatically flag inappropriate content
												</p>
											</div>
											<Switch checked={autoModeration} onCheckedChange={setAutoModeration} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Require Approval</Label>
												<p className="text-sm text-muted-foreground">
													All new devotionals must be approved before publishing
												</p>
											</div>
											<Switch checked={requireApproval} onCheckedChange={setRequireApproval} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Content Filtering</Label>
												<p className="text-sm text-muted-foreground">
													Filter profanity and inappropriate language
												</p>
											</div>
											<Switch checked={contentFiltering} onCheckedChange={setContentFiltering} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Spam Detection</Label>
												<p className="text-sm text-muted-foreground">
													Automatically detect and block spam content
												</p>
											</div>
											<Switch checked={spamDetection} onCheckedChange={setSpamDetection} />
										</div>

										<div className="flex gap-2 pt-4">
											<Button onClick={handleSaveModeration} disabled={saving}>
												<Save className="w-4 h-4 mr-2" />
												{saving ? "Saving..." : "Save Moderation"}
											</Button>
										</div>
									</CardContent>
								</Card>
							</TabsContent>

							{/* Email */}
							<TabsContent value="email" className="space-y-6">
								<Card>
									<CardHeader>
										<CardTitle>Email Notifications</CardTitle>
										<CardDescription>
											Configure platform-wide email notification settings
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-6">
										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Welcome Emails</Label>
												<p className="text-sm text-muted-foreground">
													Send welcome emails to new users
												</p>
											</div>
											<Switch checked={welcomeEmails} onCheckedChange={setWelcomeEmails} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Daily Digest</Label>
												<p className="text-sm text-muted-foreground">
													Send daily devotional digest to subscribers
												</p>
											</div>
											<Switch checked={digestEmails} onCheckedChange={setDigestEmails} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>Moderation Alerts</Label>
												<p className="text-sm text-muted-foreground">
													Email admins about flagged content
												</p>
											</div>
											<Switch checked={moderationAlerts} onCheckedChange={setModerationAlerts} />
										</div>

										<div className="flex items-center justify-between">
											<div className="space-y-0.5">
												<Label>System Alerts</Label>
												<p className="text-sm text-muted-foreground">
													Important system notifications and updates
												</p>
											</div>
											<Switch checked={systemAlerts} onCheckedChange={setSystemAlerts} />
										</div>

										<hr className="my-6" />

										<div className="space-y-4">
											<h3 className="text-lg font-semibold">Subscription Drip Feed</h3>
											<p className="text-sm text-muted-foreground mb-4">
												Configure when daily devotionals are sent to email and WhatsApp subscribers
											</p>

											<div className="flex items-center justify-between">
												<div className="space-y-0.5">
													<Label>Enable Subscription Drip Feed</Label>
													<p className="text-sm text-muted-foreground">
														Automatically send daily devotionals to subscribers
													</p>
												</div>
												<Switch checked={enableSubscriptionDripFeed} onCheckedChange={setEnableSubscriptionDripFeed} />
											</div>

											{enableSubscriptionDripFeed && (
												<div className="space-y-2">
													<Label htmlFor="drip-feed-time">Send Time (UTC)</Label>
													<Input
														id="drip-feed-time"
														type="time"
														value={subscriptionDripFeedTime}
														onChange={(e) => setSubscriptionDripFeedTime(e.target.value)}
														className="max-w-xs"
													/>
													<p className="text-xs text-muted-foreground">
														Time when daily devotionals are sent to all subscribers (24-hour format, UTC)
													</p>
												</div>
											)}
										</div>

										<div className="flex gap-2 pt-4">
											<Button onClick={handleSaveEmail} disabled={saving}>
												<Save className="w-4 h-4 mr-2" />
												{saving ? "Saving..." : "Save Email Settings"}
											</Button>
										</div>
									</CardContent>
								</Card>
							</TabsContent>

							{/* Advanced */}
							<TabsContent value="advanced" className="space-y-6">
								<Card>
									<CardHeader>
										<CardTitle>Advanced Settings</CardTitle>
										<CardDescription>
											Database and system configuration
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-4">
										<div className="p-4 rounded-lg bg-muted">
											<div className="flex items-center gap-2 mb-2">
												<Database className="w-5 h-5" />
												<h4 className="font-medium">Database</h4>
											</div>
											<p className="text-sm text-muted-foreground mb-4">
												Database maintenance and optimization tools
											</p>
											<div className="flex gap-2">
												<Button variant="outline">Backup Database</Button>
												<Button variant="outline">Optimize Tables</Button>
												<Button variant="outline">Clear Cache</Button>
											</div>
										</div>
									</CardContent>
								</Card>

								<Card className="border-destructive">
									<CardHeader>
										<CardTitle className="text-destructive">Danger Zone</CardTitle>
										<CardDescription>
											Irreversible and potentially dangerous actions
										</CardDescription>
									</CardHeader>
									<CardContent className="space-y-4">
										<div className="flex items-start gap-4">
											<AlertTriangle className="w-5 h-5 text-destructive mt-0.5" />
											<div className="flex-1">
												<h4 className="font-medium mb-1">Reset Platform</h4>
												<p className="text-sm text-muted-foreground mb-3">
													This will delete all user data and reset the platform to factory settings.
												</p>
												<Button variant="destructive" size="sm">
													Reset Platform
												</Button>
											</div>
										</div>
									</CardContent>
								</Card>
							</TabsContent>
						</Tabs>
					</div>
				</main>
			</div>
		</SidebarProvider>
	);
}
