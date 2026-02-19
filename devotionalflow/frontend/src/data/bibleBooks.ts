/**
 * Bible book reference data with chapter and verse counts
 */

export interface BibleBook {
  name: string;
  abbrev: string[];
  chapters: number[];
}

export const bibleBooks: BibleBook[] = [
  // Old Testament
  { name: "Genesis", abbrev: ["Gen", "Ge", "Gn"], chapters: [31, 25, 24, 26, 32, 22, 24, 22, 29, 32, 32, 20, 18, 24, 21, 16, 27, 33, 38, 18, 34, 24, 20, 67, 34, 35, 46, 22, 35, 43, 55, 32, 20, 31, 29, 43, 36, 30, 23, 23, 57, 38, 34, 34, 28, 34, 31, 22, 33, 26] },
  { name: "Exodus", abbrev: ["Exod", "Ex", "Exo"], chapters: [22, 25, 22, 31, 23, 30, 25, 32, 35, 29, 10, 51, 22, 31, 27, 36, 16, 27, 25, 26, 36, 31, 33, 18, 40, 37, 21, 43, 46, 38, 18, 35, 23, 35, 35, 38, 29, 31, 43, 38] },
  { name: "Leviticus", abbrev: ["Lev", "Le", "Lv"], chapters: [17, 16, 17, 35, 19, 30, 38, 36, 24, 20, 47, 8, 59, 57, 33, 34, 16, 30, 37, 27, 24, 33, 44, 23, 55, 46, 34] },
  { name: "Numbers", abbrev: ["Num", "Nu", "Nm", "Nb"], chapters: [54, 34, 51, 49, 31, 27, 89, 26, 23, 36, 35, 16, 33, 45, 41, 50, 13, 32, 22, 29, 35, 41, 30, 25, 18, 65, 23, 31, 40, 16, 54, 42, 56, 29, 34, 13] },
  { name: "Deuteronomy", abbrev: ["Deut", "Dt"], chapters: [46, 37, 29, 49, 33, 25, 26, 20, 29, 22, 32, 32, 18, 29, 23, 22, 20, 22, 21, 20, 23, 30, 25, 22, 19, 19, 26, 68, 29, 20, 30, 52, 29, 12] },
  { name: "Joshua", abbrev: ["Josh", "Jos", "Jsh"], chapters: [18, 24, 17, 24, 15, 27, 26, 35, 27, 43, 23, 24, 33, 15, 63, 10, 18, 28, 51, 9, 45, 34, 16, 33] },
  { name: "Judges", abbrev: ["Judg", "Jdg", "Jg", "Jdgs"], chapters: [36, 23, 31, 24, 31, 40, 25, 35, 57, 18, 40, 15, 25, 20, 20, 31, 13, 31, 30, 48, 25] },
  { name: "Ruth", abbrev: ["Rth", "Ru"], chapters: [22, 23, 18, 22] },
  { name: "1 Samuel", abbrev: ["1 Sam", "1 Sa", "1Samuel", "1S", "I Sa", "1 Sm", "1Sa", "I Sam"], chapters: [28, 36, 21, 22, 12, 21, 17, 22, 27, 27, 15, 25, 23, 52, 35, 23, 58, 30, 24, 42, 15, 23, 29, 22, 44, 25, 12, 25, 11, 31, 13] },
  { name: "2 Samuel", abbrev: ["2 Sam", "2 Sa", "2S", "II Sa", "2 Sm", "2Sa", "II Sam", "2Samuel"], chapters: [27, 32, 39, 12, 25, 23, 29, 18, 13, 19, 27, 31, 39, 33, 37, 23, 29, 33, 43, 26, 22, 51, 39, 25] },
  { name: "1 Kings", abbrev: ["1 Kgs", "1 Ki", "1K", "I Kgs", "1Kgs", "I Ki", "1Ki", "I Kings", "1Kings", "1st Kgs", "1st Kings"], chapters: [53, 46, 28, 34, 18, 38, 51, 66, 28, 29, 43, 33, 34, 31, 34, 34, 24, 46, 21, 43, 29, 53] },
  { name: "2 Kings", abbrev: ["2 Kgs", "2 Ki", "2K", "II Kgs", "2Kgs", "II Ki", "2Ki", "II Kings", "2Kings", "2nd Kgs", "2nd Kings"], chapters: [18, 25, 27, 44, 27, 33, 20, 29, 37, 36, 21, 21, 25, 29, 38, 20, 41, 37, 37, 21, 26, 20, 37, 20, 30] },
  { name: "1 Chronicles", abbrev: ["1 Chr", "1 Ch", "I Ch", "1Ch", "1 Chron", "I Chr", "1Chron", "I Chronicles", "1Chronicles"], chapters: [54, 55, 24, 43, 26, 81, 40, 40, 44, 14, 47, 40, 14, 17, 29, 43, 27, 17, 19, 8, 30, 19, 32, 31, 31, 32, 34, 21, 30] },
  { name: "2 Chronicles", abbrev: ["2 Chr", "2 Ch", "II Ch", "2Ch", "II Chr", "2Chron", "II Chronicles", "2Chronicles"], chapters: [17, 18, 17, 22, 14, 42, 22, 18, 31, 19, 23, 16, 22, 15, 19, 14, 19, 34, 11, 37, 20, 12, 21, 27, 28, 23, 9, 27, 36, 27, 21, 33, 25, 33, 27, 23] },
  { name: "Ezra", abbrev: ["Ezr", "Ez"], chapters: [11, 70, 13, 24, 17, 22, 28, 36, 15, 44] },
  { name: "Nehemiah", abbrev: ["Neh", "Ne"], chapters: [11, 20, 32, 23, 19, 19, 73, 18, 38, 39, 36, 47, 31] },
  { name: "Esther", abbrev: ["Esth", "Es"], chapters: [22, 23, 15, 17, 14, 14, 10, 17, 32, 3] },
  { name: "Job", abbrev: ["Jb"], chapters: [22, 13, 26, 21, 27, 30, 21, 22, 35, 22, 20, 25, 28, 22, 35, 22, 16, 21, 29, 29, 34, 30, 17, 25, 6, 14, 23, 28, 25, 31, 40, 22, 33, 37, 16, 33, 24, 41, 30, 24, 34, 17] },
  { name: "Psalms", abbrev: ["Ps", "Psalm", "Pslm", "Psa", "Psm", "Pss"], chapters: [6, 12, 8, 8, 12, 10, 17, 9, 20, 18, 7, 8, 6, 7, 5, 11, 15, 50, 14, 9, 13, 31, 6, 10, 22, 12, 14, 9, 11, 12, 24, 11, 22, 22, 28, 12, 40, 22, 13, 17, 13, 11, 5, 26, 17, 11, 9, 14, 20, 23, 19, 9, 6, 7, 23, 13, 11, 11, 17, 12, 8, 12, 11, 10, 13, 20, 7, 35, 36, 5, 24, 20, 28, 23, 10, 12, 20, 72, 13, 19, 16, 8, 18, 12, 13, 17, 7, 18, 52, 17, 16, 15, 5, 23, 11, 13, 12, 9, 9, 5, 8, 28, 22, 35, 45, 48, 43, 13, 31, 7, 10, 10, 9, 8, 18, 19, 2, 29, 176, 7, 8, 9, 4, 8, 5, 6, 5, 6, 8, 8, 3, 18, 3, 3, 21, 26, 9, 8, 24, 13, 10, 7, 12, 15, 21, 10, 20, 14, 9, 6] },
  { name: "Proverbs", abbrev: ["Prov", "Pr", "Prv"], chapters: [33, 22, 35, 27, 23, 35, 27, 36, 18, 32, 31, 28, 25, 35, 33, 33, 28, 24, 29, 30, 31, 29, 35, 34, 28, 28, 27, 28, 27, 33, 31] },
  { name: "Ecclesiastes", abbrev: ["Eccles", "Ec", "Ecc", "Qoh"], chapters: [18, 26, 22, 16, 20, 12, 29, 17, 18, 20, 10, 14] },
  { name: "Song of Solomon", abbrev: ["Song", "So", "SOS", "SongOfSongs", "SongofSolomon", "Canticles", "Canticle of Canticles"], chapters: [17, 17, 11, 16, 16, 13, 13, 14] },
  { name: "Isaiah", abbrev: ["Isa", "Is"], chapters: [31, 22, 26, 6, 30, 13, 25, 22, 21, 34, 16, 6, 22, 32, 9, 14, 14, 7, 25, 6, 17, 25, 18, 23, 12, 21, 13, 29, 24, 33, 9, 20, 24, 17, 10, 22, 38, 22, 8, 31, 29, 25, 28, 28, 25, 13, 15, 22, 26, 11, 23, 15, 12, 17, 13, 12, 21, 14, 21, 22, 11, 12, 19, 12, 25, 24] },
  { name: "Jeremiah", abbrev: ["Jer", "Je", "Jr"], chapters: [19, 37, 25, 31, 31, 30, 34, 22, 26, 25, 23, 17, 27, 22, 21, 21, 27, 23, 15, 18, 14, 30, 40, 10, 38, 24, 22, 17, 32, 24, 40, 44, 26, 22, 19, 32, 21, 28, 18, 16, 18, 22, 13, 30, 5, 28, 7, 47, 39, 46, 64, 34] },
  { name: "Lamentations", abbrev: ["Lam", "La"], chapters: [22, 22, 66, 22, 22] },
  { name: "Ezekiel", abbrev: ["Ezek", "Eze", "Ezk"], chapters: [28, 10, 27, 17, 17, 14, 27, 18, 11, 22, 25, 28, 23, 23, 8, 63, 24, 32, 14, 49, 32, 31, 49, 27, 17, 21, 36, 26, 21, 26, 18, 32, 33, 31, 15, 38, 28, 23, 29, 49, 26, 20, 27, 31, 25, 24, 23, 35] },
  { name: "Daniel", abbrev: ["Dan", "Da", "Dn"], chapters: [21, 49, 30, 37, 31, 28, 28, 27, 27, 21, 45, 13] },
  { name: "Hosea", abbrev: ["Hos", "Ho"], chapters: [11, 23, 5, 19, 15, 11, 16, 14, 17, 15, 12, 14, 16, 9] },
  { name: "Joel", abbrev: ["Jl"], chapters: [20, 32, 21] },
  { name: "Amos", abbrev: ["Am"], chapters: [15, 16, 15, 13, 27, 14, 17, 14, 15] },
  { name: "Obadiah", abbrev: ["Obad", "Ob"], chapters: [21] },
  { name: "Jonah", abbrev: ["Jnh", "Jon"], chapters: [17, 10, 10, 11] },
  { name: "Micah", abbrev: ["Mic", "Mc"], chapters: [16, 13, 12, 13, 15, 16, 20] },
  { name: "Nahum", abbrev: ["Nah", "Na"], chapters: [15, 13, 19] },
  { name: "Habakkuk", abbrev: ["Hab", "Hb"], chapters: [17, 20, 19] },
  { name: "Zephaniah", abbrev: ["Zeph", "Zep", "Zp"], chapters: [18, 15, 20] },
  { name: "Haggai", abbrev: ["Hag", "Hg"], chapters: [15, 23] },
  { name: "Zechariah", abbrev: ["Zech", "Zec", "Zc"], chapters: [21, 13, 10, 14, 11, 15, 14, 23, 17, 12, 17, 14, 9, 21] },
  { name: "Malachi", abbrev: ["Mal", "Ml"], chapters: [14, 17, 18, 6] },

  // New Testament
  { name: "Matthew", abbrev: ["Matt", "Mt"], chapters: [25, 23, 17, 25, 48, 34, 29, 34, 38, 42, 30, 50, 58, 36, 39, 28, 27, 35, 30, 34, 46, 46, 39, 51, 46, 75, 66, 20] },
  { name: "Mark", abbrev: ["Mrk", "Mk", "Mr"], chapters: [45, 28, 35, 41, 43, 56, 37, 38, 50, 52, 33, 44, 37, 72, 47, 20] },
  { name: "Luke", abbrev: ["Luk", "Lk"], chapters: [80, 52, 38, 44, 39, 49, 50, 56, 62, 42, 54, 59, 35, 35, 32, 31, 37, 43, 48, 47, 38, 71, 56, 53] },
  { name: "John", abbrev: ["Jhn", "Jn"], chapters: [51, 25, 36, 54, 47, 71, 53, 59, 41, 42, 57, 50, 38, 31, 27, 33, 26, 40, 42, 31, 25] },
  { name: "Acts", abbrev: ["Act", "Ac"], chapters: [26, 47, 26, 37, 42, 15, 60, 40, 43, 48, 30, 25, 52, 28, 41, 40, 34, 28, 41, 38, 40, 30, 35, 27, 27, 32, 44, 31] },
  { name: "Romans", abbrev: ["Rom", "Ro", "Rm"], chapters: [32, 29, 31, 25, 21, 23, 25, 39, 33, 21, 36, 21, 14, 23, 33, 27] },
  { name: "1 Corinthians", abbrev: ["1 Cor", "1 Co", "I Co", "1Co", "I Cor", "1Cor", "I Corinthians", "1Corinthians"], chapters: [31, 16, 23, 21, 13, 20, 40, 13, 27, 33, 34, 31, 13, 40, 58, 24] },
  { name: "2 Corinthians", abbrev: ["2 Cor", "2 Co", "II Co", "2Co", "II Cor", "2Cor", "II Corinthians", "2Corinthians"], chapters: [24, 17, 18, 18, 21, 18, 16, 24, 15, 18, 33, 21, 14] },
  { name: "Galatians", abbrev: ["Gal", "Ga"], chapters: [24, 21, 29, 31, 26, 18] },
  { name: "Ephesians", abbrev: ["Eph", "Ephes"], chapters: [23, 22, 21, 32, 33, 24] },
  { name: "Philippians", abbrev: ["Phil", "Php", "Pp"], chapters: [30, 30, 21, 23] },
  { name: "Colossians", abbrev: ["Col", "Co"], chapters: [29, 23, 25, 18] },
  { name: "1 Thessalonians", abbrev: ["1 Thess", "1 Th", "I Th", "1Th", "I Thes", "1Thes", "I Thess", "1Thess", "I Thessalonians", "1Thessalonians"], chapters: [10, 20, 13, 18, 28] },
  { name: "2 Thessalonians", abbrev: ["2 Thess", "2 Th", "II Th", "2Th", "II Thes", "2Thes", "II Thess", "2Thess", "II Thessalonians", "2Thessalonians"], chapters: [12, 17, 18] },
  { name: "1 Timothy", abbrev: ["1 Tim", "1 Ti", "I Ti", "1Ti", "I Tim", "1Tim", "I Timothy", "1Timothy"], chapters: [20, 15, 16, 16, 25, 21] },
  { name: "2 Timothy", abbrev: ["2 Tim", "2 Ti", "II Ti", "2Ti", "II Tim", "2Tim", "II Timothy", "2Timothy"], chapters: [18, 26, 17, 22] },
  { name: "Titus", abbrev: ["Tit", "Ti"], chapters: [16, 15, 15] },
  { name: "Philemon", abbrev: ["Phlm", "Phm"], chapters: [25] },
  { name: "Hebrews", abbrev: ["Heb"], chapters: [14, 18, 19, 16, 14, 20, 28, 13, 28, 39, 40, 29, 25] },
  { name: "James", abbrev: ["Jas", "Jm"], chapters: [27, 26, 18, 17, 20] },
  { name: "1 Peter", abbrev: ["1 Pet", "1 Pe", "I Pe", "1Pe", "I Pet", "1Pet", "I Pt", "1 Pt", "1Pt", "I Peter", "1Peter"], chapters: [25, 25, 22, 19, 14] },
  { name: "2 Peter", abbrev: ["2 Pet", "2 Pe", "II Pe", "2Pe", "II Pet", "2Pet", "II Pt", "2 Pt", "2Pt", "II Peter", "2Peter"], chapters: [21, 22, 18] },
  { name: "1 John", abbrev: ["1 Jhn", "1 Jn", "I Jn", "1Jn", "I Jo", "1Jo", "I Joh", "1Joh", "I Jhn", "1 Jo", "I John", "1John"], chapters: [10, 29, 24, 21, 21] },
  { name: "2 John", abbrev: ["2 Jhn", "2 Jn", "II Jn", "2Jn", "II Jo", "2Jo", "II Joh", "2Joh", "II Jhn", "2 Jo", "II John", "2John"], chapters: [13] },
  { name: "3 John", abbrev: ["3 Jhn", "3 Jn", "III Jn", "3Jn", "III Jo", "3Jo", "III Joh", "3Joh", "III Jhn", "3 Jo", "III John", "3John"], chapters: [14] },
  { name: "Jude", abbrev: ["Jud", "Jd"], chapters: [25] },
  { name: "Revelation", abbrev: ["Rev", "Re", "The Revelation"], chapters: [20, 29, 22, 11, 14, 17, 17, 13, 21, 11, 19, 17, 18, 20, 8, 21, 18, 24, 21, 15, 27, 21] },
];

