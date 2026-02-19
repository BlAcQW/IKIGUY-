import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { useToast } from '@/hooks/use-toast';
import {
	Phone,
	Activity,
	Users,
	RefreshCw,
	CheckCircle,
	XCircle,
	Server,
	Radio,
	PhoneCall,
	AlertCircle,
	Plus,
	Trash2,
	Eye,
	History
} from 'lucide-react';
import { API_ENDPOINTS } from '@/config/api-config';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SIPPeerDetailsModal } from '@/components/telephony/SIPPeerDetailsModal';
import { SIPPeerManagementModal } from '@/components/telephony/SIPPeerManagementModal';
import { CallHistoryTable, CallRecord } from '@/components/telephony/CallHistoryTable';
import { MetricsChart } from '@/components/telephony/MetricsChart';
import { AlertsPanel } from '@/components/telephony/AlertsPanel';
import { PhoneNumbersPanel } from '@/components/telephony/PhoneNumbersPanel';
import { VapiRoutesPanel } from '@/components/telephony/VapiRoutesPanel';
import { SIPRegistrationPanel } from '@/components/telephony/SIPRegistrationPanel';
import { TelephonyProviderSidebar, TelephonyProvider } from '@/components/telephony/TelephonyProviderSidebar';
import { AsteriskManagementPanel } from '@/components/telephony/AsteriskManagementPanel';
import { FreeSWITCHManagementPanel } from '@/components/telephony/FreeSWITCHManagementPanel';
import { DIDAnalyticsPanel } from '@/components/telephony/DIDAnalyticsPanel';

interface HealthStatus {
	status: string;
	asterisk_connected: boolean;
	ami_version?: string;
	timestamp: string;
}

interface AsteriskStatus {
	status: string;
	uptime?: string;
	active_channels?: number;
	active_calls?: number;
	sip_peers?: number;
}

interface SIPPeerDetails {
	username: string;
	status: string;
	registered: boolean;
	contact?: string;
	ip_address?: string;
	port?: number;
	user_agent?: string;
	last_registration?: string;
	expires?: number;
}

