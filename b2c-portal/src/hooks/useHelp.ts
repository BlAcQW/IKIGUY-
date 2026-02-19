import { useState, useCallback } from 'react';
import { getHelpContent, searchHelpContent, type HelpContent } from '@/lib/help-content';

interface UseHelpReturn {
	getHelp: (key: string) => HelpContent | null;
	searchHelp: (query: string) => HelpContent[];
	recentHelp: string[];
	addToRecent: (key: string) => void;
	clearRecent: () => void;
	isHelpModalOpen: boolean;
	openHelpModal: (key: string) => void;
	closeHelpModal: () => void;
	currentHelpContent: HelpContent | null;
}

export const useHelp = (): UseHelpReturn => {
	const [recentHelp, setRecentHelp] = useState<string[]>([]);
	const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
	const [currentHelpContent, setCurrentHelpContent] = useState<HelpContent | null>(null);

	const getHelp = useCallback((key: string): HelpContent | null => {
		return getHelpContent(key);
	}, []);

	const searchHelp = useCallback((query: string): HelpContent[] => {
		return searchHelpContent(query);
	}, []);

	const addToRecent = useCallback((key: string) => {
		setRecentHelp(prev => {
			const filtered = prev.filter(item => item !== key);
			return [key, ...filtered].slice(0, 5); // Keep only last 5
		});
	}, []);

	const clearRecent = useCallback(() => {
		setRecentHelp([]);
	}, []);

	const openHelpModal = useCallback((key: string) => {
		const content = getHelpContent(key);
		if (content) {
			setCurrentHelpContent(content);
			setIsHelpModalOpen(true);
			addToRecent(key);
		}
	}, [addToRecent]);

	const closeHelpModal = useCallback(() => {
		setIsHelpModalOpen(false);
		setCurrentHelpContent(null);
	}, []);

	return {
		getHelp,
		searchHelp,
		recentHelp,
		addToRecent,
		clearRecent,
		isHelpModalOpen,
		openHelpModal,
		closeHelpModal,
		currentHelpContent
	};
};

// Hook for specific help sections
export const useSectionHelp = (sectionKey: string) => {
	const help = useHelp();
	const sectionHelp = help.getHelp(sectionKey);

	const openSectionHelp = useCallback(() => {
		if (sectionHelp) {
			help.openHelpModal(sectionKey);
		}
	}, [sectionHelp, sectionKey, help]);

	return {
		...help,
		sectionHelp,
		openSectionHelp
	};
};

// Hook for feature-specific help
export const useFeatureHelp = (featureKey: string) => {
	const help = useHelp();
	const featureHelp = help.getHelp(featureKey);

	const openFeatureHelp = useCallback(() => {
		if (featureHelp) {
			help.openHelpModal(featureKey);
		}
	}, [featureHelp, featureKey, help]);

	return {
		...help,
		featureHelp,
		openFeatureHelp
	};
};
