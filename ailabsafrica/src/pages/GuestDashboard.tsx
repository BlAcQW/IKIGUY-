import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { Eye, EyeOff, ExternalLink, Copy, Trash2, Edit, CheckCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface GuestAssistant {
	id: string;
	assistant_name: string;
	assistant_type: string;
	description?: string;
	website_url?: string;
	demo_url: string;
	status: string;
	created_at: string;
	voice_name?: string;
}

const GuestDashboard = () => {
	const navigate = useNavigate();
	const { toast } = useToast();
	const [searchParams] = useSearchParams();

	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [showPassword, setShowPassword] = useState(false);
	const [loading, setLoading] = useState(false);
	const [assistants, setAssistants] = useState<GuestAssistant[]>([]);
	const [isLoggedIn, setIsLoggedIn] = useState(false);

	useEffect(() => {
		const success = searchParams.get("success");
		const newDemo = searchParams.get("newDemo");
		if (success === "true" && newDemo) {
			toast({
				title: "Demo created successfully!",
				description: "Your new demo has been created and opened in a new tab for testing!",
			});
			// Clear the URL parameters
			navigate("/guest-dashboard", { replace: true });
		}
	}, [searchParams, toast, navigate]);

	const handleLogin = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!email || !password) {
			toast({
				title: "Error",
				description: "Please enter both email and password",
				variant: "destructive",
			});
			return;
		}

		setLoading(true);

		try {
			const { data, error } = await supabase.functions.invoke('guest-assistant-management', {
				body: {
					action: 'login',
					guest_email: email,
					guest_password: password
				}
			});

			if (error) throw error;

			if (data.success) {
				setAssistants(data.assistants);
				setIsLoggedIn(true);
				toast({
					title: "Success",
					description: data.message,
				});
			} else {
				toast({
					title: "Error",
					description: data.error || "Failed to find assistants",
					variant: "destructive",
				});
			}
		} catch (error: any) {
			console.error('Guest login error:', error);
			toast({
				title: "Error",
				description: error.message || "Failed to access assistants",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const copyToClipboard = async (text: string, label: string) => {
		try {
			await navigator.clipboard.writeText(text);
			toast({
				title: "Copied!",
				description: `${label} copied to clipboard`,
			});
		} catch (error) {
			toast({
				title: "Error",
				description: "Failed to copy to clipboard",
				variant: "destructive",
			});
		}
	};

	const openDemo = (demoUrl: string) => {
		window.open(demoUrl, '_blank');
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case 'created':
				return 'bg-green-100 text-green-800';
			case 'paused':
				return 'bg-yellow-100 text-yellow-800';
			case 'deleted':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	};

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	};

	if (!isLoggedIn) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
				<Card className="w-full max-w-md">
					<CardHeader className="text-center">
						<CardTitle className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
							Guest Access
						</CardTitle>
						<CardDescription>
							Enter your email and password to access your assistants
						</CardDescription>
					</CardHeader>
					<CardContent>
						<form onSubmit={handleLogin} className="space-y-4">
							<div className="space-y-2">
								<Label htmlFor="email">Email</Label>
								<Input
									id="email"
									type="email"
									placeholder="Enter your email"
									value={email}
									onChange={(e) => setEmail(e.target.value)}
									required
								/>
							</div>

							<div className="space-y-2">
								<Label htmlFor="password">Password</Label>
								<div className="relative">
									<Input
										id="password"
										type={showPassword ? "text" : "password"}
										placeholder="Enter your password"
										value={password}
										onChange={(e) => setPassword(e.target.value)}
										required
									/>
									<Button
										type="button"
										variant="ghost"
										size="sm"
										className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
										onClick={() => setShowPassword(!showPassword)}
									>
										{showPassword ? (
											<EyeOff className="h-4 w-4" />
										) : (
											<Eye className="h-4 w-4" />
										)}
									</Button>
								</div>
							</div>

							<Button
								type="submit"
								className="w-full"
								disabled={loading}
							>
								{loading ? "Accessing..." : "Access Assistants"}
							</Button>
						</form>

						<div className="mt-6 text-center">
							<p className="text-sm text-muted-foreground">
								Don't have assistants yet?{' '}
								<Button
									variant="link"
									className="p-0 h-auto font-semibold"
									onClick={() => navigate('/create-assistant')}
								>
									Create one now
								</Button>
							</p>
						</div>
					</CardContent>
				</Card>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-background">
			<div className="container mx-auto py-8">
				<div className="flex items-center justify-between mb-8">
					<div>
						<h1 className="text-3xl font-bold">Your Assistants</h1>
						<p className="text-muted-foreground">
							Accessing as guest: {email}
						</p>
					</div>
					<div className="flex gap-2">
						<Button
							variant="outline"
							onClick={() => {
								setIsLoggedIn(false);
								setAssistants([]);
							}}
						>
							Switch Account
						</Button>
						<Button onClick={() => navigate('/create-assistant')}>
							Create New Assistant
						</Button>
					</div>
				</div>

				{assistants.length === 0 ? (
					<Card>
						<CardContent className="text-center py-12">
							<p className="text-muted-foreground mb-4">
								No assistants found for this account
							</p>
							<Button onClick={() => navigate('/create-assistant')}>
								Create Your First Assistant
							</Button>
						</CardContent>
					</Card>
				) : (
					<div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
						{assistants.map((assistant) => (
							<Card key={assistant.id} className="hover:shadow-lg transition-shadow">
								<CardHeader>
									<div className="flex items-start justify-between">
										<div className="flex-1">
											<CardTitle className="text-lg">{assistant.assistant_name}</CardTitle>
											<CardDescription className="mt-1">
												{assistant.description || 'No description'}
											</CardDescription>
										</div>
										<Badge className={getStatusColor(assistant.status)}>
											{assistant.status}
										</Badge>
									</div>
								</CardHeader>
								<CardContent className="space-y-4">
									<div className="space-y-2">
										<div className="flex items-center justify-between text-sm">
											<span className="text-muted-foreground">Type:</span>
											<span className="font-medium">{assistant.assistant_type}</span>
										</div>
										{assistant.voice_name && (
											<div className="flex items-center justify-between text-sm">
												<span className="text-muted-foreground">Voice:</span>
												<span className="font-medium">{assistant.voice_name}</span>
											</div>
										)}
										<div className="flex items-center justify-between text-sm">
											<span className="text-muted-foreground">Created:</span>
											<span className="font-medium">{formatDate(assistant.created_at)}</span>
										</div>
									</div>

									<div className="flex gap-2">
										<Button
											size="sm"
											className="flex-1"
											onClick={() => openDemo(assistant.demo_url)}
										>
											<ExternalLink className="h-4 w-4 mr-2" />
											View Demo
										</Button>
										<Button
											size="sm"
											variant="outline"
											onClick={() => copyToClipboard(assistant.demo_url, 'Demo URL')}
										>
											<Copy className="h-4 w-4" />
										</Button>
									</div>

									{assistant.website_url && (
										<div className="pt-2 border-t">
											<div className="flex items-center justify-between text-sm">
												<span className="text-muted-foreground">Website:</span>
												<Button
													variant="link"
													size="sm"
													className="p-0 h-auto"
													onClick={() => window.open(assistant.website_url, '_blank')}
												>
													Visit Site
												</Button>
											</div>
										</div>
									)}
								</CardContent>
							</Card>
						))}
					</div>
				)}
			</div>
		</div>
	);
};

export default GuestDashboard;