const Telephony: React.FC = () => {
	const { toast } = useToast();
	const [isLoading, setIsLoading] = useState(false);
	const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
	const [asteriskStatus, setAsteriskStatus] = useState<AsteriskStatus | null>(null);
	const [sipPeers, setSipPeers] = useState<string[]>([]);
	const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

	// Provider selection state
	const [selectedProvider, setSelectedProvider] = useState<TelephonyProvider>('freeswitch');

	// Provider information
	const providers = [
		{
			id: 'freeswitch' as TelephonyProvider,
			name: 'FreeSWITCH',
			description: 'Modern SIP server',
			icon: '🚀',
			status: 'healthy' as const,
			features: ['Dynamic provisioning', 'ESL API', 'WebSocket support'],
		},
		{
			id: 'asterisk' as TelephonyProvider,
			name: 'Asterisk',
			description: 'Legacy PBX system',
			icon: '📞',
			status: asteriskStatus?.status === 'healthy' ? ('healthy' as const) : ('unhealthy' as const),
			features: ['PJSIP', 'AMI', 'Dialplan'],
		},
	];

	// Modals state
	const [selectedPeer, setSelectedPeer] = useState<SIPPeerDetails | null>(null);
	const [isPeerDetailsOpen, setIsPeerDetailsOpen] = useState(false);
	const [isPeerManagementOpen, setIsPeerManagementOpen] = useState(false);
	const [managementMode, setManagementMode] = useState<'create' | 'edit'>('create');

	// Call history from API
	const [callHistory, setCallHistory] = useState<CallRecord[]>([]);
	const [isHistoryLoading, setIsHistoryLoading] = useState(false);

	// WebSocket connection
	const [wsConnected, setWsConnected] = useState(false);

	// Fetch health status
	const fetchHealthStatus = async () => {
		try {
			const response = await fetch(API_ENDPOINTS.asterisk.health);
			if (!response.ok) throw new Error('Failed to fetch health status');
			const data = await response.json();
			setHealthStatus(data);
		} catch (error) {
			console.error('Error fetching health status:', error);
			toast({
				title: 'Health Check Failed',
				description: 'Could not connect to Asterisk monitoring service',
				variant: 'destructive',
			});
		}
	};

	// Fetch Asterisk status
	const fetchAsteriskStatus = async () => {
		try {
			const response = await fetch(API_ENDPOINTS.asterisk.status);
			if (!response.ok) throw new Error('Failed to fetch Asterisk status');
			const data = await response.json();
			setAsteriskStatus(data);
		} catch (error) {
			console.error('Error fetching Asterisk status:', error);
		}
	};

	// Fetch SIP peers
	const fetchSIPPeers = async () => {
		try {
			const response = await fetch(API_ENDPOINTS.asterisk.sip.peers);
			if (!response.ok) throw new Error('Failed to fetch SIP peers');
			const data = await response.json();
			setSipPeers(data.peers || []);
		} catch (error) {
			console.error('Error fetching SIP peers:', error);
		}
	};

	// Fetch call history
	const fetchCallHistory = async () => {
		setIsHistoryLoading(true);
		try {
			const response = await fetch(`${API_ENDPOINTS.asterisk.callHistory}?limit=50`);
			if (!response.ok) throw new Error('Failed to fetch call history');
			const data = await response.json();
			setCallHistory(data.calls || []);
		} catch (error) {
			console.error('Error fetching call history:', error);
		} finally {
			setIsHistoryLoading(false);
		}
	};

	// Setup WebSocket connection
	useEffect(() => {
		let ws: WebSocket | null = null;

		const connectWebSocket = () => {
			try {
				ws = new WebSocket(API_ENDPOINTS.asterisk.ws);

				ws.onopen = () => {
					console.log('WebSocket connected');
					setWsConnected(true);
				};

				ws.onmessage = (event) => {
					const message = JSON.parse(event.data);
					console.log('WebSocket message:', message);

					if (message.type === 'status_update') {
						// Update asterisk status in real-time
						setAsteriskStatus(message.data);
					}
				};

				ws.onerror = (error) => {
					console.error('WebSocket error:', error);
					setWsConnected(false);
				};

				ws.onclose = () => {
					console.log('WebSocket closed, reconnecting...');
					setWsConnected(false);
					// Attempt to reconnect after 5 seconds
					setTimeout(connectWebSocket, 5000);
				};
			} catch (error) {
				console.error('Failed to create WebSocket connection:', error);
				setWsConnected(false);
			}
		};

		connectWebSocket();

		return () => {
			if (ws) {
				ws.close();
			}
		};
	}, []);

	// Fetch peer details
	const fetchPeerDetails = async (username: string) => {
		try {
			const response = await fetch(API_ENDPOINTS.asterisk.sip.peerDetail(username));
			if (!response.ok) throw new Error('Failed to fetch peer details');
			const data = await response.json();
			setSelectedPeer(data);
			setIsPeerDetailsOpen(true);
		} catch (error) {
			console.error('Error fetching peer details:', error);
			toast({
				title: 'Error',
				description: 'Failed to fetch peer details',
				variant: 'destructive',
			});
		}
	};

	// Delete SIP peer
	const handleDeletePeer = async (username: string) => {
		if (!confirm(`Are you sure you want to delete SIP peer "${username}"?`)) {
			return;
		}

		setIsLoading(true);
		try {
			const response = await fetch(API_ENDPOINTS.asterisk.sip.peer, {
				method: 'DELETE',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					number: username, // You may need to store the number separately
					sip_username: username,
				}),
			});

			if (!response.ok) throw new Error('Failed to delete SIP peer');

			toast({
				title: 'Success',
				description: 'SIP peer deleted successfully',
			});

			await refreshAllData();
		} catch (error) {
			console.error('Error deleting SIP peer:', error);
			toast({
				title: 'Error',
				description: 'Failed to delete SIP peer',
				variant: 'destructive',
			});
		} finally {
			setIsLoading(false);
		}
	};

	// Reload PJSIP configuration
	const handleReloadPJSIP = async () => {
		setIsLoading(true);
		try {
			const response = await fetch(API_ENDPOINTS.asterisk.reload, {
				method: 'POST',
			});

			if (!response.ok) throw new Error('Failed to reload PJSIP');

			const data = await response.json();
			toast({
				title: 'PJSIP Reloaded',
				description: data.message || 'PJSIP configuration reloaded successfully',
			});

			await refreshAllData();
		} catch (error) {
			console.error('Error reloading PJSIP:', error);
			toast({
				title: 'Reload Failed',
				description: 'Could not reload PJSIP configuration',
				variant: 'destructive',
			});
		} finally {
			setIsLoading(false);
		}
	};

	// Refresh all data
	const refreshAllData = async () => {
		setIsLoading(true);
		try {
			await Promise.all([
				fetchHealthStatus(),
				fetchAsteriskStatus(),
				fetchSIPPeers(),
				fetchCallHistory(),
			]);
			setLastRefresh(new Date());
		} catch (error) {
			console.error('Error refreshing data:', error);
		} finally {
			setIsLoading(false);
		}
	};

	// Initial data load
	useEffect(() => {
		refreshAllData();

		// Auto-refresh every 30 seconds
		const interval = setInterval(refreshAllData, 30000);
		return () => clearInterval(interval);
	}, []);

	return (
		<div className="flex h-screen bg-background">
			<DashboardSidebar />

			<div className="flex-1 flex flex-col overflow-hidden">
				<div className="flex-1 overflow-y-auto p-6 space-y-6">
					{/* Header */}
					<div className="flex items-center justify-between">
						<div>
							<h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
								<Phone className="h-8 w-8 text-indigo-600" />
								Telephony Infrastructure
							</h1>
							<p className="text-muted-foreground mt-1">
								Monitor and manage your Asterisk telephony system
							</p>
						</div>
						<div className="flex items-center gap-2">
							<Badge variant={wsConnected ? 'default' : 'outline'} className={wsConnected ? 'bg-green-500' : ''}>
								<div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-white' : 'bg-gray-400'} mr-2`} />
								{wsConnected ? 'Live' : 'Offline'}
							</Badge>
							<span className="text-sm text-muted-foreground">
								Last updated: {lastRefresh.toLocaleTimeString()}
							</span>
							<Button
								onClick={refreshAllData}
								disabled={isLoading}
								variant="outline"
								size="sm"
							>
								<RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
								Refresh
							</Button>
						</div>
					</div>

					{/* Health Status Cards */}
					<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
						{/* Health Status */}
						<Card>
							<CardHeader className="pb-3">
								<CardTitle className="text-sm font-medium flex items-center gap-2">
									<Activity className="h-4 w-4" />
									System Health
								</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="flex items-center gap-2">
									{healthStatus?.status === 'healthy' ? (
										<>
											<CheckCircle className="h-5 w-5 text-green-500" />
											<Badge variant="default" className="bg-green-500">Healthy</Badge>
										</>
									) : (
										<>
											<XCircle className="h-5 w-5 text-red-500" />
											<Badge variant="destructive">Unhealthy</Badge>
										</>
									)}
								</div>
								{healthStatus?.ami_version && (
									<p className="text-xs text-muted-foreground mt-2">
										{healthStatus.ami_version}
									</p>
								)}
							</CardContent>
						</Card>

						{/* Active Channels */}
						<Card>
							<CardHeader className="pb-3">
								<CardTitle className="text-sm font-medium flex items-center gap-2">
									<Radio className="h-4 w-4" />
									Active Channels
								</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="text-3xl font-bold">
									{asteriskStatus?.active_channels ?? '-'}
								</div>
								<p className="text-xs text-muted-foreground mt-1">
									{asteriskStatus?.active_calls ?? 0} active calls
								</p>
							</CardContent>
						</Card>

						{/* SIP Peers */}
						<Card>
							<CardHeader className="pb-3">
								<CardTitle className="text-sm font-medium flex items-center gap-2">
									<Users className="h-4 w-4" />
									SIP Peers
								</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="text-3xl font-bold">
									{asteriskStatus?.sip_peers ?? sipPeers.length}
								</div>
								<p className="text-xs text-muted-foreground mt-1">
									Registered endpoints
								</p>
							</CardContent>
						</Card>

						{/* Uptime */}
						<Card>
							<CardHeader className="pb-3">
								<CardTitle className="text-sm font-medium flex items-center gap-2">
									<Server className="h-4 w-4" />
									System Uptime
								</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="text-xl font-bold">
									{asteriskStatus?.uptime || 'N/A'}
								</div>
								<p className="text-xs text-muted-foreground mt-1">
									Asterisk PBX
								</p>
							</CardContent>
						</Card>
					</div>

					{/* Tabs for different sections */}
					<Tabs defaultValue="providers" className="w-full">
						<TabsList className="grid w-full grid-cols-9">
							<TabsTrigger value="providers">Providers</TabsTrigger>
							<TabsTrigger value="registration">SIP Setup</TabsTrigger>
							<TabsTrigger value="metrics">Metrics</TabsTrigger>
							<TabsTrigger value="alerts">Alerts</TabsTrigger>
							<TabsTrigger value="routing">Phone Routes</TabsTrigger>
							<TabsTrigger value="did-analytics">DID Analytics</TabsTrigger>
							<TabsTrigger value="peers">SIP Peers</TabsTrigger>
							<TabsTrigger value="history">Call History</TabsTrigger>
							<TabsTrigger value="actions">Quick Actions</TabsTrigger>
						</TabsList>

						{/* Provider Management Tab - NEW */}
						<TabsContent value="providers" className="space-y-4">
							<div className="flex gap-6">
								<TelephonyProviderSidebar
									selectedProvider={selectedProvider}
									onSelectProvider={setSelectedProvider}
									providers={providers}
									onRefresh={refreshAllData}
								/>
								<div className="flex-1">
									{selectedProvider === 'freeswitch' ? (
										<FreeSWITCHManagementPanel />
									) : (
										<AsteriskManagementPanel />
									)}
								</div>
							</div>
						</TabsContent>

						{/* SIP Registration Tab - NEW */}
						<TabsContent value="registration" className="space-y-4">
							<SIPRegistrationPanel />
						</TabsContent>

						{/* Metrics Tab */}
						<TabsContent value="metrics" className="space-y-4">
							<MetricsChart defaultPeriod="24h" />
						</TabsContent>

						{/* Alerts Tab */}
						<TabsContent value="alerts" className="space-y-4">
							<AlertsPanel autoRefresh={true} refreshInterval={30000} />
						</TabsContent>

						{/* Phone Routes Tab - NEW */}
						<TabsContent value="routing" className="space-y-4">
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<Phone className="h-5 w-5" />
										Phone Numbers & Vapi Routes
									</CardTitle>
									<CardDescription>
										Overview of virtual phone numbers and their Vapi assistant routing configuration
									</CardDescription>
								</CardHeader>
								<CardContent className="space-y-6">
									{/* Phone Numbers Section */}
									<div>
										<h3 className="text-lg font-semibold mb-3">Virtual Phone Numbers</h3>
										<PhoneNumbersPanel onRefresh={refreshAllData} />
									</div>

									{/* Vapi Routes Section */}
									<div>
										<h3 className="text-lg font-semibold mb-3">Vapi Call Routing</h3>
										<VapiRoutesPanel onRefresh={refreshAllData} />
									</div>
								</CardContent>
							</Card>
						</TabsContent>

						{/* DID Analytics Tab - NEW */}
						<TabsContent value="did-analytics" className="space-y-4">
							<DIDAnalyticsPanel onRefresh={refreshAllData} />
						</TabsContent>

						{/* SIP Peers Tab */}
						<TabsContent value="peers" className="space-y-4">
							<Card>
								<CardHeader>
									<div className="flex items-center justify-between">
										<div>
											<CardTitle className="flex items-center gap-2">
												<PhoneCall className="h-5 w-5" />
												SIP Peers
											</CardTitle>
											<CardDescription>
												Registered SIP endpoints and their status
											</CardDescription>
										</div>
										<Button
											onClick={() => {
												setManagementMode('create');
												setIsPeerManagementOpen(true);
											}}
											size="sm"
										>
											<Plus className="h-4 w-4 mr-2" />
											Add Peer
										</Button>
									</div>
								</CardHeader>
								<CardContent>
									{sipPeers.length === 0 ? (
										<div className="text-center py-8 text-muted-foreground">
											<AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
											<p>No SIP peers registered</p>
											<Button
												variant="outline"
												size="sm"
												className="mt-4"
												onClick={() => {
													setManagementMode('create');
													setIsPeerManagementOpen(true);
												}}
											>
												Create your first peer
											</Button>
										</div>
									) : (
										<div className="space-y-2">
											{sipPeers.map((peer, index) => (
												<div
													key={index}
													className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent transition-colors"
												>
													<div className="flex items-center gap-3">
														<div className="w-2 h-2 rounded-full bg-green-500" />
														<span className="font-mono text-sm">{peer}</span>
														<Badge variant="outline">Active</Badge>
													</div>
													<div className="flex items-center gap-2">
														<Button
															variant="ghost"
															size="sm"
															onClick={() => fetchPeerDetails(peer)}
														>
															<Eye className="h-4 w-4" />
														</Button>
														<Button
															variant="ghost"
															size="sm"
															onClick={() => handleDeletePeer(peer)}
															disabled={isLoading}
														>
															<Trash2 className="h-4 w-4 text-red-500" />
														</Button>
													</div>
												</div>
											))}
										</div>
									)}
								</CardContent>
							</Card>
						</TabsContent>

						{/* Call History Tab */}
						<TabsContent value="history" className="space-y-4">
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<History className="h-5 w-5" />
										Call History
									</CardTitle>
									<CardDescription>
										Recent call detail records (CDR)
									</CardDescription>
								</CardHeader>
								<CardContent>
									<CallHistoryTable
										calls={callHistory}
										isLoading={isHistoryLoading}
										onRefresh={fetchCallHistory}
									/>
								</CardContent>
							</Card>
						</TabsContent>

						{/* Quick Actions Tab */}
						<TabsContent value="actions" className="space-y-4">
							<Card>
								<CardHeader>
									<CardTitle>Quick Actions</CardTitle>
									<CardDescription>
										Manage your Asterisk telephony system
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
										<Button
											onClick={handleReloadPJSIP}
											disabled={isLoading}
											variant="outline"
											className="w-full h-20 flex-col gap-2"
										>
											<RefreshCw className={`h-6 w-6 ${isLoading ? 'animate-spin' : ''}`} />
											<span>Reload PJSIP Configuration</span>
										</Button>

										<Button
											onClick={fetchSIPPeers}
											disabled={isLoading}
											variant="outline"
											className="w-full h-20 flex-col gap-2"
										>
											<Users className="h-6 w-6" />
											<span>Refresh SIP Peers</span>
										</Button>

										<Button
											onClick={() => window.open(API_ENDPOINTS.asterisk.base + '/docs', '_blank')}
											variant="outline"
											className="w-full h-20 flex-col gap-2"
										>
											<Server className="h-6 w-6" />
											<span>View API Documentation</span>
										</Button>

										<Button
											onClick={refreshAllData}
											disabled={isLoading}
											variant="outline"
											className="w-full h-20 flex-col gap-2"
										>
											<Activity className="h-6 w-6" />
											<span>Refresh All Data</span>
										</Button>
									</div>
								</CardContent>
							</Card>

							{/* Connection Details */}
							<Card>
								<CardHeader>
									<CardTitle>Connection Details</CardTitle>
									<CardDescription>
										Asterisk API configuration and endpoints
									</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="space-y-3 font-mono text-sm">
										<div className="flex items-center justify-between p-2 bg-muted rounded">
											<span className="text-muted-foreground">API Base URL:</span>
											<span className="text-foreground">{API_ENDPOINTS.asterisk.base}</span>
										</div>
										<div className="flex items-center justify-between p-2 bg-muted rounded">
											<span className="text-muted-foreground">AMI Connected:</span>
											<span className="text-foreground">
												{healthStatus?.asterisk_connected ? (
													<Badge variant="default" className="bg-green-500">Connected</Badge>
												) : (
													<Badge variant="destructive">Disconnected</Badge>
												)}
											</span>
										</div>
										<div className="flex items-center justify-between p-2 bg-muted rounded">
											<span className="text-muted-foreground">Status:</span>
											<span className="text-foreground">
												{asteriskStatus?.status || 'Unknown'}
											</span>
										</div>
									</div>
								</CardContent>
							</Card>
						</TabsContent>
					</Tabs>
				</div>
			</div>

			{/* Modals */}
			<SIPPeerDetailsModal
				peer={selectedPeer}
				isOpen={isPeerDetailsOpen}
				onClose={() => {
					setIsPeerDetailsOpen(false);
					setSelectedPeer(null);
				}}
			/>

			<SIPPeerManagementModal
				isOpen={isPeerManagementOpen}
				onClose={() => setIsPeerManagementOpen(false)}
				onSuccess={() => {
					refreshAllData();
					setIsPeerManagementOpen(false);
				}}
				mode={managementMode}
			/>
		</div>
	);
};

export default Telephony;
