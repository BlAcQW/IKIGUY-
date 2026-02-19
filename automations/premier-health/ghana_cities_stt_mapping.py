#!/usr/bin/env python3
"""
Ghana Cities Speech-to-Text (STT) Variation Mapping
===================================================

Comprehensive mapping of all 106 Premier Health provider locations to their
common STT mishearings, phonetic variations, and similar-sounding English words.

Purpose: Improve voice assistant location accuracy for healthcare provider searches

Author: AI Labs Africa
Date: October 2025
Version: 1.0
"""

# Complete STT mapping for all 106 cities/regions in Ghana
# Format: 'CORRECT_CITY_NAME': [list, of, stt, variations]

GHANA_CITY_STT_MAPPING = {

    # ========================================================================
    # GREATER ACCRA REGION (30 areas)
    # ========================================================================

    # Madina / Adenta / Dodowa cluster
    'MADINA': ['medina', 'madonna', 'moderna', 'marina', 'madinna', 'madena', 'medena', 'ma dina', 'my dina', 'madeena', 'madeira'],
    'ADENTA': ['a denta', 'adventar', 'advent', 'a dental', 'edenta', 'uh denta', 'adenter', 'a denture'],
    'DODOWA': ['dodo wa', 'dodo way', 'do do wa', 'doda wa', 'dodua', 'doduwa', 'do dawa'],

    # Accra Central / Tudu / Makola
    'ACCRA': ['akra', 'accura', 'acura', 'acra', 'akara', 'accara', 'ak-ra', 'ack-ra'],
    'ACCRA CENTRAL': ['akra central', 'accura central', 'acura central', 'accra sentra', 'accra sental', 'accra center'],
    'TUDU': ['too doo', 'tu du', 'two doo', 'toodoo', 'tutu', 'to do', 'todo'],
    'MAKOLA': ['macola', 'ma cola', 'makolla', 'macolla', 'ma kola', 'makala', 'morocco', 'ma color'],

    # Circle / Kaneshie / North Kaneshie / Industrial Area
    'CIRCLE': ['circus', 'sircle', 'sir kill', 'cerkle', 'circle e', 'sir cole'],
    'KANESHIE': ['can a she', 'canashi', 'cane a she', 'kanashi', 'kenya she', 'canashie', 'kan a she', 'can ash'],
    'NORTH KANESHIE': ['north can a she', 'north canashi', 'north kenya she', 'north kanashi', 'north cane she'],
    'INDUSTRIAL AREA': ['industrial aria', 'in dustrial area'],

    # Airport / 37 Area
    'AIRPORT': ['air port', 'airpot', 'ear port'],
    'AIRPORT RESIDENTIAL AREA': ['airport residential', 'airport residencial', 'airport resi dental'],
    '37 AREA': ['thirty seven area', '37 aria', 'three seven area', 'thirty-seven area', 'thirty 7 area', '37', 'thirty seven', 'thirty-seven', 'three seven'],

    # Legon areas
    'LEGON': ['legion', 'lee gone', 'lay gone', 'leg on', 'lagon', 'leagon', 'le gon', 'legan', 'legone'],
    'NORTH LEGON': ['north legion', 'north lee gone', 'north leagon'],
    'EAST LEGON': ['east legion', 'east lee gone', 'east leagon', 'east leg on', 'ease legion'],

    # Dzorwulu / Abelenkpe
    'DZORWULU': ['zo wulu', 'zor wulu', 'joe wulu', 'zow ulu', 'zorwulu', 'jor wulu', 'jaw wulu', 'zor wooloo', 'dzor wooloo', 'zowulu'],
    'ABELENKPE': ['abel ink pay', 'abel n k p', 'a belen kpe', 'abelen k pe', 'abelenkpay', 'abel n pay', 'abelenpe', 'a berlin pay'],

    # Lapaz cluster
    'LAPAZ': ['la paz', 'lapa', 'la pass', 'lapas', 'la pah', 'lapez', 'la pez'],
    'NYAMEKYE': ['nya mechi', 'nama key', 'nya me chi', 'nyamechi', 'nya mickey', 'nama chi', 'nia mechi'],
    'DARKUMAN': ['dark human', 'dar human', 'darkman', 'dark man', 'darcoman', 'darkumen', 'daku man'],
    'ODORKOR': ['odor core', 'oh door core', 'o door cor', 'oh door cor', 'odoko', 'oh doko'],

    # Kokomlemle / Maamobi / Nima
    'KOKOMLEMLE': ['cocoa lemle', 'koko lemle', 'cocoa mlemle', 'koko mlemle', 'cocoa limley', 'koko limley', 'coco lemle', 'kokolemleh'],
    'MAAMOBI': ['ma mobi', 'mama bee', 'ma mo bee', 'mamobi', 'ma mobby', 'mama obi', 'ma moby'],
    'NIMA': ['neema', 'nema', 'knee ma', 'nee ma', 'nimah', 'naima', 'nama'],

    # Other Accra areas
    'ASYLUM DOWN': ['asylum town', 'asylum dawn', 'a silum down', 'ay silum down', 'asylumdown'],
    'ADABRAKA': ['ada braka', 'ada barack', 'ada braca', 'adaraka', 'ada broker', 'ada baraka', 'adabraca'],
    'OSU': ['oh sue', 'oh so', 'oh zoo', 'osoo', 'ossue', 'ohio sue'],
    'RIDGE': ['rich', 'ridges'],
    'LABONE': ['la bone', 'lab one', 'la bonne', 'labonne', 'la bon', 'labon'],
    'LA': ['lah', 'l a'],
    'TSE ADDO': ['see ado', 'say ado', 'see a do', 'say a do', 'tsay ado', 'chez ado'],
    'CANTONMENTS': ['canton mints', 'canton ments', 'cantonment'],
    'ACHIMOTA': ['ashimota', 'achimotor', 'achmota', 'a chimota', 'aki mota', 'achi motor', 'achimotah'],
    'NEW ACHIMOTA': ['new ashimota', 'new achimotor', 'new aki mota'],
    'ADJRINGANOR': ['aj ringer nor', 'adjringer nor', 'ad jinger nor', 'aj ringer', 'ad ringer nor', 'adjringanaw', 'adjuringanor'],

    # Dansoman / Mamprobi / Korle-Bu
    'DANSOMAN': ['dan so man', 'danso man', 'dan soaman', 'danceman', 'dan soman', 'dansomen'],
    'MAMPROBI': ['mam pro bee', 'mam probi', 'man probi', 'mampro bee', 'mamproby', 'mam pro b'],
    'KORLE-BU': ['korle boo', 'cor lee boo', 'corley boo', 'korleh bu', 'korle bu', 'kor lay boo', 'corlebu', 'korlebu'],

    # Dome / Haatso / Ashongman / Kwabenya
    'DOME': ['doom', 'dom'],
    'HAATSO': ['hat so', 'haat so', 'hot so', 'haht so', 'ha so', 'hasso'],
    'ASHONGMAN': ['a song man', 'ashong man', 'ah shong man', 'a shang man', 'ashongmen', 'ashong mon'],
    'KWABENYA': ['kwah ben ya', 'kwa ben ya', 'kwabenja', 'quabenya', 'kwabania'],

    # Teshie / Nungua
    'TESHIE': ['te she', 'teshi', 'teshay', 'teshe', 'teh she', 'teshee', 'te shay'],
    'NUNGUA': ['nun gua', 'nun wa', 'nunwa', 'nungwa', 'nun gwa', 'nong wa', 'nangua'],

    # Spintex / Baatsona
    'SPINTEX': ['spin tex', 'spin text', 'spin teks', 'spinteks', 'spindex'],
    'SPINTEX ROAD': ['spin tex road', 'spin text road', 'spintex'],
    'BAATSONA': ['bat so na', 'baht sona', 'batso na', 'baht so na', 'bot sona'],

    # Tema area
    'TEMA': ['teema', 'tima', 'tayma', 'tay ma', 'tea ma', 'tehmah'],

    # TEMA Communities - All standardized to "TEMA COMMUNITY X" format (matches KB documents)
    # Handles both "tema community X" and standalone "community X" queries
    'TEMA COMMUNITY 1': [
        'tema community one', 'tema comm one', 'tema comm 1', 'tema community 1',
        'community one', 'community 1', 'comm one', 'comm 1', 'comm. 1', 'komunity one'
    ],
    'TEMA COMMUNITY 2': [
        'tema community two', 'tema comm two', 'tema comm 2', 'tema community 2', 'tema two',
        'community two', 'community 2', 'comm two', 'comm 2', 'comm. 2', 'komunity two'
    ],
    'TEMA COMMUNITY 3': [
        'tema community three', 'tema comm three', 'tema comm 3', 'tema community 3', 'tema three',
        'community three', 'community 3', 'comm three', 'comm 3', 'comm. 3', 'komunity three'
    ],
    'TEMA COMMUNITY 4': [
        'tema community four', 'tema comm four', 'tema comm 4', 'tema community 4', 'tema four',
        'community four', 'community 4', 'comm four', 'comm 4', 'comm. 4', 'komunity four'
    ],
    'TEMA COMMUNITY 5': [
        'tema community five', 'tema comm five', 'tema comm 5', 'tema community 5', 'tema five',
        'community five', 'community 5', 'comm five', 'comm 5', 'comm. 5', 'komunity five'
    ],
    'TEMA COMMUNITY 6': [
        'tema community six', 'tema comm six', 'tema comm 6', 'tema community 6', 'tema six',
        'community six', 'community 6', 'comm six', 'comm 6', 'comm. 6', 'komunity six'
    ],
    'TEMA COMMUNITY 7': [
        'tema community seven', 'tema comm seven', 'tema comm 7', 'tema community 7', 'tema seven',
        'community seven', 'community 7', 'comm seven', 'comm 7', 'comm. 7', 'komunity seven'
    ],
    'TEMA COMMUNITY 8': [
        'tema community eight', 'tema comm eight', 'tema comm 8', 'tema community 8', 'tema eight',
        'community eight', 'community 8', 'comm eight', 'comm 8', 'comm. 8', 'komunity eight'
    ],
    'TEMA COMMUNITY 9': [
        'tema community nine', 'tema comm nine', 'tema comm 9', 'tema community 9', 'tema nine',
        'community nine', 'community 9', 'comm nine', 'comm 9', 'comm. 9', 'komunity nine'
    ],
    'TEMA COMMUNITY 10': [
        'tema community ten', 'tema comm ten', 'tema comm 10', 'tema community 10', 'tema ten',
        'community ten', 'community 10', 'comm ten', 'comm 10', 'comm. 10', 'komunity ten'
    ],
    'TEMA COMMUNITY 11': [
        'tema community eleven', 'tema comm eleven', 'tema comm 11', 'tema community 11',
        'community eleven', 'community 11', 'comm eleven', 'comm 11', 'comm. 11', 'komunity eleven'
    ],
    'TEMA COMMUNITY 21': [
        'tema community twenty one', 'tema comm twenty one', 'tema comm 21', 'tema community 21',
        'community twenty one', 'community 21', 'comm twenty one', 'comm 21', 'comm. 21', 'komunity twenty one'
    ],
    'TEMA COMMUNITY 22': [
        'tema community twenty two', 'tema comm twenty two', 'tema comm 22', 'tema community 22',
        'community twenty two', 'community 22', 'comm twenty two', 'comm 22', 'comm. 22', 'komunity twenty two'
    ],
    'TEMA COMMUNITY 25': [
        'tema community twenty five', 'tema comm twenty five', 'tema comm 25', 'tema community 25',
        'community twenty five', 'community 25', 'comm twenty five', 'comm 25', 'comm. 25', 'komunity twenty five'
    ],
    'TEMA COMMUNITY 27': [
        'tema community twenty seven', 'tema comm twenty seven', 'tema comm 27', 'tema community 27',
        'community twenty seven', 'community 27', 'comm twenty seven', 'comm 27', 'comm. 27', 'komunity twenty seven'
    ],
    'TEMA COMMUNITY 28': [
        'tema community twenty eight', 'tema comm twenty eight', 'tema comm 28', 'tema community 28',
        'community twenty eight', 'community 28', 'comm twenty eight', 'comm 28', 'comm. 28', 'komunity twenty eight'
    ],
    'TEMA COMMUNITY 29': [
        'tema community twenty nine', 'tema comm twenty nine', 'tema comm 29', 'tema community 29',
        'community twenty nine', 'community 29', 'comm twenty nine', 'comm 29', 'comm. 29', 'komunity twenty nine'
    ],
    'TEMA COMMUNITY 30': [
        'tema community thirty', 'tema comm thirty', 'tema comm 30', 'tema community 30',
        'community thirty', 'community 30', 'comm thirty', 'comm 30', 'comm. 30', 'komunity thirty'
    ],
    'TEMA COMMUNITY 31': [
        'tema community thirty one', 'tema comm thirty one', 'tema comm 31', 'tema community 31',
        'community thirty one', 'community 31', 'comm thirty one', 'comm 31', 'comm. 31', 'komunity thirty one'
    ],
    'TEMA COMMUNITY 32': [
        'tema community thirty two', 'tema comm thirty two', 'tema comm 32', 'tema community 32',
        'community thirty two', 'community 32', 'comm thirty two', 'comm 32', 'comm. 32', 'komunity thirty two'
    ],
    'TEMA COMMUNITY 33': [
        'tema community thirty three', 'tema comm thirty three', 'tema comm 33', 'tema community 33',
        'community thirty three', 'community 33', 'comm thirty three', 'comm 33', 'comm. 33', 'komunity thirty three'
    ],
    'TEMA COMMUNITY 34': [
        'tema community thirty four', 'tema comm thirty four', 'tema comm 34', 'tema community 34',
        'community thirty four', 'community 34', 'comm thirty four', 'comm 34', 'comm. 34', 'komunity thirty four'
    ],
    'TEMA COMMUNITY 35': [
        'tema community thirty five', 'tema comm thirty five', 'tema comm 35', 'tema community 35',
        'community thirty five', 'community 35', 'comm thirty five', 'comm 35', 'comm. 35', 'komunity thirty five'
    ],
    'TEMA COMMUNITY 36': [
        'tema community thirty six', 'tema comm thirty six', 'tema comm 36', 'tema community 36',
        'community thirty six', 'community 36', 'comm thirty six', 'comm 36', 'comm. 36', 'komunity thirty six'
    ],
    'TEMA COMMUNITY 37': [
        'tema community thirty seven', 'tema comm thirty seven', 'tema comm 37', 'tema community 37',
        'community thirty seven', 'community 37', 'comm thirty seven', 'comm 37', 'comm. 37', 'komunity thirty seven'
    ],
    'TEMA COMMUNITY 38': [
        'tema community thirty eight', 'tema comm thirty eight', 'tema comm 38', 'tema community 38',
        'community thirty eight', 'community 38', 'comm thirty eight', 'comm 38', 'comm. 38', 'komunity thirty eight'
    ],
    'TEMA COMMUNITY 39': [
        'tema community thirty nine', 'tema comm thirty nine', 'tema comm 39', 'tema community 39',
        'community thirty nine', 'community 39', 'comm thirty nine', 'comm 39', 'comm. 39', 'komunity thirty nine'
    ],
    'TEMA COMMUNITY 40': [
        'tema community forty', 'tema comm forty', 'tema comm 40', 'tema community 40',
        'community forty', 'community 40', 'comm forty', 'comm 40', 'comm. 40', 'komunity forty'
    ],
    'TEMA COMMUNITY 41': [
        'tema community forty one', 'tema comm forty one', 'tema comm 41', 'tema community 41',
        'community forty one', 'community 41', 'comm forty one', 'comm 41', 'comm. 41', 'komunity forty one'
    ],

    # Sakumono / Lashibi
    'SAKUMONO': ['sack u mono', 'saku mono', 'sacomono', 'sako mono', 'sak mono'],
    'SAKUMONO ESTATE': ['sack u mono estate', 'sakumono state', 'saku mono estate', 'sacomono estate'],
    'LASHIBI': ['la she bee', 'lashe bi', 'lashi bi', 'lashibee', 'la shi bi', 'la she b'],

    # Ashaiman
    'ASHAIMAN': ['a shy man', 'ashay man', 'asha man', 'ashaimen', 'a shaman', 'ashiman', 'ashai man'],

    # Weija / Kasoa / Gbawe
    'WEIJA': ['way ja', 'wei ja', 'waya', 'weja', 'wayja', 'we jar'],
    'KASOA': ['ka so a', 'casoa', 'ka soar', 'kasowa', 'ka so wa', 'cassoa'],
    'GBAWE': ['bah way', 'gba way', 'ba way', 'gbaway', 'gba we', 'bah we', 'gabawe'],

    # Amansaman / Pokuase
    'AMANSAMAN': ['a man saman', 'amansa man', 'aman saman', 'amanda man', 'aman sa man'],
    'POKUASE': ['poco a say', 'poko a say', 'pocoa say', 'poko ase', 'poco ase'],

    # Tantra Hill / Ofankor
    'TANTRA HILL': ['tantra heel', 'tandra hill', 'tantra heal', 'tantra'],
    'OFANKOR': ['oh fan core', 'o fan cor', 'ofan core', 'o fanko', 'oh fanko', 'ofancore'],

    # Latebiokoshie / Mataheko
    'LATEBIOKOSHIE': ['late bio ko she', 'late bio koshi', 'latter bio koshi', 'late biokoshire', 'late bio ko shay'],
    'MATAHEKO': ['mata heko', 'mata echo', 'matta heko', 'ma ta heko', 'mataheco'],

    # Tesano
    'TESANO': ['te sa no', 'te sano', 'tay sano', 'tessa no', 'tesanoh'],

    # Michel Camp / Afienya
    'MICHEL CAMP': ['michael camp', 'mitchell camp', 'michelle camp', 'micheal camp'],
    'AFIENYA': ['a fie nya', 'ah fee nya', 'a feenya', 'afenya', 'ah finya'],


    # ========================================================================
    # CENTRAL REGION (8 areas)
    # ========================================================================

    'CAPE COAST': ['cape cost', 'cap coast', 'cape coste', 'capecoast', 'capo coast'],
    'WINNEBA': ['winnipeg', 'winnebago', 'wini ba', 'winnie ba', 'win a ba', 'winna ba', 'winnaba', 'winebah', 'winnepeg', 'winibar'],
    'ELMINA': ['el mina', 'el meena', 'el mena', 'almina', 'elmeena'],
    'ASSIN': ['a sin', 'assign', 'assing', 'assine'],
    'SWEDRU': ['swed roo', 'swed drew', 'sweden', 'swedrew', 'sweet drew', 'swe drew'],
    'MANKESSIM': ['man cassim', 'man ke sim', 'man kesim', 'man ca sim', 'man cass im', 'man keseem'],
    'ASIKUMA': ['asi kuma', 'a si kuma', 'as kuma', 'asi cuma'],
    'AJUMAKO': ['a ju mako', 'aju mako', 'ah ju marco', 'ajumarco', 'a juma ko', 'ajumaco'],


    # ========================================================================
    # ASHANTI REGION / KUMASI AREA (14 areas)
    # ========================================================================

    # Bomso / KNUST / Ejisu
    'BOMSO': ['bomb so', 'bom so', 'bonso', 'bomzo'],
    'KNUST': ['canust', 'k nust', 'k n u s t', 'kay nust', 'knew st'],
    'EJISU': ['e ji su', 'eji sue', 'eh jisu', 'eh ji soo', 'ejisoo', 'e jee sue'],

    # Other Kumasi areas
    'ASOKWA': ['a sock wa', 'asok wa', 'ah sok wa', 'a soak wa', 'asoqua'],
    'BANTAMA': ['ban tama', 'banta ma', 'ban tammer', 'bantamah', 'ban tamar', 'bantamaa'],
    'ABREPO': ['ab repo', 'a brepo', 'abripo', 'abrapo', 'a bray po', 'abrego'],
    'TAFO': ['taffo', 'ta foe'],
    'BREMANG': ['bray mang', 'bre mang', 'bre man', 'breh mang', 'bremen'],
    'ABUAKWA': ['abu akwa', 'abu aqua', 'abu aqwa', 'abuaqua', 'abu ak wa'],
    'TANOSO': ['ta no so', 'tan oh so', 'tannosso', 'ta nose oh'],
    'SANTASI': ['san ta si', 'santa see', 'san tasi'],
    'PATASE': ['pa ta say', 'pata say', 'pa tase', 'patasay'],
    'PATASI': ['pa ta si', 'patasi', 'pata si', 'pah tasi'],
    'SUAME': ['sue me', 'sua me', 'swami', 'suameh', 'sua may'],
    'ADUM': ['adam', 'a doom', 'adham', 'a dum', 'adom', 'uh dum'],
    'AHODWO': ['a hodo', 'ah hodo', 'ah hodwo', 'ahojo', 'a hoe dwo'],
    'AHINSAN': ['a hinsan', 'ahisan', 'ahi san', 'a hinson', 'ah in san'],
    'MAMPONTENG': ['mam pon teng', 'mampong teng', 'mam pont eng', 'mampon tang', 'mam pon ten'],
    'MAMPONG': ['mam pong', 'man pong', 'mam pung', 'mampon'],
    'AGONA': ['a go na', 'ah go na', 'ah gonna', 'a gonna'],
    'WIAMOASE': ['wee a mo ase', 'wia moase', 'we ah moase', 'wiamoseh', 'we a mo say'],
    'OBUASI': ['oh bu asi', 'o boo asi', 'oh boo asi', 'obuasee', 'oh bwasi'],
    'DUNKWA': ['dunk wa', 'donk wa', 'don qua', 'dunkwah'],
    'KONONGO': ['ko no ngo', 'con on go', 'ko non go', 'co nongo'],
    'AGOGO': ['ah go go', 'a go go', 'ah gogo', 'agohgo'],


    # ========================================================================
    # BRONG-AHAFO REGION (13 areas)
    # ========================================================================

    'SUNYANI': ['sue n yani', 'sun yani', 'soon yani', 'son yani', 'sue knee ani', 'suniani'],
    'TECHIMAN': ['teki man', 'tech man', 'techy man', 'techi man', 'take man', 'teckman'],
    'BEREKUM': ['bere kum', 'berry come', 'berry kum', 'bere come', 'bericum'],
    'DORMAA': ['door ma', 'dor maa', 'dorma', 'door mah'],
    'NKORANZA': ['n ko ran za', 'encoranza', 'en ko ranza', 'n coranza', 'encore anza'],
    'WENCHI': ['wen chi', 'when chi', 'winch', 'wench', 'wenchy'],
    'DROBO': ['dro bo', 'dro bow', 'droboh', 'draw bow'],
    'BECHEM': ['be chem', 'bay chem', 'behem', 'be kem', 'bekim'],
    'SAMPA': ['sam pa', 'samba', 'sam pah', 'sampah'],
    'GOASO': ['go a so', 'go ah so', 'go aso', 'guaso', 'go wa so'],
    'HWIDIEM': ['hwi diem', 'whidiem', 'we diem', 'we deem', 'whee diem'],
    'KENYASE': ['ken ya se', 'kenya say', 'kenya se', 'kenyassay', 'ken yassy'],
    'KINTAMPO': ['kin tam po', 'can tampo', 'kin tampo', 'quintampo', 'kin tempo'],
    'DUAYAW NKWANTA': ['dua yaw en kwanta', 'doo yaw n quanta', 'duayaw nkwanta'],
    'DUAYAW': ['dua yaw', 'doo yaw', 'doo a yaw', 'dway aw'],
    'NKWANTA': ['n kwanta', 'en kwanta', 'n quanta', 'enkwanta'],


    # ========================================================================
    # EASTERN REGION (16 areas)
    # ========================================================================

    'KOFORIDUA': ['ko fo ridua', 'coforidua', 'ko for idea', 'coffee ridua', 'ko fori dua', 'koforidwa', 'koforidu'],
    'NSAWAM': ['n sawam', 'ensawam', 'en sawam', 'n saw am', 'insawam'],
    'SUHUM': ['sue hum', 'sue home', 'su home', 'suhome', 'sue um'],
    'AKOSOMBO': ['ako sombo', 'acho sombo', 'ako combo', 'akosambo', 'ako zombo', 'akombo'],
    'SOMANYA': ['so man ya', 'somalia', 'so manya', 'soh man ya'],
    'ODUMASE': ['oh duma say', 'oh duma se', 'o duma say', 'oh duma sei'],
    'KROBO': ['crow bow', 'crow bo', 'kro bo', 'cro bow'],
    'ODA': ['oh da', 'odah', 'o dah', 'oder'],
    'AKWATIA': ['ak wa tia', 'aquatia', 'ak qua tia', 'ak water', 'akwatiah'],
    'KADE': ['kay day', 'ka day', 'caddy', 'kadeh'],
    'BEGORO': ['be go ro', 'bay goro', 'be goro', 'begorrow'],
    'OSIEM': ['oh seem', 'oh see em', 'o seem', 'osiym'],
    'NKAWKAW': ['n kaw kaw', 'enkawkaw', 'en caw caw', 'n cow cow', 'n ka ka', 'producing kokow', 'pro doing kokow', 'produceing kokow'],
    'NEW ABIREM': ['new a bi rem', 'new abbey rem', 'new ah birem', 'new ab rem'],
    'ASAMANKESE': ['a saman ke se', 'ah saman case', 'a sa man ke se', 'asaman casey'],
    'ASIAKWA': ['asi ak wa', 'asia qua', 'asi aqua', 'asia akwa'],
    'OSINO': ['oh see no', 'oh sino', 'o see no', 'osiino'],
    'ANYINAM': ['any nam', 'annie nam', 'ani nam'],
    'ENYIRESI': ['en yi re si', 'en ire si', 'eniresi', 'en ye re si'],
    'KIBI': ['kee bi', 'key bee', 'keebi', 'keebee'],
    'MAMFE- AKUAPEM': ['mamfe akuapem', 'mamfe ah qua pem'],
    'MAMFE': ['mam fe', 'mom fe', 'mam fay', 'mamfeh'],
    'AKUAPEM': ['ah qua pem', 'ah qua pim', 'aquapem', 'akwapem', 'ah quay pem'],


    # ========================================================================
    # WESTERN REGION (19 areas)
    # ========================================================================

    'TAKORADI': ['taco radi', 'taco ready', 'tako radi', 'tacoradi', 'ta coradi'],
    'SEKONDI': ['say con di', 'second', 'second i', 'say condi', 'secondi'],
    'TARKWA': ['tark wa', 'tar qua', 'tar kwa', 'tarkwah', 'tarqua'],
    'BOGOSO': ['bo go so', 'bow go so', 'bogo so', 'bo gosoh'],
    'WASSA': ['wa sa', 'wasa', 'wah sa', 'wassah'],
    'AKROPONG': ['ah crow pong', 'acropong', 'ak ro pong', 'akro pong'],
    'WASSA AKROPONG': ['wassa akropong', 'wasa akro pong'],
    'ASANKRAGWA': ['a san kra gwa', 'a san cragwa', 'asan kragwa', 'ah sankragwa'],
    'SAMREBOI': ['sam re boy', 'sam re boi', 'sam ray boy', 'samreboy'],
    'ENCHI': ['en chi', 'inchi', 'en chee', 'enchee', 'inch'],
    'INCHABAN': ['in cha ban', 'inch a ban', 'in cha bon', 'inchabahn'],
    'SUAMAN': ['sue a man', 'soo aman', 'sua man', 'suahman'],
    'DADIESO': ['da die so', 'daddy so', 'da di so', 'dadi esso'],
    'SUAMAN DADIESO': ['suaman dadieso', 'sua man daddy so'],

    # Sefwi towns
    'SEFWI': ['sef we', 'sef wee', 'say fee', 'sef wi', 'sefwe'],
    'BIBIANI': ['bi bi ani', 'bee bee ani', 'bi bianie', 'bibi ani'],
    'SEFWI BIBIANI': ['sefwi bibiani', 'sef we bee bee ani'],
    'ANHWIASO': ['an we a so', 'an we aso', 'anhwiasso', 'an wee aso'],
    'SEFWI ANHWIASO': ['sefwi anhwiaso', 'sef we anhwiaso'],
    'BEKWAI': ['be kwai', 'bek way', 'beck why', 'bekwy'],
    'SEFWI BEKWAI': ['sefwi bekwai', 'sef we bekwai'],
    'WIAWSO': ['wee aw so', 'we aw so', 'wee a so', 'wiahso'],
    'SEFWI WIAWSO': ['sefwi wiawso', 'sef we wiawso'],
    'ASAFO': ['a sa fo', 'ah sa fo', 'asafoh', 'a safari'],
    'SEFWI ASAFO': ['sefwi asafo', 'sef we asafo'],
    'ASAWINSO': ['a sa win so', 'ah sa win so', 'asa winso'],
    'SEFWI ASAWINSO': ['sefwi asawinso', 'sef we asawinso'],
    'JUABOSO': ['ju a bo so', 'jua boso', 'joo boso', 'juabosso'],
    'SEFWI JUABOSO': ['sefwi juaboso', 'sef we juaboso'],
    'BODI': ['bo di', 'bow dee', 'body', 'bodee'],
    'SEFWI BODI': ['sefwi bodi', 'sef we body'],
    'ESSAM': ['es sam', 'essay', 'essem', 'esam'],
    'SEFWI ESSAM': ['sefwi essam', 'sef we essam'],
    'AKONTOMBRA': ['ah kon tombra', 'ah con tombra', 'akon tombra', 'ah contombra'],
    'SEFWI AKONTOMBRA': ['sefwi akontombra', 'sef we akontombra'],


    # ========================================================================
    # VOLTA REGION (2 areas)
    # ========================================================================

    'HO': ['hoe', 'hoh', 'how', 'haw'],
    'HOHOE': ['ho ho', 'hoe hoe', 'ho ho ay', 'ho hoy', 'hoho'],


    # ========================================================================
    # NORTHERN REGION (6 areas)
    # ========================================================================

    'TAMALE': ['ta ma lee', 'tama lee', 'ta molly', 'tomale', 'tamalee', 'ta marley'],
    'WA': ['wah', 'war', 'where'],
    'BOLGATANGA': ['bol ga tanga', 'bol ga tongo', 'ball ga tanga', 'bolga tanga', 'bolgo tanga'],
    'BAWKU': ['baw ku', 'bow coo', 'back you', 'bow koo', 'bawk'],
    'NAVRONGO': ['nav rongo', 'nav ron go', 'na rongo', 'nav ronco'],
    'LAWRA': ['law ra', 'laura', 'lara', 'lawrah'],

    # ========================================================================
    # INSURANCE PLAN TYPES
    # ========================================================================
    # Premier Health Insurance coverage tiers and their voice variations
    # These help users search for facilities that accept specific plan types

    'PLATINUM PLUS': [
        'platinum plus', 'plat plus', 'platinum+', 'plat+', 'platinum class plus',
        'premium plus', 'platinum plan plus', 'flat plus', 'platnum plus',
        'platinum pass', 'plat pass', 'platinum plas'
    ],
    'PLATINUM': [
        'platinum', 'plat', 'platinum plan', 'platinum class', 'premium plan',
        'flat plan', 'platnum', 'platinum coverage', 'plat plan', 'flatinum'
    ],
    'MERCURY': [
        'mercury', 'mercury plan', 'mer', 'mercury class', 'mercury coverage',
        'merkury', 'mercury package', 'mer plan', 'marcury'
    ],
    'REGULAR': [
        'regular', 'regular plan', 'reg', 'standard', 'standard plan',
        'basic plan', 'regular coverage', 'reg plan', 'standard coverage',
        'basic coverage', 'basic', 'regular package'
    ],
}


