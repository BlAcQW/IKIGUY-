import { useState, useEffect, useRef } from "react";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
	DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Camera, X, Upload } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ProfileEditDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	onProfileUpdated?: () => void;
}

export const ProfileEditDialog = ({
	open,
	onOpenChange,
	onProfileUpdated,
}: ProfileEditDialogProps) => {
	const { user, refreshUser } = useAuth();
	const { toast } = useToast();
	const [isLoading, setIsLoading] = useState(false);
	const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);

	// Form state
	const [formData, setFormData] = useState({
		name: "",
		bio: "",
		avatar_url: "",
		ministry_name: "",
		ministry_website: "",
	});

	// Load user data when dialog opens
	useEffect(() => {
		if (open && user) {
			setFormData({
				name: user.name || "",
				bio: user.bio || "",
				avatar_url: user.avatar_url || "",
				ministry_name: user.ministry_name || "",
				ministry_website: user.ministry_website || "",
			});
		}
	}, [open, user]);

	const handleChange = (
		e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
	) => {
		const { name, value } = e.target;
		setFormData((prev) => ({ ...prev, [name]: value }));
	};

	const handleAvatarClick = () => {
		fileInputRef.current?.click();
	};

	const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (!file) return;

		// Validate file type
		if (!file.type.startsWith("image/")) {
			toast({
				title: "Invalid file",
				description: "Please select an image file",
				variant: "destructive",
			});
			return;
		}

		// Validate file size (max 5MB)
		if (file.size > 5 * 1024 * 1024) {
			toast({
				title: "File too large",
				description: "Please select an image smaller than 5MB",
				variant: "destructive",
			});
			return;
		}

		setIsUploadingAvatar(true);

		try {
			const formData = new FormData();
			formData.append("file", file);
			formData.append("category", "avatars");

			// Don't set Content-Type manually - axios will set it with the correct boundary
			const response = await apiClient.client.post("/media/upload-image", formData);

			// Update avatar URL in form
			setFormData((prev) => ({
				...prev,
				avatar_url: response.data.url,
			}));

			toast({
				title: "Image uploaded",
				description: "Your profile picture has been updated",
			});
		} catch (error: any) {
			console.error("Avatar upload error:", error);
			toast({
				title: "Upload failed",
				description: error.response?.data?.detail || "Failed to upload image",
				variant: "destructive",
			});
		} finally {
			setIsUploadingAvatar(false);
		}
	};

	const handleRemoveAvatar = () => {
		setFormData((prev) => ({ ...prev, avatar_url: "" }));
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setIsLoading(true);

		try {
			// Only send fields that have changed
			const updateData: any = {};

			if (formData.name !== user?.name) {
				updateData.name = formData.name;
			}
			if (formData.bio !== (user?.bio || "")) {
				updateData.bio = formData.bio;
			}
			if (formData.avatar_url !== (user?.avatar_url || "")) {
				updateData.avatar_url = formData.avatar_url;
			}
			if (formData.ministry_name !== (user?.ministry_name || "")) {
				updateData.ministry_name = formData.ministry_name;
			}
			if (formData.ministry_website !== (user?.ministry_website || "")) {
				updateData.ministry_website = formData.ministry_website;
			}

			// Only update if there are changes
			if (Object.keys(updateData).length === 0) {
				toast({
					title: "No changes",
					description: "No profile changes were made",
				});
				onOpenChange(false);
				return;
			}

			await apiClient.updateProfile(updateData);

			// Refresh user data
			if (refreshUser) {
				await refreshUser();
			}

			toast({
				title: "Profile updated",
				description: "Your profile has been updated successfully",
			});

			onOpenChange(false);

			// Call callback if provided
			if (onProfileUpdated) {
				onProfileUpdated();
			}
		} catch (error: any) {
			console.error("Failed to update profile:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to update profile",
				variant: "destructive",
			});
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="sm:max-w-[500px]">
				<DialogHeader>
					<DialogTitle>Edit Profile</DialogTitle>
					<DialogDescription>
						Update your profile information. Changes will be saved immediately.
					</DialogDescription>
				</DialogHeader>

				<form onSubmit={handleSubmit} className="space-y-4">
					{/* Profile Picture */}
					<div className="space-y-2">
						<Label>Profile Picture</Label>
						<div className="flex items-center gap-4">
							{/* Avatar Preview - Clickable */}
							<div className="relative">
								{formData.avatar_url ? (
									<div className="relative w-20 h-20 rounded-full overflow-hidden border-2 border-border">
										<img
											src={formData.avatar_url}
											alt="Profile"
											className="w-full h-full object-cover"
										/>
										{/* Change Photo Overlay */}
										<button
											type="button"
											onClick={handleAvatarClick}
											disabled={isUploadingAvatar || isLoading}
											className="absolute inset-0 bg-black/50 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center"
										>
											<Camera className="w-6 h-6 text-white" />
										</button>
										{/* Remove Button */}
										<button
											type="button"
											onClick={handleRemoveAvatar}
											className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center hover:bg-destructive/90 transition-colors shadow-lg z-10"
											disabled={isUploadingAvatar || isLoading}
										>
											<X className="w-3 h-3" />
										</button>
									</div>
								) : (
									<button
										type="button"
										onClick={handleAvatarClick}
										disabled={isUploadingAvatar || isLoading}
										className="w-20 h-20 rounded-full bg-muted flex items-center justify-center border-2 border-dashed border-border hover:border-secondary hover:bg-secondary/10 transition-all cursor-pointer"
									>
										{isUploadingAvatar ? (
											<Loader2 className="w-8 h-8 text-muted-foreground animate-spin" />
										) : (
											<Camera className="w-8 h-8 text-muted-foreground" />
										)}
									</button>
								)}
							</div>

							{/* Upload Button */}
							<div className="flex-1 space-y-2">
								<input
									ref={fileInputRef}
									type="file"
									accept="image/*"
									onChange={handleAvatarUpload}
									className="hidden"
									disabled={isUploadingAvatar || isLoading}
								/>
								<Button
									type="button"
									variant="outline"
									size="sm"
									onClick={handleAvatarClick}
									disabled={isUploadingAvatar || isLoading}
									className="gap-2"
								>
									{isUploadingAvatar ? (
										<>
											<Loader2 className="w-4 h-4 animate-spin" />
											Uploading...
										</>
									) : (
										<>
											<Upload className="w-4 h-4" />
											Upload Picture
										</>
									)}
								</Button>
								<p className="text-xs text-muted-foreground">
									JPG, PNG or GIF (max 5MB)
								</p>
							</div>
						</div>
					</div>

					{/* Name */}
					<div className="space-y-2">
						<Label htmlFor="name">
							Name <span className="text-destructive">*</span>
						</Label>
						<Input
							id="name"
							name="name"
							value={formData.name}
							onChange={handleChange}
							placeholder="Your full name"
							required
							disabled={isLoading}
						/>
					</div>

					{/* Bio */}
					<div className="space-y-2">
						<Label htmlFor="bio">Bio</Label>
						<Textarea
							id="bio"
							name="bio"
							value={formData.bio}
							onChange={handleChange}
							placeholder="Tell us about yourself..."
							rows={3}
							maxLength={500}
							disabled={isLoading}
						/>
						<p className="text-xs text-muted-foreground">
							{formData.bio.length}/500 characters
						</p>
					</div>

					{/* Ministry fields - only show for admins/authors */}
					{user?.role === "admin" && (
						<>
							<div className="space-y-2">
								<Label htmlFor="ministry_name">Ministry Name</Label>
								<Input
									id="ministry_name"
									name="ministry_name"
									value={formData.ministry_name}
									onChange={handleChange}
									placeholder="Your ministry name"
									maxLength={200}
									disabled={isLoading}
								/>
							</div>

							<div className="space-y-2">
								<Label htmlFor="ministry_website">Ministry Website</Label>
								<Input
									id="ministry_website"
									name="ministry_website"
									type="url"
									value={formData.ministry_website}
									onChange={handleChange}
									placeholder="https://yourministry.com"
									disabled={isLoading}
								/>
							</div>
						</>
					)}

					<DialogFooter>
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
							Save Changes
						</Button>
					</DialogFooter>
				</form>
			</DialogContent>
		</Dialog>
	);
};
