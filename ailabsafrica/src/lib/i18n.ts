import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Import translation files
import enTranslations from './locales/en.json';
import frTranslations from './locales/fr.json';
import arTranslations from './locales/ar.json';
import swTranslations from './locales/sw.json';
import ptTranslations from './locales/pt.json';

const resources = {
	en: {
		translation: enTranslations
	},
	fr: {
		translation: frTranslations
	},
	ar: {
		translation: arTranslations
	},
	sw: {
		translation: swTranslations
	},
	pt: {
		translation: ptTranslations
	}
};

i18n
	// .use(Backend) // Temporarily disabled to avoid initialization issues
	.use(LanguageDetector)
	.use(initReactI18next)
	.init({
		resources,
		fallbackLng: 'en',
		debug: process.env.NODE_ENV === 'development',

		interpolation: {
			escapeValue: false, // React already escapes values
		},

		detection: {
			order: ['localStorage', 'navigator', 'htmlTag'],
			caches: ['localStorage'],
			lookupLocalStorage: 'i18nextLng',
		},

		// backend: {
		// 	loadPath: '/api/supabase/functions/manage-i18n',
		// 	requestOptions: {
		// 		method: 'POST',
		// 		headers: {
		// 			'Content-Type': 'application/json',
		// 		},
		// 		body: JSON.stringify({
		// 			action: 'get_translations',
		// 			languageCode: '{{lng}}'
		// 		})
		// 	},
		// 	parse: (data: string) => {
		// 		try {
		// 			const response = JSON.parse(data);
		// 			return response.data || {};
		// 		} catch (error) {
		// 			console.error('Error parsing translation data:', error);
		// 			return {};
		// 		}
		// 	}
		// },

		react: {
			useSuspense: false,
		},

		// RTL support
		dir: (lng: string) => {
			return lng === 'ar' ? 'rtl' : 'ltr';
		}
	});

export default i18n;
