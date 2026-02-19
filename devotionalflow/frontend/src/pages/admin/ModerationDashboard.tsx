import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Shield, AlertTriangle, CheckCircle, XCircle, Eye, Clock, Bell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
	SidebarProvider,
	SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";

interface ModerationStats {
	total_flags: number;
	pending_flags: number;
	resolved_flags: number;
	dismissed_flags: number;
	flags_by_severity: Record<string, number>;
	recent_flags: any[];
}

interface Flag {
	flag_id: string;
	devotional_id: string;
	devotional_title: string;
	reason: string;
	details?: string;
	severity: string;
	status: string;
	flagged_by: string;
	flagged_at: string;
	resolved_at?: string;
	resolved_by?: string;
}

const ModerationDashboard = () => {
	const { toast } = useToast();
	const [stats, setStats] = useState<ModerationStats | null>(null);
	const [flags, setFlags] = useState<Flag[]>([]);
	const [loading, setLoading] = useState(true);
	const [selectedFlag, setSelectedFlag] = useState<Flag | null>(null);
	const [resolutionNotes, setResolutionNotes] = useState("");
	const [statusFilter, setStatusFilter] = useState<string>("pending");
	const [severityFilter, setSeverityFilter] = useState<string>("all");
	const [resolving, setResolving] = useState(false);

	useEffect(() => {
		fetchModerationData();
	}, [statusFilter, severityFilter]);

	const fetchModerationData = async () => {
		try {
			setLoading(true);

			const [statsData, flagsData] = await Promise.all([
				apiClient.getModerationStats(),
				apiClient.getFlags({
					status: statusFilter === "all" ? undefined : statusFilter as any,
					severity: severityFilter === "all" ? undefined : severityFilter as any,
					page: 1,
					page_size: 50,
				}),
			]);

			setStats(statsData);
			setFlags(flagsData.flags || []);
		} catch (error: any) {
			console.error("Failed to fetch moderation data:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to load moderation data",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const handleResolveFlag = async (action: 'approve' | 'delete' | 'hide' | 'warn_author' | 'suspend_author' | 'dismiss_flag') => {
		if (!selectedFlag) return;

		try {
			setResolving(true);

			await apiClient.resolveFlag(selectedFlag.flag_id, {
				action: action,
				notes: resolutionNotes,
			});

			toast({
				title: "Success",
				description: "Flag resolved successfully",
			});

			setSelectedFlag(null);
			setResolutionNotes("");
			fetchModerationData();
		} catch (error: any) {
			console.error("Failed to resolve flag:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to resolve flag",
				variant: "destructive",
			});
		} finally {
			setResolving(false);
		}
	};

	const getSeverityColor = (severity: string) => {
		switch (severity) {
			case "critical":
				return "bg-destructive text-destructive-foreground";
			case "high":
				return "bg-secondary text-secondary-foreground";
			case "medium":
				return "bg-yellow-500 text-black";
			case "low":
				return "bg-blue-500 text-white";
			default:
				return "bg-muted text-muted-foreground";
		}
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case "pending":
				return "bg-yellow-500/10 text-yellow-700 border-yellow-500/20";
			case "resolved":
				return "bg-green-500/10 text-green-700 border-green-500/20";
			case "dismissed":
				return "bg-gray-500/10 text-gray-700 border-gray-500/20";
			default:
				return "bg-muted text-muted-foreground";
		}
	};

	const formatTimestamp = (timestamp: string) => {
		const date = new Date(timestamp);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: 'numeric',
			minute: '2-digit',
		});
	};

	return (
		<SidebarProvider>
			<div className="min-h-screen flex w-full bg-background">
				<AdminSidebar />

				<div className="flex-1 overflow-auto">
					{/* Header */}
					<header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
						<div className="flex h-16 items-center gap-4 px-6">
							<SidebarTrigger className="md:hidden" />
							<div className="flex-1">
								<h1 className="text-xl font-serif font-bold text-foreground">Content Moderation</h1>
								<p className="text-sm text-muted-foreground">Review and manage flagged content</p>
							</div>
							<Button variant="outline" size="icon">
								<Bell className="w-4 h-4" />
							</Button>
						</div>
					</header>

					{/* Content */}
					<div className="p-6">
						<div className="flex items-center justify-between mb-6">
							<div>
								<Select value={statusFilter} onValueChange={setStatusFilter}>
									<SelectTrigger className="w-32">
										<SelectValue />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="all">All Status</SelectItem>
										<SelectItem value="pending">Pending</SelectItem>
										<SelectItem value="resolved">Resolved</SelectItem>
										<SelectItem value="dismissed">Dismissed</SelectItem>
									</SelectContent>
								</Select>
								<Select value={severityFilter} onValueChange={setSeverityFilter}>
									<SelectTrigger className="w-32">
										<SelectValue />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="all">All Severity</SelectItem>
										<SelectItem value="critical">Critical</SelectItem>
										<SelectItem value="high">High</SelectItem>
										<SelectItem value="medium">Medium</SelectItem>
										<SelectItem value="low">Low</SelectItem>
									</SelectContent>
								</Select>
							</div>
						</div>
					</div>

					<div className="p-6 space-y-6">
						{/* Stats */}
						<div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
					{loading ? (
						Array.from({ length: 4 }).map((_, i) => (
							<Card key={i}>
								<CardContent className="p-6">
									<Skeleton className="h-8 w-16 mb-2" />
									<Skeleton className="h-4 w-20" />
								</CardContent>
							</Card>
						))
					) : stats ? (
						[
							{ label: "Total Flags", value: stats.total_flags, icon: AlertTriangle, color: "text-secondary" },
							{ label: "Pending", value: stats.pending_flags, icon: Clock, color: "text-yellow-500" },
							{ label: "Resolved", value: stats.resolved_flags, icon: CheckCircle, color: "text-green-500" },
							{ label: "Dismissed", value: stats.dismissed_flags, icon: XCircle, color: "text-gray-500" },
						].map((stat, i) => (
							<Card key={i}>
								<CardContent className="p-6">
									<div className="flex items-center gap-3 mb-2">
										<stat.icon className={`w-5 h-5 ${stat.color}`} />
										<p className="text-2xl font-bold text-foreground">{stat.value}</p>
									</div>
									<p className="text-sm text-muted-foreground">{stat.label}</p>
								</CardContent>
							</Card>
						))
					) : null}
				</div>

				{/* Flags List */}
				<Card>
					<CardHeader>
						<CardTitle>Flagged Content</CardTitle>
					</CardHeader>
					<CardContent>
						{loading ? (
							<div className="space-y-4">
								{Array.from({ length: 5 }).map((_, i) => (
									<Skeleton key={i} className="h-24 w-full" />
								))}
							</div>
						) : flags.length > 0 ? (
							<div className="space-y-4">
								{flags.map((flag) => (
									<motion.div
										key={flag.flag_id}
										initial={{ opacity: 0, y: 20 }}
										animate={{ opacity: 1, y: 0 }}
										className="p-4 bg-muted/50 rounded-lg border border-border hover:border-secondary/50 transition-colors cursor-pointer"
										onClick={() => setSelectedFlag(flag)}
									>
										<div className="flex items-start justify-between mb-2">
											<div className="flex-1">
												<h3 className="font-semibold text-foreground mb-1">
													{flag.devotional_title}
												</h3>
												<p className="text-sm text-muted-foreground mb-2">{flag.reason}</p>
												{flag.details && (
													<p className="text-xs text-muted-foreground italic">"{flag.details}"</p>
												)}
											</div>
											<div className="flex flex-col items-end gap-2">
												<Badge className={getSeverityColor(flag.severity)}>
													{flag.severity}
												</Badge>
												<Badge variant="outline" className={getStatusColor(flag.status)}>
													{flag.status}
												</Badge>
											</div>
										</div>
										<div className="flex items-center gap-4 text-xs text-muted-foreground">
											<span>Flagged {formatTimestamp(flag.flagged_at)}</span>
											{flag.resolved_at && (
												<span>Resolved {formatTimestamp(flag.resolved_at)}</span>
											)}
										</div>
									</motion.div>
								))}
							</div>
						) : (
							<div className="text-center py-12">
								<Shield className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
								<p className="text-muted-foreground">No flags found</p>
							</div>
						)}
					</CardContent>
				</Card>
					</div>
				</div>

				{/* Review Dialog */}
			<Dialog open={selectedFlag !== null} onOpenChange={() => setSelectedFlag(null)}>
					<DialogContent className="max-w-2xl">
						<DialogHeader>
							<DialogTitle>Review Flagged Content</DialogTitle>
							<DialogDescription>
								{selectedFlag?.devotional_title}
							</DialogDescription>
						</DialogHeader>

						{selectedFlag && (
							<div className="space-y-4">
								<div>
									<h4 className="font-medium mb-1">Reason for Flag:</h4>
									<p className="text-sm text-muted-foreground">{selectedFlag.reason}</p>
								</div>

								{selectedFlag.details && (
									<div>
										<h4 className="font-medium mb-1">Additional Details:</h4>
										<p className="text-sm text-muted-foreground italic">"{selectedFlag.details}"</p>
									</div>
								)}

								<div className="flex items-center gap-4">
									<div>
										<span className="text-sm font-medium">Severity: </span>
										<Badge className={getSeverityColor(selectedFlag.severity)}>
											{selectedFlag.severity}
										</Badge>
									</div>
									<div>
										<span className="text-sm font-medium">Status: </span>
										<Badge variant="outline" className={getStatusColor(selectedFlag.status)}>
											{selectedFlag.status}
										</Badge>
									</div>
								</div>

								{selectedFlag.status === 'pending' && (
									<>
										<div>
											<label className="text-sm font-medium mb-2 block">
												Resolution Notes:
											</label>
											<Textarea
												placeholder="Add notes about your decision..."
												value={resolutionNotes}
												onChange={(e) => setResolutionNotes(e.target.value)}
												rows={3}
											/>
										</div>

										<DialogFooter className="gap-2">
											<Button
												variant="outline"
												onClick={() => handleResolveFlag("dismiss_flag")}
												disabled={resolving}
											>
												Dismiss Flag
											</Button>
											<Button
												variant="outline"
												onClick={() => handleResolveFlag("approve")}
												disabled={resolving}
											>
												Approve Content
											</Button>
											<Button
												variant="outline"
												onClick={() => handleResolveFlag("hide")}
												disabled={resolving}
											>
												Hide Content
											</Button>
											<Button
												variant="destructive"
												onClick={() => handleResolveFlag("delete")}
												disabled={resolving}
											>
												Delete Content
											</Button>
										</DialogFooter>
									</>
								)}

								{selectedFlag.status !== 'pending' && (
									<div className="bg-muted p-4 rounded-lg">
										<p className="text-sm text-muted-foreground">
											This flag has already been {selectedFlag.status}.
										</p>
										{selectedFlag.resolved_at && (
											<p className="text-xs text-muted-foreground mt-1">
												Resolved on {formatTimestamp(selectedFlag.resolved_at)}
											</p>
										)}
									</div>
								)}
							</div>
						)}
					</DialogContent>
				</Dialog>
			</div>
		</SidebarProvider>
	);
};

export default ModerationDashboard;