export function findBook(query: string): BibleBook | null {
  const q = query.toLowerCase().trim();
  // First try exact match
  let book = bibleBooks.find(book =>
    book.name.toLowerCase() === q ||
    book.abbrev.some(abbr => abbr.toLowerCase() === q)
  );
  
  // If no exact match, try partial match (for cases like "timothy" matching "1 Timothy")
  if (!book) {
    book = bibleBooks.find(book => {
      const bookNameLower = book.name.toLowerCase();
      // Check if query matches the end of book name (e.g., "timothy" matches "1 timothy")
      // or if book name contains the query
      return bookNameLower.endsWith(` ${q}`) || 
             bookNameLower === q ||
             (bookNameLower.includes(q) && bookNameLower.split(' ').some(part => part === q));
    });
  }
  
  return book || null;
}

export function searchBooks(query: string): BibleBook[] {
  if (!query) return [];
  const q = query.toLowerCase().trim();
  return bibleBooks.filter(book => {
    const bookNameLower = book.name.toLowerCase();
    // Check if book name contains the query (for books like "1 Timothy" matching "timothy")
    // or starts with the query
    const nameMatches = bookNameLower.includes(q) || bookNameLower.startsWith(q);
    // Check abbreviations
    const abbrevMatches = book.abbrev.some(abbr => 
      abbr.toLowerCase().startsWith(q) || abbr.toLowerCase().includes(q)
    );
    return nameMatches || abbrevMatches;
  }).slice(0, 10);
}
