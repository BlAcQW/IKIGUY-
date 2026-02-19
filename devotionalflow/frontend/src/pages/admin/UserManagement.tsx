import { useState } from "react";
import { motion } from "framer-motion";
import {
	BookOpen,
	Users,
	Settings,
	Shield,
	Menu,
	Search,
	Bell,
	BarChart3,
	Activity,
	UserPlus,
	MoreHorizontal,
	Mail,
	Calendar,
	Filter,
	Download,
	FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
	SidebarProvider,
	SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

interface User {
	id: string;
	name: string;
	email: string;
	role: "user" | "admin";
	status: "active" | "suspended";
	joinedDate: string;
	devotionalsCount?: number;
	lastActive: string;
}

const mockUsers: User[] = [
	{
		id: "1",
		name: "Sarah Johnson",
		email: "sarah.j@example.com",
		role: "user",
		status: "active",
		joinedDate: "2024-01-15",
		lastActive: "2 hours ago",
	},
	{
		id: "2",
		name: "Michael Chen",
		email: "michael@church.org",
		role: "admin",
		status: "active",
		joinedDate: "2023-11-20",
		devotionalsCount: 156,
		lastActive: "5 minutes ago",
	},
	{
		id: "3",
		name: "Emily Brown",
		email: "emily.brown@example.com",
		role: "admin",
		status: "active",
		joinedDate: "2024-02-10",
		devotionalsCount: 42,
		lastActive: "1 hour ago",
	},
	{
		id: "4",
		name: "Admin User",
		email: "admin@ailabsafrica.com",
		role: "admin",
		status: "active",
		joinedDate: "2023-01-01",
		lastActive: "Just now",
	},
	{
		id: "5",
		name: "David Martinez",
		email: "david.m@example.com",
		role: "user",
		status: "active",
		joinedDate: "2024-03-05",
		lastActive: "1 day ago",
	},
	{
		id: "6",
		name: "James Wilson",
		email: "james@faithchurch.org",
		role: "admin",
		status: "active",
		joinedDate: "2023-09-12",
		devotionalsCount: 203,
		lastActive: "30 minutes ago",
	},
	{
		id: "7",
		name: "Grace Okonkwo",
		email: "grace.o@example.com",
		role: "user",
		status: "active",
		joinedDate: "2024-04-22",
		lastActive: "3 days ago",
	},
	{
		id: "8",
		name: "John Smith",
		email: "john.s@example.com",
		role: "user",
		status: "suspended",
		joinedDate: "2024-02-28",
		lastActive: "2 weeks ago",
	},
];

function UserManagementContent() {
	const [searchQuery, setSearchQuery] = useState("");
	const [roleFilter, setRoleFilter] = useState<string>("all");
	const [selectedUser, setSelectedUser] = useState<User | null>(null);
	const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
	const { toast } = useToast();

	const filteredUsers = mockUsers.filter((user) => {
		const matchesSearch =
			user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			user.email.toLowerCase().includes(searchQuery.toLowerCase());
		const matchesRole = roleFilter === "all" || user.role === roleFilter;
		return matchesSearch && matchesRole;
	});

	const handleEditUser = (user: User) => {
		setSelectedUser(user);
		setIsEditDialogOpen(true);
	};

	const handleUpdateRole = (newRole: "user" | "admin") => {
		if (!selectedUser) return;

		toast({
			title: "Role updated",
			description: `${selectedUser.name} is now a ${newRole}`,
		});
		setIsEditDialogOpen(false);
		setSelectedUser(null);
	};

	const handleSuspendUser = (user: User) => {
		toast({
			title: user.status === "active" ? "User suspended" : "User activated",
			description: `${user.name} has been ${user.status === "active" ? "suspended" : "activated"
				}`,
		});
	};

	const getRoleBadgeColor = (role: string) => {
		switch (role) {
			case "admin":
				return "bg-primary/10 text-primary";
			case "pastor":
				return "bg-secondary/10 text-secondary";
			default:
				return "bg-muted text-muted-foreground";
		}
	};

	return (
		<div className="flex-1 overflow-auto">
			{/* Header */}
			<header className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border">
				<div className="flex items-center justify-between px-6 h-16">
					<div className="flex items-center gap-4">
						<SidebarTrigger className="lg:hidden">
							<Menu className="w-5 h-5" />
						</SidebarTrigger>
						<div className="relative">
							<Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
							<Input
								placeholder="Search users..."
								value={searchQuery}
								onChange={(e) => setSearchQuery(e.target.value)}
								className="pl-9 w-64 h-9 bg-muted/50"
							/>
						</div>
					</div>
					<div className="flex items-center gap-3">
						<Button variant="ghost" size="icon" className="relative">
							<Bell className="w-5 h-5" />
						</Button>
						<Button variant="outline" size="sm" className="gap-2">
							<Download className="w-4 h-4" />
							Export
						</Button>
						<Button variant="hero" size="sm" className="gap-2">
							<UserPlus className="w-4 h-4" />
							Invite Pastor
						</Button>
					</div>
				</div>
			</header>

			{/* Content */}
			<main className="p-6">
				<motion.div
					initial={{ opacity: 0, y: 20 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.5 }}
				>
					{/* Header */}
					<div className="mb-6">
						<h1 className="font-serif text-3xl font-bold text-foreground mb-2">
							User Management
						</h1>
						<p className="text-muted-foreground">
							Manage users, roles, and permissions across the platform
						</p>
					</div>

					{/* Filters */}
					<div className="flex items-center gap-3 mb-6">
						<Select value={roleFilter} onValueChange={setRoleFilter}>
							<SelectTrigger className="w-40">
								<Filter className="w-4 h-4 mr-2" />
								<SelectValue placeholder="Filter by role" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="all">All Roles</SelectItem>
								<SelectItem value="user">Users</SelectItem>
								<SelectItem value="admin">Admins</SelectItem>
							</SelectContent>
						</Select>
						<div className="text-sm text-muted-foreground">
							Showing {filteredUsers.length} of {mockUsers.length} users
						</div>
					</div>

					{/* Users Table */}
					<div className="bg-card rounded-2xl border border-border shadow-soft overflow-hidden">
						<div className="overflow-x-auto">
							<table className="w-full">
								<thead className="bg-muted/50 border-b border-border">
									<tr>
										<th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-6 py-4">
											User
										</th>
										<th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-6 py-4">
											Role
										</th>
										<th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-6 py-4">
											Status
										</th>
										<th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-6 py-4">
											Joined
										</th>
										<th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-6 py-4">
											Last Active
										</th>
										<th className="text-left text-xs font-medium text-muted-foreground uppercase tracking-wider px-6 py-4">
											Devotionals
										</th>
										<th className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider px-6 py-4">
											Actions
										</th>
									</tr>
								</thead>
								<tbody className="divide-y divide-border">
									{filteredUsers.map((user) => (
										<tr
											key={user.id}
											className="hover:bg-muted/30 transition-colors"
										>
											<td className="px-6 py-4">
												<div className="flex items-center gap-3">
													<div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
														<span className="font-semibold text-secondary text-sm">
															{user.name
																? user.name.split(" ").filter(n => n).map((n) => n[0]).join("").toUpperCase().slice(0, 2)
																: "?"}
														</span>
													</div>
													<div>
														<p className="font-medium text-foreground text-sm">
															{user.name}
														</p>
														<p className="text-xs text-muted-foreground flex items-center gap-1">
															<Mail className="w-3 h-3" />
															{user.email}
														</p>
													</div>
												</div>
											</td>
											<td className="px-6 py-4">
												<span
													className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getRoleBadgeColor(
														user.role
													)}`}
												>
													{user.role === "admin" && (
														<Shield className="w-3 h-3 mr-1" />
													)}
													{user.role.charAt(0).toUpperCase() + user.role.slice(1)}
												</span>
											</td>
											<td className="px-6 py-4">
												<span
													className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${user.status === "active"
															? "bg-accent/10 text-accent"
															: "bg-destructive/10 text-destructive"
														}`}
												>
													{user.status}
												</span>
											</td>
											<td className="px-6 py-4">
												<div className="flex items-center gap-1.5 text-sm text-muted-foreground">
													<Calendar className="w-3.5 h-3.5" />
													{new Date(user.joinedDate).toLocaleDateString()}
												</div>
											</td>
											<td className="px-6 py-4 text-sm text-muted-foreground">
												{user.lastActive}
											</td>
											<td className="px-6 py-4 text-sm text-foreground">
												{user.devotionalsCount || "—"}
											</td>
											<td className="px-6 py-4 text-right">
												<DropdownMenu>
													<DropdownMenuTrigger asChild>
														<Button variant="ghost" size="icon">
															<MoreHorizontal className="w-4 h-4" />
														</Button>
													</DropdownMenuTrigger>
													<DropdownMenuContent align="end">
														<DropdownMenuLabel>Actions</DropdownMenuLabel>
														<DropdownMenuSeparator />
														<DropdownMenuItem onClick={() => handleEditUser(user)}>
															Change Role
														</DropdownMenuItem>
														<DropdownMenuItem>View Profile</DropdownMenuItem>
														<DropdownMenuItem>Send Email</DropdownMenuItem>
														<DropdownMenuSeparator />
														<DropdownMenuItem
															onClick={() => handleSuspendUser(user)}
															className="text-destructive"
														>
															{user.status === "active" ? "Suspend" : "Activate"} User
														</DropdownMenuItem>
													</DropdownMenuContent>
												</DropdownMenu>
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>
				</motion.div>
			</main>

			{/* Edit User Dialog */}
			<Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
				<DialogContent>
					<DialogHeader>
						<DialogTitle>Change User Role</DialogTitle>
						<DialogDescription>
							Update the role for {selectedUser?.name}
						</DialogDescription>
					</DialogHeader>
					<div className="space-y-4 py-4">
						<div className="space-y-2">
							<Label>Current Role</Label>
							<p className="text-sm text-muted-foreground">
								{selectedUser?.role.charAt(0).toUpperCase()}
								{selectedUser?.role.slice(1)}
							</p>
						</div>
						<div className="space-y-2">
							<Label htmlFor="role">New Role</Label>
							<Select
								defaultValue={selectedUser?.role}
								onValueChange={(value: any) => handleUpdateRole(value)}
							>
								<SelectTrigger>
									<SelectValue />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="user">User</SelectItem>
									<SelectItem value="admin">Admin</SelectItem>
								</SelectContent>
							</Select>
							<p className="text-xs text-muted-foreground">
								Users can read and interact with devotionals. Admins can create content and have full platform access.
							</p>
						</div>
					</div>
					<DialogFooter>
						<Button
							variant="ghost"
							onClick={() => setIsEditDialogOpen(false)}
						>
							Cancel
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
		</div>
	);
}

const UserManagement = () => {
	return (
		<SidebarProvider>
			<div className="min-h-screen flex w-full bg-background">
				<AdminSidebar />
				<UserManagementContent />
			</div>
		</SidebarProvider>
	);
};

export default UserManagement;
