import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Bell, Send, Users, Calendar, Settings, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
	SidebarProvider,
	SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { Checkbox } from "@/components/ui/checkbox";
import { DateTimePicker } from "@/components/ui/date-time-picker";

interface Announcement {
	id: string;
	title: string;
	message: string;
	segments: string[];
	user_ids?: string[];
	scheduled_at?: string;
	sent_at?: string;
	stats?: {
		total: number;
		sent: number;
		failed: number;
		no_subscription: number;
	};
	status: "pending" | "sending" | "sent" | "failed";
}

const AVAILABLE_SEGMENTS = [
	{ id: "all_users", label: "All Users" },
	{ id: "active_readers", label: "Active Readers (30+ reads)" },
	{ id: "regular_readers", label: "Regular Readers (7-29 reads)" },
	{ id: "new_readers", label: "New Readers (< 7 reads)" },
	{ id: "engaged_readers", label: "Engaged Readers (10+ bookmarks)" },
	{ id: "notification_enabled", label: "Notification Enabled" },
	{ id: "mobile_users", label: "Mobile Users" },
	{ id: "desktop_users", label: "Desktop Users" },
];

export default function Announcements() {
	const { toast } = useToast();
	const [loading, setLoading] = useState(false);
	const [announcements, setAnnouncements] = useState<Announcement[]>([]);
	const [showForm, setShowForm] = useState(false);
	
	// Form state
	const [title, setTitle] = useState("");
	const [message, setMessage] = useState("");
	const [selectedSegments, setSelectedSegments] = useState<string[]>([]);
	const [scheduledAt, setScheduledAt] = useState<Date | undefined>(undefined);

	useEffect(() => {
		loadAnnouncements();
	}, []);

	const loadAnnouncements = async () => {
		try {
			setLoading(true);
			const data = await apiClient.listAnnouncements();
			setAnnouncements(data);
		} catch (error: any) {
			console.error("Failed to load announcements:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to load announcements",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!title.trim() || !message.trim()) {
			toast({
				title: "Validation Error",
				description: "Please fill in all required fields",
				variant: "destructive",
			});
			return;
		}

		if (selectedSegments.length === 0) {
			toast({
				title: "Validation Error",
				description: "Please select at least one audience segment",
				variant: "destructive",
			});
			return;
		}

		try {
			setLoading(true);
			await apiClient.createAnnouncement({
				title: title.trim(),
				message: message.trim(),
				segments: selectedSegments,
				scheduled_at: scheduledAt?.toISOString(),
			});

			toast({
				title: "Success",
				description: scheduledAt 
					? "Announcement scheduled successfully" 
					: "Announcement sent successfully",
			});

			// Reset form
			setTitle("");
			setMessage("");
			setSelectedSegments([]);
			setScheduledAt(undefined);
			setShowForm(false);

			// Reload announcements
			loadAnnouncements();
		} catch (error: any) {
			console.error("Failed to create announcement:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to send announcement",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const toggleSegment = (segmentId: string) => {
		setSelectedSegments(prev =>
			prev.includes(segmentId)
				? prev.filter(id => id !== segmentId)
				: [...prev, segmentId]
		);
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
								<h1 className="text-xl font-serif font-bold text-foreground">Announcements</h1>
								<p className="text-sm text-muted-foreground">Send custom notifications to readers</p>
							</div>
							<Button onClick={() => setShowForm(!showForm)}>
								<Send className="w-4 h-4 mr-2" />
								{showForm ? "Cancel" : "New Announcement"}
							</Button>
						</div>
					</header>

					{/* Content */}
					<div className="p-6 space-y-6">
						{/* Create Announcement Form */}
						{showForm && (
							<Card>
								<CardHeader>
									<CardTitle>Create Announcement</CardTitle>
									<CardDescription>Send a custom notification to selected audience segments</CardDescription>
								</CardHeader>
								<CardContent>
									<form onSubmit={handleSubmit} className="space-y-6">
										<div className="space-y-2">
											<Label htmlFor="title">Title *</Label>
											<Input
												id="title"
												value={title}
												onChange={(e) => setTitle(e.target.value)}
												placeholder="Announcement title"
												maxLength={200}
												required
											/>
										</div>

										<div className="space-y-2">
											<Label htmlFor="message">Message *</Label>
											<Textarea
												id="message"
												value={message}
												onChange={(e) => setMessage(e.target.value)}
												placeholder="Announcement message"
												rows={4}
												maxLength={500}
												required
											/>
											<p className="text-xs text-muted-foreground">
												{message.length} / 500 characters
											</p>
										</div>

										<div className="space-y-2">
											<Label>Target Audience *</Label>
											<div className="grid grid-cols-2 md:grid-cols-3 gap-3">
												{AVAILABLE_SEGMENTS.map((segment) => (
													<div key={segment.id} className="flex items-center space-x-2">
														<Checkbox
															id={segment.id}
															checked={selectedSegments.includes(segment.id)}
															onCheckedChange={() => toggleSegment(segment.id)}
														/>
														<Label
															htmlFor={segment.id}
															className="text-sm font-normal cursor-pointer"
														>
															{segment.label}
														</Label>
													</div>
												))}
											</div>
										</div>

										<div className="space-y-2">
											<Label htmlFor="schedule">Schedule (Optional)</Label>
											<DateTimePicker
												value={scheduledAt}
												onChange={setScheduledAt}
												minDate={new Date()}
												placeholder="Send immediately or schedule for later"
											/>
										</div>

										<div className="flex gap-3">
											<Button type="submit" disabled={loading}>
												{scheduledAt ? (
													<>
														<Calendar className="w-4 h-4 mr-2" />
														Schedule
													</>
												) : (
													<>
														<Send className="w-4 h-4 mr-2" />
														Send Now
													</>
												)}
											</Button>
											<Button
												type="button"
												variant="outline"
												onClick={() => {
													setShowForm(false);
													setTitle("");
													setMessage("");
													setSelectedSegments([]);
													setScheduledAt(undefined);
												}}
											>
												Cancel
											</Button>
										</div>
									</form>
								</CardContent>
							</Card>
						)}

						{/* Announcements List */}
						<Card>
							<CardHeader>
								<CardTitle>Recent Announcements</CardTitle>
								<CardDescription>View all sent and scheduled announcements</CardDescription>
							</CardHeader>
							<CardContent>
								{loading && announcements.length === 0 ? (
									<div className="text-center py-8 text-muted-foreground">
										Loading announcements...
									</div>
								) : announcements.length === 0 ? (
									<div className="text-center py-8 text-muted-foreground">
										No announcements yet. Create your first one!
									</div>
								) : (
									<div className="space-y-4">
										{announcements.map((announcement) => (
											<div
												key={announcement.id}
												className="p-4 border rounded-lg space-y-3"
											>
												<div className="flex items-start justify-between">
													<div className="flex-1">
														<h3 className="font-semibold text-foreground">{announcement.title}</h3>
														<p className="text-sm text-muted-foreground mt-1">{announcement.message}</p>
													</div>
													<Badge
														variant={
															announcement.status === "sent"
																? "default"
																: announcement.status === "failed"
																? "destructive"
																: "secondary"
														}
													>
														{announcement.status}
													</Badge>
												</div>

												<div className="flex flex-wrap gap-2">
													{announcement.segments.map((segment) => (
														<Badge key={segment} variant="outline" className="text-xs">
															{AVAILABLE_SEGMENTS.find(s => s.id === segment)?.label || segment}
														</Badge>
													))}
												</div>

												{announcement.stats && (
													<div className="flex items-center gap-4 text-sm text-muted-foreground">
														<span>Sent: {announcement.stats.sent}</span>
														<span>Failed: {announcement.stats.failed}</span>
														<span>No Subscription: {announcement.stats.no_subscription}</span>
													</div>
												)}

												{announcement.sent_at && (
													<p className="text-xs text-muted-foreground">
														Sent: {new Date(announcement.sent_at).toLocaleString()}
													</p>
												)}
												{announcement.scheduled_at && !announcement.sent_at && (
													<p className="text-xs text-muted-foreground">
														Scheduled: {new Date(announcement.scheduled_at).toLocaleString()}
													</p>
												)}
											</div>
										))}
									</div>
								)}
							</CardContent>
						</Card>
					</div>
				</main>
			</div>
		</SidebarProvider>
	);
}

