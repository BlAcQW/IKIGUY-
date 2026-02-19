/**
 * Push notification utilities for DevotionalFlow.
 * Handles Web Push API subscription and notification display.
 */

import { apiClient } from "@/lib/api";

// VAPID key will be fetched from backend
let VAPID_PUBLIC_KEY_CACHE: string | null = null;

async function getVapidPublicKey(): Promise<string> {
	if (VAPID_PUBLIC_KEY_CACHE) {
		return VAPID_PUBLIC_KEY_CACHE;
	}

	try {
		const data = await apiClient.getVapidPublicKey();
		VAPID_PUBLIC_KEY_CACHE = data.public_key;
		return VAPID_PUBLIC_KEY_CACHE;
	} catch (error) {
		console.error('Failed to fetch VAPID public key:', error);
		throw new Error('VAPID public key not available');
	}
}

/**
 * Request push notification permission and subscribe.
 */
export async function subscribeToPushNotifications(): Promise<boolean> {
	try {
		// Check if browser supports push notifications
		if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
			console.warn("Push notifications are not supported in this browser");
			return false;
		}

		// Request permission
		const permission = await Notification.requestPermission();
		if (permission !== "granted") {
			console.warn("Push notification permission denied");
			return false;
		}

		// Register service worker
		const registration = await navigator.serviceWorker.ready;

		// Get VAPID key from backend
		const vapidPublicKey = await getVapidPublicKey();
		const vapidKey = urlBase64ToUint8Array(vapidPublicKey);
		if (!vapidKey) {
			console.error("VAPID public key not configured");
			return false;
		}

		// Subscribe to push
		const subscription = await registration.pushManager.subscribe({
			userVisibleOnly: true,
			applicationServerKey: vapidKey,
		});

		// Send subscription to backend
		await apiClient.subscribeToPushNotifications(subscription);

		console.log("Successfully subscribed to push notifications");
		return true;
	} catch (error) {
		console.error("Error subscribing to push notifications:", error);
		return false;
	}
}

/**
 * Unsubscribe from push notifications.
 */
export async function unsubscribeFromPushNotifications(): Promise<boolean> {
	try {
		const registration = await navigator.serviceWorker.ready;
		const subscription = await registration.pushManager.getSubscription();

		if (subscription) {
			await subscription.unsubscribe();
			await apiClient.unsubscribeFromPushNotifications(subscription.endpoint);
			console.log("Successfully unsubscribed from push notifications");
			return true;
		}

		return false;
	} catch (error) {
		console.error("Error unsubscribing from push notifications:", error);
		return false;
	}
}

/**
 * Check if user is subscribed to push notifications.
 */
export async function isSubscribedToPushNotifications(): Promise<boolean> {
	try {
		const registration = await navigator.serviceWorker.ready;
		const subscription = await registration.pushManager.getSubscription();
		return subscription !== null;
	} catch (error) {
		console.error("Error checking push subscription:", error);
		return false;
	}
}

/**
 * Convert VAPID public key from base64 URL to Uint8Array.
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array | null {
	if (!base64String) return null;

	const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
	const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");

	const rawData = window.atob(base64);
	const outputArray = new Uint8Array(rawData.length);

	for (let i = 0; i < rawData.length; ++i) {
		outputArray[i] = rawData.charCodeAt(i);
	}

	return outputArray;
}

/**
 * Initialize push notification service worker.
 */
export async function initializePushNotifications(): Promise<void> {
	if ("serviceWorker" in navigator) {
		try {
			// Register service worker for push notifications
			const registration = await navigator.serviceWorker.register("/sw.js", {
				scope: "/",
			});

			console.log("Service Worker registered for push notifications:", registration.scope);

			// Listen for push events
			navigator.serviceWorker.addEventListener("message", (event) => {
				if (event.data && event.data.type === "PUSH_NOTIFICATION") {
					// Handle push notification
					console.log("Push notification received:", event.data);
				}
			});
		} catch (error) {
			console.error("Error registering service worker:", error);
		}
	}
}

