import { useEffect, useRef, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';

interface DemoAnalyticsEvent {
	demo_id: string;
	assistant_id: string;
	event_type: 'view' | 'interaction' | 'conversion' | 'share' | 'embed';
	event_data?: any;
	page_url?: string;
}

interface SessionData {
	session_id: string;
	interaction_count: number;
	conversion_events: any[];
}

export const useDemoAnalytics = (demoId: string, assistantId: string) => {
	const sessionId = useRef<string>(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
	const sessionStartTime = useRef<number>(Date.now());
	const interactionCount = useRef<number>(0);
	const conversionEvents = useRef<any[]>([]);
	const isTracking = useRef<boolean>(false);

	// Start session tracking
	const startSession = useCallback(async () => {
		if (isTracking.current) return;

		try {
			await supabase.functions.invoke('track-demo-analytics', {
				body: {
					action: 'start',
					demo_id: demoId,
					assistant_id: assistantId,
					session_id: sessionId.current,
					user_agent: navigator.userAgent,
					referrer: document.referrer,
					page_url: window.location.href
				}
			});

			isTracking.current = true;

			// Track initial view event
			await trackEvent('view', {
				page_url: window.location.href,
				referrer: document.referrer
			});

		} catch (error) {
			console.error('Failed to start analytics session:', error);
		}
	}, [demoId, assistantId]);

	// Track analytics event
	const trackEvent = useCallback(async (eventType: DemoAnalyticsEvent['event_type'], eventData?: any) => {
		if (!isTracking.current) return;

		try {
			await supabase.functions.invoke('track-demo-analytics', {
				body: {
					action: 'track_event',
					demo_id: demoId,
					assistant_id: assistantId,
					event_type: eventType,
					session_id: sessionId.current,
					event_data: eventData,
					user_agent: navigator.userAgent,
					page_url: window.location.href,
					referrer: document.referrer
				}
			});

			// Update interaction count for certain events
			if (eventType === 'interaction') {
				interactionCount.current++;
			} else if (eventType === 'conversion') {
				conversionEvents.current.push({
					timestamp: new Date().toISOString(),
					data: eventData
				});
			}

		} catch (error) {
			console.error('Failed to track analytics event:', error);
		}
	}, [demoId, assistantId]);

	// Update session
	const updateSession = useCallback(async () => {
		if (!isTracking.current) return;

		try {
			await supabase.functions.invoke('track-demo-analytics', {
				body: {
					action: 'update',
					demo_id: demoId,
					assistant_id: assistantId,
					session_id: sessionId.current,
					interaction_count: interactionCount.current,
					conversion_events: conversionEvents.current
				}
			});
		} catch (error) {
			console.error('Failed to update analytics session:', error);
		}
	}, [demoId, assistantId]);

	// End session
	const endSession = useCallback(async () => {
		if (!isTracking.current) return;

		try {
			const duration = Math.floor((Date.now() - sessionStartTime.current) / 1000);

			await supabase.functions.invoke('track-demo-analytics', {
				body: {
					action: 'end',
					demo_id: demoId,
					assistant_id: assistantId,
					session_id: sessionId.current,
					interaction_count: interactionCount.current,
					conversion_events: conversionEvents.current
				}
			});

			// Track session end event
			await trackEvent('view', {
				duration_seconds: duration,
				interaction_count: interactionCount.current,
				conversion_count: conversionEvents.current.length
			});

			isTracking.current = false;
		} catch (error) {
			console.error('Failed to end analytics session:', error);
		}
	}, [demoId, assistantId, trackEvent]);

	// Track user interactions
	const trackInteraction = useCallback((interactionType: string, data?: any) => {
		trackEvent('interaction', {
			type: interactionType,
			timestamp: new Date().toISOString(),
			...data
		});
	}, [trackEvent]);

	// Track conversions
	const trackConversion = useCallback((conversionType: string, data?: any) => {
		trackEvent('conversion', {
			type: conversionType,
			timestamp: new Date().toISOString(),
			...data
		});
	}, [trackEvent]);

	// Track sharing
	const trackShare = useCallback((shareMethod: string, data?: any) => {
		trackEvent('share', {
			method: shareMethod,
			timestamp: new Date().toISOString(),
			...data
		});
	}, [trackEvent]);

	// Track embedding
	const trackEmbed = useCallback((embedData?: any) => {
		trackEvent('embed', {
			timestamp: new Date().toISOString(),
			...embedData
		});
	}, [trackEvent]);

	// Auto-update session periodically
	useEffect(() => {
		if (!isTracking.current) return;

		const interval = setInterval(updateSession, 30000); // Update every 30 seconds

		return () => clearInterval(interval);
	}, [updateSession]);

	// Handle page visibility changes
	useEffect(() => {
		const handleVisibilityChange = () => {
			if (document.hidden) {
				updateSession();
			} else {
				updateSession();
			}
		};

		document.addEventListener('visibilitychange', handleVisibilityChange);

		return () => {
			document.removeEventListener('visibilitychange', handleVisibilityChange);
		};
	}, [updateSession]);

	// Handle page unload
	useEffect(() => {
		const handleBeforeUnload = () => {
			endSession();
		};

		window.addEventListener('beforeunload', handleBeforeUnload);

		return () => {
			window.removeEventListener('beforeunload', handleBeforeUnload);
			endSession();
		};
	}, [endSession]);

	return {
		startSession,
		trackEvent,
		trackInteraction,
		trackConversion,
		trackShare,
		trackEmbed,
		updateSession,
		endSession,
		sessionId: sessionId.current,
		isTracking: isTracking.current
	};
};
