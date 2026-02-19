// Language mapping utility for VoiceAgent
export interface LanguageInfo {
	code: string;
	name: string;
	nativeName?: string;
	iso_639_3?: string;
}

// Comprehensive language mapping with codes and full names
export const LANGUAGE_MAPPING: Record<string, LanguageInfo> = {
	'en': { code: 'en', name: 'English', nativeName: 'English' },
	'fr': { code: 'fr', name: 'French', nativeName: 'Français' },
	'es': { code: 'es', name: 'Spanish', nativeName: 'Español' },
	'de': { code: 'de', name: 'German', nativeName: 'Deutsch' },
	'it': { code: 'it', name: 'Italian', nativeName: 'Italiano' },
	'pt': { code: 'pt', name: 'Portuguese', nativeName: 'Português' },
	'pl': { code: 'pl', name: 'Polish', nativeName: 'Polski' },
	'hi': { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
	'ja': { code: 'ja', name: 'Japanese', nativeName: '日本語' },
	'ko': { code: 'ko', name: 'Korean', nativeName: '한국어' },
	'zh': { code: 'zh', name: 'Chinese', nativeName: '中文' },
	'ar': { code: 'ar', name: 'Arabic', nativeName: 'العربية' },
	'ru': { code: 'ru', name: 'Russian', nativeName: 'Русский' },
	'tr': { code: 'tr', name: 'Turkish', nativeName: 'Türkçe' },

	// African languages
	'twi': { code: 'twi', name: 'Twi', nativeName: 'Twi' },
	'asante_twi': { code: 'asante_twi', name: 'Asante Twi', nativeName: 'Asante Twi' },
	'akuapem_twi': { code: 'akuapem_twi', name: 'Akuapem Twi', nativeName: 'Akuapem Twi' },
	'ewe': { code: 'ewe', name: 'Ewe', nativeName: 'Eʋegbe' },
	'ga': { code: 'ga', name: 'Ga', nativeName: 'Ga' },
	'dagbani': { code: 'dagbani', name: 'Dagbani', nativeName: 'Dagbani' },
	'hausa': { code: 'hausa', name: 'Hausa', nativeName: 'Hausa' },
	'yoruba': { code: 'yoruba', name: 'Yoruba', nativeName: 'Yorùbá' },
	'igbo': { code: 'igbo', name: 'Igbo', nativeName: 'Igbo' },
	'swahili': { code: 'swahili', name: 'Swahili', nativeName: 'Kiswahili' },
	'zulu': { code: 'zulu', name: 'Zulu', nativeName: 'isiZulu' },
	'xhosa': { code: 'xhosa', name: 'Xhosa', nativeName: 'isiXhosa' },
	'afrikaans': { code: 'afrikaans', name: 'Afrikaans', nativeName: 'Afrikaans' },
	'kikuyu': { code: 'kikuyu', name: 'Kikuyu', nativeName: 'Gĩkũyũ' },
	'luo': { code: 'luo', name: 'Luo', nativeName: 'Dholuo' },

	// Additional languages
	'amharic': { code: 'amharic', name: 'Amharic', nativeName: 'አማርኛ' },
	'oromo': { code: 'oromo', name: 'Oromo', nativeName: 'Afaan Oromoo' },
	'somali': { code: 'somali', name: 'Somali', nativeName: 'Soomaaliga' },
	'tigrinya': { code: 'tigrinya', name: 'Tigrinya', nativeName: 'ትግርኛ' },
	'wolof': { code: 'wolof', name: 'Wolof', nativeName: 'Wolof' },
	'fula': { code: 'fula', name: 'Fula', nativeName: 'Fulfulde' },
	'mandinka': { code: 'mandinka', name: 'Mandinka', nativeName: 'Mandinka' },
	'bambara': { code: 'bambara', name: 'Bambara', nativeName: 'Bamanankan' },
	'lingala': { code: 'lingala', name: 'Lingala', nativeName: 'Lingála' },
	'kikongo': { code: 'kikongo', name: 'Kikongo', nativeName: 'Kikongo' },
	'tshiluba': { code: 'tshiluba', name: 'Tshiluba', nativeName: 'Tshiluba' },
	'sesotho': { code: 'sesotho', name: 'Sesotho', nativeName: 'Sesotho' },
	'chichewa': { code: 'chichewa', name: 'Chichewa', nativeName: 'Chichewa' },
	'bemba': { code: 'bemba', name: 'Bemba', nativeName: 'Ichibemba' },
	'nyanja': { code: 'nyanja', name: 'Nyanja', nativeName: 'Chichewa' },
	'tonga': { code: 'tonga', name: 'Tonga', nativeName: 'Chitonga' },
	'shona': { code: 'shona', name: 'Shona', nativeName: 'chiShona' },
	'ndebele': { code: 'ndebele', name: 'Ndebele', nativeName: 'isiNdebele' },
	'tswana': { code: 'tswana', name: 'Tswana', nativeName: 'Setswana' },
	'venda': { code: 'venda', name: 'Venda', nativeName: 'Tshivenda' },
	'tsonga': { code: 'tsonga', name: 'Tsonga', nativeName: 'Xitsonga' },
	'northern_sotho': { code: 'northern_sotho', name: 'Northern Sotho', nativeName: 'Sepedi' },
	'swati': { code: 'swati', name: 'Swati', nativeName: 'siSwati' },
	'kinyarwanda': { code: 'kinyarwanda', name: 'Kinyarwanda', nativeName: 'Ikinyarwanda' },
	'kirundi': { code: 'kirundi', name: 'Kirundi', nativeName: 'Ikirundi' },
	'malagasy': { code: 'malagasy', name: 'Malagasy', nativeName: 'Malagasy' },
	'comorian': { code: 'comorian', name: 'Comorian', nativeName: 'Shikomori' },
	'afar': { code: 'afar', name: 'Afar', nativeName: 'Afaraf' },
	'tamazight': { code: 'tamazight', name: 'Tamazight', nativeName: 'Tamazight' },
	'fon': { code: 'fon', name: 'Fon', nativeName: 'Fon' },
	'moore': { code: 'moore', name: 'Moore', nativeName: 'Mòoré' },
	'dioula': { code: 'dioula', name: 'Dioula', nativeName: 'Dioula' },
	'sango': { code: 'sango', name: 'Sango', nativeName: 'Sängö' },
	'kabyle': { code: 'kabyle', name: 'Kabyle', nativeName: 'Taqbaylit' },
	'kabye': { code: 'kabye', name: 'Kabye', nativeName: 'Kabye' },
	'zarma': { code: 'zarma', name: 'Zarma', nativeName: 'Zarma' },
	'kabverdianu': { code: 'kabverdianu', name: 'Kabuverdianu', nativeName: 'Kabuverdianu' },
	'kriol': { code: 'kriol', name: 'Kriol', nativeName: 'Kriol' },
	'maninka': { code: 'maninka', name: 'Maninka', nativeName: 'Maninka' },
	'susu': { code: 'susu', name: 'Susu', nativeName: 'Susu' },
	'oshiwambo': { code: 'oshiwambo', name: 'Oshiwambo', nativeName: 'Oshiwambo' },
	'seychellois_creole': { code: 'seychellois_creole', name: 'Seychellois Creole', nativeName: 'Kreol Seselwa' },
	'krio': { code: 'krio', name: 'Krio', nativeName: 'Krio' },
	'mauritian_creole': { code: 'mauritian_creole', name: 'Mauritian Creole', nativeName: 'Kreol Morisien' },

	// Emerging market languages
	'mandarin': { code: 'mandarin', name: 'Mandarin Chinese', nativeName: '普通话' },
	'hindi': { code: 'hindi', name: 'Hindi', nativeName: 'हिन्दी' },
	'indonesian': { code: 'indonesian', name: 'Indonesian', nativeName: 'Bahasa Indonesia' },
	'filipino': { code: 'filipino', name: 'Filipino', nativeName: 'Filipino' },
	'vietnamese': { code: 'vietnamese', name: 'Vietnamese', nativeName: 'Tiếng Việt' },
	'thai': { code: 'thai', name: 'Thai', nativeName: 'ไทย' },
	'turkish': { code: 'turkish', name: 'Turkish', nativeName: 'Türkçe' },

	// Meta MMS ISO 639-3 codes for enhanced compatibility
	'twi': { code: 'twi', name: 'Twi', nativeName: 'Twi', iso_639_3: 'twi' },
	'aka': { code: 'aka', name: 'Akan', nativeName: 'Akan', iso_639_3: 'aka' },
	'ewe': { code: 'ewe', name: 'Ewe', nativeName: 'Eʋegbe', iso_639_3: 'ewe' },
	'gaa': { code: 'gaa', name: 'Ga', nativeName: 'Ga', iso_639_3: 'gaa' },
	'ada': { code: 'ada', name: 'Dangme', nativeName: 'Dangme', iso_639_3: 'ada' },
	'dag': { code: 'dag', name: 'Dagbani', nativeName: 'Dagbanli', iso_639_3: 'dag' },
	'nzi': { code: 'nzi', name: 'Nzema', nativeName: 'Nzema', iso_639_3: 'nzi' },
	'gjn': { code: 'gjn', name: 'Gonja', nativeName: 'Gonja', iso_639_3: 'gjn' },
	'xsm': { code: 'xsm', name: 'Kasem', nativeName: 'Kasem', iso_639_3: 'xsm' },
	'yor': { code: 'yor', name: 'Yoruba', nativeName: 'Yorùbá', iso_639_3: 'yor' },
	'ibo': { code: 'ibo', name: 'Igbo', nativeName: 'Igbo', iso_639_3: 'ibo' },
	'hau': { code: 'hau', name: 'Hausa', nativeName: 'Hausa', iso_639_3: 'hau' },
	'swa': { code: 'swa', name: 'Swahili', nativeName: 'Kiswahili', iso_639_3: 'swa' },
	'kik': { code: 'kik', name: 'Kikuyu', nativeName: 'Gĩkũyũ', iso_639_3: 'kik' },
	'luo': { code: 'luo', name: 'Luo', nativeName: 'Dholuo', iso_639_3: 'luo' },
	'amh': { code: 'amh', name: 'Amharic', nativeName: 'አማርኛ', iso_639_3: 'amh' },
	'orm': { code: 'orm', name: 'Oromo', nativeName: 'Afaan Oromoo', iso_639_3: 'orm' },
	'som': { code: 'som', name: 'Somali', nativeName: 'Soomaali', iso_639_3: 'som' },
	'tir': { code: 'tir', name: 'Tigrinya', nativeName: 'ትግርኛ', iso_639_3: 'tir' },
	'zul': { code: 'zul', name: 'Zulu', nativeName: 'isiZulu', iso_639_3: 'zul' },
	'xho': { code: 'xho', name: 'Xhosa', nativeName: 'isiXhosa', iso_639_3: 'xho' },
	'afr': { code: 'afr', name: 'Afrikaans', nativeName: 'Afrikaans', iso_639_3: 'afr' },
	'sot': { code: 'sot', name: 'Sotho', nativeName: 'Sesotho', iso_639_3: 'sot' },
	'tsn': { code: 'tsn', name: 'Tswana', nativeName: 'Setswana', iso_639_3: 'tsn' },
	'nbl': { code: 'nbl', name: 'Ndebele', nativeName: 'isiNdebele', iso_639_3: 'nbl' },
	'ssw': { code: 'ssw', name: 'Swati', nativeName: 'siSwati', iso_639_3: 'ssw' },
	'tso': { code: 'tso', name: 'Tsonga', nativeName: 'Xitsonga', iso_639_3: 'tso' },
	'ven': { code: 'ven', name: 'Venda', nativeName: 'Tshivenda', iso_639_3: 'ven' },
	'ful': { code: 'ful', name: 'Fula', nativeName: 'Fulfulde', iso_639_3: 'ful' },
	'wol': { code: 'wol', name: 'Wolof', nativeName: 'Wolof', iso_639_3: 'wol' },
	'bam': { code: 'bam', name: 'Bambara', nativeName: 'Bamanankan', iso_639_3: 'bam' },
	'man': { code: 'man', name: 'Mandinka', nativeName: 'Mandinka', iso_639_3: 'man' },
	'sus': { code: 'sus', name: 'Susu', nativeName: 'Sosoxui', iso_639_3: 'sus' },
	'fon': { code: 'fon', name: 'Fon', nativeName: 'Fon', iso_639_3: 'fon' },
	'kab': { code: 'kab', name: 'Kabye', nativeName: 'Kabiyè', iso_639_3: 'kab' },
	'lin': { code: 'lin', name: 'Lingala', nativeName: 'Lingála', iso_639_3: 'lin' },
	'kon': { code: 'kon', name: 'Kikongo', nativeName: 'Kikongo', iso_639_3: 'kon' },
	'lua': { code: 'lua', name: 'Tshiluba', nativeName: 'Tshiluba', iso_639_3: 'lua' },
	'sag': { code: 'sag', name: 'Sango', nativeName: 'Sängö', iso_639_3: 'sag' },
	'ara': { code: 'ara', name: 'Arabic', nativeName: 'العربية', iso_639_3: 'ara' },
	'ber': { code: 'ber', name: 'Tamazight', nativeName: 'Tamazight', iso_639_3: 'ber' },
	'aar': { code: 'aar', name: 'Afar', nativeName: 'Afaraf', iso_639_3: 'aar' },
	'run': { code: 'run', name: 'Kirundi', nativeName: 'Kirundi', iso_639_3: 'run' },
	'kin': { code: 'kin', name: 'Kinyarwanda', nativeName: 'Ikinyarwanda', iso_639_3: 'kin' },
	'mlg': { code: 'mlg', name: 'Malagasy', nativeName: 'Malagasy', iso_639_3: 'mlg' },
	'nya': { code: 'nya', name: 'Nyanja', nativeName: 'Chichewa', iso_639_3: 'nya' },
	'her': { code: 'her', name: 'Oshiwambo', nativeName: 'Oshiwambo', iso_639_3: 'her' },
	'bem': { code: 'bem', name: 'Bemba', nativeName: 'Ichibemba', iso_639_3: 'bem' },
	'ton': { code: 'ton', name: 'Tonga', nativeName: 'Chitonga', iso_639_3: 'ton' },
	'sna': { code: 'sna', name: 'Shona', nativeName: 'chiShona', iso_639_3: 'sna' },
	'nde': { code: 'nde', name: 'Ndebele', nativeName: 'isiNdebele', iso_639_3: 'nde' },
	'eng': { code: 'eng', name: 'English', nativeName: 'English', iso_639_3: 'eng' },
	'fra': { code: 'fra', name: 'French', nativeName: 'Français', iso_639_3: 'fra' },
	'spa': { code: 'spa', name: 'Spanish', nativeName: 'Español', iso_639_3: 'spa' },
	'por': { code: 'por', name: 'Portuguese', nativeName: 'Português', iso_639_3: 'por' },
	'cmn': { code: 'cmn', name: 'Mandarin', nativeName: '中文', iso_639_3: 'cmn' },
	'hin': { code: 'hin', name: 'Hindi', nativeName: 'हिन्दी', iso_639_3: 'hin' },
	'ind': { code: 'ind', name: 'Indonesian', nativeName: 'Bahasa Indonesia', iso_639_3: 'ind' },
	'fil': { code: 'fil', name: 'Filipino', nativeName: 'Filipino', iso_639_3: 'fil' },
	'vie': { code: 'vie', name: 'Vietnamese', nativeName: 'Tiếng Việt', iso_639_3: 'vie' },
	'tha': { code: 'tha', name: 'Thai', nativeName: 'ไทย', iso_639_3: 'tha' },
	'tur': { code: 'tur', name: 'Turkish', nativeName: 'Türkçe', iso_639_3: 'tur' },
	'ewe': { code: 'ewe', name: 'Ewe', nativeName: 'Eʋegbe', iso_639_3: 'ewe' },
	'gaa': { code: 'gaa', name: 'Ga', nativeName: 'Ga', iso_639_3: 'gaa' },
	'ada': { code: 'ada', name: 'Dangme', nativeName: 'Dangme', iso_639_3: 'ada' },
	'dag': { code: 'dag', name: 'Dagbani', nativeName: 'Dagbanli', iso_639_3: 'dag' },
	'nzi': { code: 'nzi', name: 'Nzema', nativeName: 'Nzema', iso_639_3: 'nzi' },
	'gjn': { code: 'gjn', name: 'Gonja', nativeName: 'Gonja', iso_639_3: 'gjn' },
	'xsm': { code: 'xsm', name: 'Kasem', nativeName: 'Kasem', iso_639_3: 'xsm' },
	'yor': { code: 'yor', name: 'Yoruba', nativeName: 'Yorùbá', iso_639_3: 'yor' },
	'ibo': { code: 'ibo', name: 'Igbo', nativeName: 'Igbo', iso_639_3: 'ibo' },
	'hau': { code: 'hau', name: 'Hausa', nativeName: 'Hausa', iso_639_3: 'hau' },
	'swa': { code: 'swa', name: 'Swahili', nativeName: 'Kiswahili', iso_639_3: 'swa' },
	'kik': { code: 'kik', name: 'Kikuyu', nativeName: 'Gĩkũyũ', iso_639_3: 'kik' },
	'luo': { code: 'luo', name: 'Luo', nativeName: 'Dholuo', iso_639_3: 'luo' },
	'amh': { code: 'amh', name: 'Amharic', nativeName: 'አማርኛ', iso_639_3: 'amh' },
	'orm': { code: 'orm', name: 'Oromo', nativeName: 'Afaan Oromoo', iso_639_3: 'orm' },
	'som': { code: 'som', name: 'Somali', nativeName: 'Soomaali', iso_639_3: 'som' },
	'tir': { code: 'tir', name: 'Tigrinya', nativeName: 'ትግርኛ', iso_639_3: 'tir' },
	'zul': { code: 'zul', name: 'Zulu', nativeName: 'isiZulu', iso_639_3: 'zul' },
	'xho': { code: 'xho', name: 'Xhosa', nativeName: 'isiXhosa', iso_639_3: 'xho' },
	'afr': { code: 'afr', name: 'Afrikaans', nativeName: 'Afrikaans', iso_639_3: 'afr' },
	'sot': { code: 'sot', name: 'Sotho', nativeName: 'Sesotho', iso_639_3: 'sot' },
	'tsn': { code: 'tsn', name: 'Tswana', nativeName: 'Setswana', iso_639_3: 'tsn' },
	'nbl': { code: 'nbl', name: 'Ndebele', nativeName: 'isiNdebele', iso_639_3: 'nbl' },
	'ssw': { code: 'ssw', name: 'Swati', nativeName: 'siSwati', iso_639_3: 'ssw' },
	'tso': { code: 'tso', name: 'Tsonga', nativeName: 'Xitsonga', iso_639_3: 'tso' },
	'ven': { code: 'ven', name: 'Venda', nativeName: 'Tshivenda', iso_639_3: 'ven' },
	'eng': { code: 'eng', name: 'English', nativeName: 'English', iso_639_3: 'eng' },
	'fra': { code: 'fra', name: 'French', nativeName: 'Français', iso_639_3: 'fra' },
	'spa': { code: 'spa', name: 'Spanish', nativeName: 'Español', iso_639_3: 'spa' },
	'por': { code: 'por', name: 'Portuguese', nativeName: 'Português', iso_639_3: 'por' },
	'cmn': { code: 'cmn', name: 'Mandarin', nativeName: '中文', iso_639_3: 'cmn' },
	'hin': { code: 'hin', name: 'Hindi', nativeName: 'हिन्दी', iso_639_3: 'hin' },
	'ind': { code: 'ind', name: 'Indonesian', nativeName: 'Bahasa Indonesia', iso_639_3: 'ind' },
	'fil': { code: 'fil', name: 'Filipino', nativeName: 'Filipino', iso_639_3: 'fil' },
	'vie': { code: 'vie', name: 'Vietnamese', nativeName: 'Tiếng Việt', iso_639_3: 'vie' },
	'tha': { code: 'tha', name: 'Thai', nativeName: 'ไทย', iso_639_3: 'tha' },
	'tur': { code: 'tur', name: 'Turkish', nativeName: 'Türkçe', iso_639_3: 'tur' }
};

// Country to language mapping
export const COUNTRY_LANGUAGES: Record<string, string[]> = {
	'Ghana': ['en', 'twi', 'asante_twi', 'akuapem_twi', 'ewe', 'ga', 'dagbani', 'hausa', 'aka', 'gaa', 'ada', 'dag', 'nzi', 'gjn', 'xsm'],
	'Kenya': ['en', 'swahili', 'kikuyu', 'luo'],
	'Nigeria': ['en', 'hausa', 'yoruba', 'igbo'],
	'South Africa': ['en', 'zulu', 'xhosa', 'afrikaans', 'ndebele', 'northern_sotho', 'sesotho', 'swati', 'tsonga', 'tswana', 'venda'],
	'Ethiopia': ['amharic', 'oromo', 'somali', 'tigrinya'],
	'Tanzania': ['swahili', 'en'],
	'Uganda': ['en', 'swahili'],
	'Rwanda': ['kinyarwanda', 'en', 'swahili'],
	'Burundi': ['kirundi', 'en', 'swahili'],
	'Somalia': ['somali'],
	'Sudan': ['ar', 'en'],
	'South Sudan': ['en', 'ar'],
	'Egypt': ['ar'],
	'Libya': ['ar'],
	'Tunisia': ['ar'],
	'Algeria': ['ar', 'tamazight'],
	'Morocco': ['ar', 'tamazight'],
	'Mauritania': ['ar', 'wolof'],
	'Senegal': ['fr', 'wolof'],
	'Gambia': ['en', 'mandinka', 'wolof', 'fula'],
	'Guinea': ['fr', 'fula', 'maninka', 'susu'],
	'Guinea-Bissau': ['pt', 'kriol'],
	'Sierra Leone': ['en', 'krio'],
	'Liberia': ['en'],
	'Mali': ['fr', 'bambara'],
	'Burkina Faso': ['fr', 'moore', 'dioula'],
	'Niger': ['fr', 'hausa', 'zarma'],
	'Chad': ['fr', 'ar'],
	'Cameroon': ['fr', 'en'],
	'Central African Republic': ['fr', 'sango'],
	'Gabon': ['fr'],
	'Republic of the Congo': ['fr', 'lingala', 'kikongo'],
	'Democratic Republic of the Congo': ['fr', 'lingala', 'swahili', 'kikongo', 'tshiluba'],
	'Angola': ['pt'],
	'Mozambique': ['pt'],
	'Sao Tome and Principe': ['pt'],
	'Cabo Verde': ['pt', 'kabverdianu'],
	'Equatorial Guinea': ['es', 'fr', 'pt'],
	'Benin': ['fr', 'fon', 'yoruba'],
	'Togo': ['fr', 'ewe', 'kabye'],
	'Ivory Coast': ['fr'],
	'Botswana': ['en', 'tswana'],
	'Namibia': ['en', 'afrikaans', 'oshiwambo'],
	'Zambia': ['en', 'bemba', 'nyanja', 'tonga'],
	'Zimbabwe': ['en', 'shona', 'ndebele'],
	'Malawi': ['en', 'chichewa'],
	'Lesotho': ['en', 'sesotho'],
	'Eswatini': ['en', 'swati'],
	'Madagascar': ['malagasy', 'fr'],
	'Mauritius': ['en', 'fr', 'mauritian_creole'],
	'Seychelles': ['seychellois_creole', 'en', 'fr'],
	'Comoros': ['ar', 'fr', 'comorian'],
	'Djibouti': ['fr', 'ar', 'somali', 'afar'],
	'Eritrea': ['tigrinya', 'ar', 'en'],

	// Emerging markets
	'Brazil': ['pt'],
	'China': ['mandarin'],
	'India': ['hindi', 'en'],
	'Indonesia': ['indonesian'],
	'Mexico': ['es'],
	'Philippines': ['filipino', 'en'],
	'Vietnam': ['vietnamese'],
	'Thailand': ['thai'],
	'Turkey': ['turkish'],
	'Argentina': ['es']
};

// Get language display name
export function getLanguageDisplayName(languageCode: string): string {
	const langInfo = LANGUAGE_MAPPING[languageCode];
	if (langInfo) {
		return `${langInfo.name} (${langInfo.code})`;
	}
	return languageCode;
}

// Get languages for a specific country
export function getLanguagesForCountry(country: string): string[] {
	if (country === 'All' || !country) {
		return Object.keys(LANGUAGE_MAPPING);
	}
	return COUNTRY_LANGUAGES[country] || [];
}

// Get all available countries
export function getAvailableCountries(): string[] {
	return ['All', ...Object.keys(COUNTRY_LANGUAGES)];
}

// Filter languages based on country and provider support
export function filterLanguagesByCountryAndProvider(
	country: string,
	providerLanguages: string[]
): string[] {
	const countryLanguages = getLanguagesForCountry(country);

	if (country === 'All' || !country) {
		return providerLanguages;
	}

	// Return intersection of country languages and provider languages
	return countryLanguages.filter(lang => providerLanguages.includes(lang));
}