# Reverse mapping: STT variation -> Correct city name
# Automatically generated from the main mapping
STT_TO_CORRECT_CITY = {}
for correct_city, variations in GHANA_CITY_STT_MAPPING.items():
    for variation in variations:
        STT_TO_CORRECT_CITY[variation.upper()] = correct_city


# Regional groupings for better organization
REGIONAL_GROUPINGS = {
    'GREATER_ACCRA': [
        'MADINA', 'ADENTA', 'DODOWA', 'ACCRA', 'ACCRA CENTRAL', 'TUDU', 'MAKOLA',
        'CIRCLE', 'KANESHIE', 'NORTH KANESHIE', 'INDUSTRIAL AREA', 'AIRPORT',
        'AIRPORT RESIDENTIAL AREA', '37 AREA', 'LEGON', 'NORTH LEGON', 'EAST LEGON',
        'DZORWULU', 'ABELENKPE', 'LAPAZ', 'NYAMEKYE', 'DARKUMAN', 'ODORKOR',
        'KOKOMLEMLE', 'MAAMOBI', 'NIMA', 'ASYLUM DOWN', 'ADABRAKA', 'OSU', 'RIDGE',
        'LABONE', 'LA', 'TSE ADDO', 'CANTONMENTS', 'ACHIMOTA', 'NEW ACHIMOTA',
        'ADJRINGANOR', 'DANSOMAN', 'MAMPROBI', 'KORLE-BU', 'DOME', 'HAATSO',
        'ASHONGMAN', 'KWABENYA', 'TESHIE', 'NUNGUA', 'SPINTEX', 'SPINTEX ROAD',
        'BAATSONA', 'TEMA', 'SAKUMONO', 'SAKUMONO ESTATE', 'LASHIBI', 'ASHAIMAN',
        'WEIJA', 'KASOA', 'GBAWE', 'AMANSAMAN', 'POKUASE', 'TANTRA HILL', 'OFANKOR',
        'LATEBIOKOSHIE', 'MATAHEKO', 'TESANO', 'MICHEL CAMP', 'AFIENYA'
    ],
    'CENTRAL': [
        'CAPE COAST', 'WINNEBA', 'ELMINA', 'ASSIN', 'SWEDRU',
        'MANKESSIM', 'ASIKUMA', 'AJUMAKO'
    ],
    'ASHANTI': [
        'BOMSO', 'KNUST', 'EJISU', 'ASOKWA', 'BANTAMA', 'ABREPO', 'TAFO', 'BREMANG', 'ABUAKWA', 'TANOSO',
        'SANTASI', 'PATASI', 'SUAME', 'ADUM', 'AHODWO',
        'AHINSAN', 'MAMPONTENG', 'MAMPONG', 'AGONA', 'WIAMOASE', 'OBUASI',
        'DUNKWA', 'KONONGO', 'AGOGO'
    ],
    'BRONG_AHAFO': [
        'SUNYANI', 'TECHIMAN', 'BEREKUM', 'DORMAA', 'NKORANZA', 'WENCHI',
        'DROBO', 'BECHEM', 'SAMPA', 'GOASO', 'HWIDIEM', 'KENYASE', 'KINTAMPO',
        'DUAYAW', 'NKWANTA'
    ],
    'EASTERN': [
        'KOFORIDUA', 'NSAWAM', 'SUHUM', 'AKOSOMBO', 'SOMANYA', 'ODUMASE',
        'KROBO', 'ODA', 'AKWATIA', 'KADE', 'BEGORO', 'OSIEM',
        'NKAWKAW', 'NEW ABIREM', 'ASAMANKESE', 'ASIAKWA', 'OSINO', 'ANYINAM',
        'ENYIRESI', 'KIBI', 'MAMFE', 'AKUAPEM'
    ],
    'WESTERN': [
        'TAKORADI', 'SEKONDI', 'TARKWA', 'BOGOSO', 'WASSA', 'AKROPONG',
        'WASSA AKROPONG', 'ASANKRAGWA', 'SAMREBOI', 'ENCHI', 'INCHABAN',
        'SUAMAN', 'DADIESO', 'SUAMAN DADIESO', 'SEFWI', 'BIBIANI', 'ANHWIASO',
        'BEKWAI', 'WIAWSO', 'ASAFO', 'ASAWINSO', 'JUABOSO', 'BODI', 'ESSAM',
        'AKONTOMBRA'
    ],
    'VOLTA': ['HO', 'HOHOE'],
    'NORTHERN': ['TAMALE', 'WA', 'BOLGATANGA', 'BAWKU', 'NAVRONGO', 'LAWRA']
}


