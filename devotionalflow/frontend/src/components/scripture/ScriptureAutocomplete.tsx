import { useState, useEffect, useRef } from "react";
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { bibleBooks, searchBooks, findBook } from "@/data/bibleBooks";
import { BookOpen } from "lucide-react";

interface ScriptureAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSelect?: (reference: string) => void;
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}

export function ScriptureAutocomplete({ value, onChange, onSelect, onKeyDown: parentOnKeyDown }: ScriptureAutocompleteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!value) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    const newSuggestions: string[] = [];

    // Parse the input to extract book, chapter, and verse
    let bookName = "";
    let chapterNum = 0;
    let verseNum = 0;

    // Check if there's a colon (verse reference)
    if (value.includes(":")) {
      // Format: "Book Chapter:Verse" or "Book:Verse"
      const colonParts = value.split(":");
      const beforeColon = colonParts[0].trim();
      const afterColon = colonParts[1] || "";

      // Extract chapter and book from before colon
      const spaceIndex = beforeColon.lastIndexOf(" ");
      if (spaceIndex > 0) {
        bookName = beforeColon.substring(0, spaceIndex).trim();
        chapterNum = parseInt(beforeColon.substring(spaceIndex + 1)) || 0;
      } else {
        bookName = beforeColon;
      }

      verseNum = parseInt(afterColon) || 0;
    }
    // Check if there's a space (chapter reference)
    else if (value.includes(" ")) {
      // Format: "Book Chapter" or "timothy 1" (which could mean "1 Timothy" or "2 Timothy")
      const parts = value.trim().split(/\s+/);
      
      // Check if first part is a number (like "1 timothy" or "2 timothy")
      const firstPartNum = parseInt(parts[0]);
      if (parts.length >= 2 && !isNaN(firstPartNum)) {
        // Format: "1 timothy" or "2 timothy" - the number is part of the book name
        bookName = parts.slice(0, 2).join(" "); // "1 timothy"
        chapterNum = parts.length > 2 ? parseInt(parts[2]) || 0 : 0;
      } else {
        // Format: "timothy 1" - could be "1 Timothy" chapter 1 or "2 Timothy" chapter 1
        // Or "Book Chapter" format
        const spaceIndex = value.lastIndexOf(" ");
        bookName = value.substring(0, spaceIndex).trim();
        const chapterStr = value.substring(spaceIndex + 1).trim();
        chapterNum = parseInt(chapterStr) || 0;
      }
    }
    // Just the book name
    else {
      bookName = value.trim();
    }

    // Suggest books
    if (!value.includes(" ") && !value.includes(":")) {
      const matchingBooks = searchBooks(bookName);
      matchingBooks.forEach(book => {
        newSuggestions.push(book.name);
        // Suggest first few chapters for all matching books
        newSuggestions.push(`${book.name} 1`);
        if (book.chapters.length > 1) newSuggestions.push(`${book.name} 2`);
        if (book.chapters.length > 2) newSuggestions.push(`${book.name} 3`);
      });
    }
    // Suggest chapters
    else if (value.includes(" ") && !value.includes(":")) {
      // If bookName doesn't start with a number but could match numbered books (e.g., "timothy")
      // Try to find all matching books
      const matchingBooks = searchBooks(bookName);
      
      if (matchingBooks.length === 1) {
        // Single match, use it
        const book = matchingBooks[0];
        if (chapterNum > 0) {
          const startChapter = Math.max(1, chapterNum);
          const endChapter = Math.min(chapterNum + 4, book.chapters.length);
          for (let i = startChapter; i <= endChapter; i++) {
            newSuggestions.push(`${book.name} ${i}`);
            if (i === chapterNum) {
              newSuggestions.push(`${book.name} ${i}:1`);
              if (book.chapters[i - 1] >= 16) newSuggestions.push(`${book.name} ${i}:16`);
            }
          }
        } else {
          for (let i = 1; i <= Math.min(5, book.chapters.length); i++) {
            newSuggestions.push(`${book.name} ${i}`);
          }
        }
      } else if (matchingBooks.length > 1) {
        // Multiple matches (e.g., "1 Timothy" and "2 Timothy")
        // If chapterNum is provided, try to match based on the chapter number
        // Otherwise, show suggestions for all matching books
        matchingBooks.forEach(book => {
          if (chapterNum > 0) {
            // Check if this book has the requested chapter
            if (chapterNum <= book.chapters.length) {
              newSuggestions.push(`${book.name} ${chapterNum}`);
              newSuggestions.push(`${book.name} ${chapterNum}:1`);
            }
          } else {
            // Show first few chapters for each matching book
            for (let i = 1; i <= Math.min(3, book.chapters.length); i++) {
              newSuggestions.push(`${book.name} ${i}`);
            }
          }
        });
      } else {
        // Fallback to original logic
        const book = findBook(bookName);
        if (book) {
          if (chapterNum > 0) {
            const startChapter = Math.max(1, chapterNum);
            const endChapter = Math.min(chapterNum + 4, book.chapters.length);
            for (let i = startChapter; i <= endChapter; i++) {
              newSuggestions.push(`${book.name} ${i}`);
              if (i === chapterNum) {
                newSuggestions.push(`${book.name} ${i}:1`);
                if (book.chapters[i - 1] >= 16) newSuggestions.push(`${book.name} ${i}:16`);
              }
            }
          } else {
            for (let i = 1; i <= Math.min(5, book.chapters.length); i++) {
              newSuggestions.push(`${book.name} ${i}`);
            }
          }
        }
      }
    }
    // Suggest verses
    else if (value.includes(":")) {
      const book = findBook(bookName);
      if (book && chapterNum > 0 && chapterNum <= book.chapters.length) {
        const maxVerse = book.chapters[chapterNum - 1];

        if (verseNum > 0) {
          // Show the typed verse and surrounding verses
          const startVerse = Math.max(1, verseNum);
          const endVerse = Math.min(verseNum + 4, maxVerse);

          for (let i = startVerse; i <= endVerse; i++) {
            newSuggestions.push(`${book.name} ${chapterNum}:${i}`);
            // Add range suggestion for the exact verse being typed
            if (i === verseNum && verseNum < maxVerse) {
              const rangeEnd = Math.min(verseNum + 2, maxVerse);
              if (rangeEnd > verseNum) {
                newSuggestions.push(`${book.name} ${chapterNum}:${verseNum}-${rangeEnd}`);
              }
            }
          }
        } else {
          // No verse number yet, suggest first few verses
          for (let i = 1; i <= Math.min(5, maxVerse); i++) {
            newSuggestions.push(`${book.name} ${chapterNum}:${i}`);
          }
        }
      }
    }

    setSuggestions(newSuggestions.slice(0, 10));
    setIsOpen(newSuggestions.length > 0);
    setSelectedIndex(-1); // Reset selection when suggestions change
  }, [value]);

  const handleSelect = (suggestion: string) => {
    onChange(suggestion);
    setSuggestions([]);
    setIsOpen(false);
    setSelectedIndex(-1);
    if (onSelect) {
      onSelect(suggestion);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Handle autocomplete navigation
    if (isOpen && suggestions.length > 0) {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) => 
            prev < suggestions.length - 1 ? prev + 1 : prev
          );
          return;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
          return;
        case "Enter":
          e.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
            handleSelect(suggestions[selectedIndex]);
          }
          return;
        case "Escape":
          e.preventDefault();
          setIsOpen(false);
          setSelectedIndex(-1);
          return;
      }
    }
    
    // Call parent handler if provided
    if (parentOnKeyDown) {
      parentOnKeyDown(e);
    }
  };

  // Attach keyboard handler to the input field in parent
  useEffect(() => {
    const input = document.querySelector('input[placeholder*="verse reference"]') as HTMLInputElement;
    if (input) {
      const handler = (e: KeyboardEvent) => {
        // Handle autocomplete navigation
        if (isOpen && suggestions.length > 0) {
          switch (e.key) {
            case "ArrowDown":
              e.preventDefault();
              setSelectedIndex((prev) => 
                prev < suggestions.length - 1 ? prev + 1 : prev
              );
              return;
            case "ArrowUp":
              e.preventDefault();
              setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
              return;
            case "Enter":
              e.preventDefault();
              if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
                handleSelect(suggestions[selectedIndex]);
              }
              return;
            case "Escape":
              e.preventDefault();
              setIsOpen(false);
              setSelectedIndex(-1);
              return;
          }
        }
        
        // Call parent handler if provided
        if (parentOnKeyDown) {
          const reactEvent = e as unknown as React.KeyboardEvent<HTMLInputElement>;
          parentOnKeyDown(reactEvent);
        }
      };
      input.addEventListener('keydown', handler, true); // Use capture phase
      return () => input.removeEventListener('keydown', handler, true);
    }
  }, [isOpen, suggestions, selectedIndex, value, parentOnKeyDown]);

  return (
    <div className="relative">
      {isOpen && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 z-50 mt-1 max-h-60 overflow-auto rounded-lg border border-border bg-popover shadow-lg">
          <Command shouldFilter={false}>
            <CommandList>
              <CommandGroup heading="Suggestions">
                {suggestions.map((suggestion, index) => (
                  <CommandItem
                    key={index}
                    value={suggestion}
                    onSelect={() => handleSelect(suggestion)}
                    className={index === selectedIndex ? "bg-accent text-accent-foreground" : ""}
                    data-selected={index === selectedIndex}
                  >
                    <BookOpen className="mr-2 h-4 w-4" />
                    <span>{suggestion}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </div>
      )}
    </div>
  );
}
