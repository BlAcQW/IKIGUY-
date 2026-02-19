import { BookOpen, BarChart3, PenLine, FileText, Users, Shield, Activity, Settings, ArrowLeft, Bell, LogOut } from "lucide-react";
import {
	Sidebar,
	SidebarContent,
	SidebarGroup,
	SidebarGroupContent,
	SidebarGroupLabel,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
	SidebarFooter,
} from "@/components/ui/sidebar";
import { NavLink, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

const adminMenuItems = [
	{ title: "Dashboard", url: "/admin", icon: BarChart3, section: "overview" },
	{ title: "Compose", url: "/admin/compose", icon: PenLine, section: "content" },
	{ title: "All Content", url: "/admin/content", icon: FileText, section: "content" },
	{ title: "Calendar", url: "/admin/calendar", icon: BookOpen, section: "content" },
	{ title: "Users", url: "/admin/users", icon: Users, section: "management" },
	{ title: "Moderation", url: "/admin/moderation", icon: Shield, section: "management" },
	{ title: "Analytics", url: "/admin/analytics", icon: Activity, section: "management" },
	{ title: "Announcements", url: "/admin/announcements", icon: Bell, section: "management" },
	{ title: "Settings", url: "/admin/settings", icon: Settings, section: "platform" },
];

export function AdminSidebar() {
	const navigate = useNavigate();
	const { logout } = useAuth();

	const contentItems = adminMenuItems.filter(item => item.section === "content");
	const managementItems = adminMenuItems.filter(item => item.section === "management");
	const platformItems = adminMenuItems.filter(item => item.section === "platform");
	const overviewItems = adminMenuItems.filter(item => item.section === "overview");

	const handleLogout = async () => {
		await logout();
		navigate('/');
	};

	return (
		<Sidebar className="border-r border-border bg-card">
			{/* Header */}
			<div className="p-4 border-b border-border">
				<a href="/" className="flex items-center gap-2 mb-3">
					<div className="w-9 h-9 rounded-xl bg-secondary flex items-center justify-center">
						<BookOpen className="w-5 h-5 text-secondary-foreground" />
					</div>
					<div>
						<h2 className="font-serif font-bold text-lg text-foreground">FreshManna</h2>
						<p className="text-xs text-muted-foreground">Admin Panel</p>
					</div>
				</a>

				{/* Back to App Button */}
				<Button
					variant="outline"
					size="sm"
					className="w-full"
					onClick={() => navigate('/feed')}
				>
					<ArrowLeft className="w-4 h-4 mr-2" />
					Back to App
				</Button>
			</div>

			<SidebarContent>
				{/* Overview */}
				<SidebarGroup>
					<SidebarGroupLabel>Overview</SidebarGroupLabel>
					<SidebarGroupContent>
						<SidebarMenu>
							{overviewItems.map((item) => (
								<SidebarMenuItem key={item.title}>
									<SidebarMenuButton asChild>
										<NavLink to={item.url}>
											<item.icon className="w-4 h-4" />
											<span>{item.title}</span>
										</NavLink>
									</SidebarMenuButton>
								</SidebarMenuItem>
							))}
						</SidebarMenu>
					</SidebarGroupContent>
				</SidebarGroup>

				{/* Content Management */}
				<SidebarGroup>
					<SidebarGroupLabel>Content</SidebarGroupLabel>
					<SidebarGroupContent>
						<SidebarMenu>
							{contentItems.map((item) => (
								<SidebarMenuItem key={item.title}>
									<SidebarMenuButton asChild>
										<NavLink to={item.url}>
											<item.icon className="w-4 h-4" />
											<span>{item.title}</span>
										</NavLink>
									</SidebarMenuButton>
								</SidebarMenuItem>
							))}
						</SidebarMenu>
					</SidebarGroupContent>
				</SidebarGroup>

				{/* User & Platform Management */}
				<SidebarGroup>
					<SidebarGroupLabel>Management</SidebarGroupLabel>
					<SidebarGroupContent>
						<SidebarMenu>
							{managementItems.map((item) => (
								<SidebarMenuItem key={item.title}>
									<SidebarMenuButton asChild>
										<NavLink to={item.url}>
											<item.icon className="w-4 h-4" />
											<span>{item.title}</span>
										</NavLink>
									</SidebarMenuButton>
								</SidebarMenuItem>
							))}
						</SidebarMenu>
					</SidebarGroupContent>
				</SidebarGroup>

				{/* Platform Settings */}
				<SidebarGroup>
					<SidebarGroupLabel>Platform</SidebarGroupLabel>
					<SidebarGroupContent>
						<SidebarMenu>
							{platformItems.map((item) => (
								<SidebarMenuItem key={item.title}>
									<SidebarMenuButton asChild>
										<NavLink to={item.url}>
											<item.icon className="w-4 h-4" />
											<span>{item.title}</span>
										</NavLink>
									</SidebarMenuButton>
								</SidebarMenuItem>
							))}
						</SidebarMenu>
					</SidebarGroupContent>
				</SidebarGroup>
			</SidebarContent>

			{/* Footer with Logout */}
			<SidebarFooter className="border-t border-border p-4">
				<Button
					variant="ghost"
					className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
					onClick={handleLogout}
				>
					<LogOut className="w-4 h-4 mr-2" />
					Log Out
				</Button>
			</SidebarFooter>
		</Sidebar>
	);
}