def get_statistics():
    """Get statistics about the mapping."""
    total_cities = len(GHANA_CITY_STT_MAPPING)
    total_variations = sum(len(variations) for variations in GHANA_CITY_STT_MAPPING.values())
    avg_variations = total_variations / total_cities if total_cities > 0 else 0

    return {
        'total_cities': total_cities,
        'total_variations': total_variations,
        'average_variations_per_city': round(avg_variations, 2),
        'regions': len(REGIONAL_GROUPINGS)
    }


# Module metadata
__version__ = '1.0.0'
__author__ = 'AI Labs Africa'
__description__ = 'Ghana Cities STT variation mapping for Premier Health provider locations'


if __name__ == '__main__':
    # Display statistics when run directly
    stats = get_statistics()
    print("="*80)
    print("GHANA CITIES STT MAPPING - STATISTICS")
    print("="*80)
    print(f"Total Cities/Regions Mapped: {stats['total_cities']}")
    print(f"Total STT Variations: {stats['total_variations']}")
    print(f"Average Variations per City: {stats['average_variations_per_city']}")
    print(f"Number of Regions: {stats['regions']}")
    print()

    # Test some examples
    print("EXAMPLE LOOKUPS:")
    print("-" * 80)
    test_cases = [
        ('winnipeg', 'WINNEBA'),
        ('medina', 'MADINA'),
        ('circus', 'CIRCLE'),
        ('koforidua', 'KOFORIDUA'),
        ('jaw wulu', 'DZORWULU')
    ]

    for test_input, expected in test_cases:
        result = STT_TO_CORRECT_CITY.get(test_input.upper())
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: '{test_input}' → {result} (expected: {expected})")
