/**
 * SSML Editor Component
 *
 * Editor for Speech Synthesis Markup Language (SSML) with tag insertion helpers.
 * Created: 2025-10-27
 * Sprint 4: Advanced Features (Phase 9)
 */

import React, { useState, useRef } from 'react';

interface SSMLEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

interface SSMLTag {
  name: string;
  description: string;
  template: string;
  icon: string;
}

const SSML_TAGS: SSMLTag[] = [
  {
    name: 'Emphasis',
    description: 'Add stress/emphasis to words',
    template: '<emphasis level="strong">TEXT</emphasis>',
    icon: '💪',
  },
  {
    name: 'Break',
    description: 'Insert a pause',
    template: '<break time="500ms"/>',
    icon: '⏸️',
  },
  {
    name: 'Prosody (Rate)',
    description: 'Control speaking rate',
    template: '<prosody rate="slow">TEXT</prosody>',
    icon: '🐌',
  },
  {
    name: 'Prosody (Pitch)',
    description: 'Control pitch',
    template: '<prosody pitch="high">TEXT</prosody>',
    icon: '🎵',
  },
  {
    name: 'Prosody (Volume)',
    description: 'Control volume',
    template: '<prosody volume="loud">TEXT</prosody>',
    icon: '🔊',
  },
  {
    name: 'Say-As (Number)',
    description: 'How to pronounce numbers',
    template: '<say-as interpret-as="cardinal">123</say-as>',
    icon: '🔢',
  },
  {
    name: 'Say-As (Date)',
    description: 'Pronounce dates',
    template: '<say-as interpret-as="date" format="mdy">12/31/2024</say-as>',
    icon: '📅',
  },
  {
    name: 'Say-As (Time)',
    description: 'Pronounce time',
    template: '<say-as interpret-as="time" format="hms12">2:30pm</say-as>',
    icon: '🕐',
  },
  {
    name: 'Paragraph',
    description: 'Mark paragraph boundaries',
    template: '<p>TEXT</p>',
    icon: '¶',
  },
  {
    name: 'Sentence',
    description: 'Mark sentence boundaries',
    template: '<s>TEXT</s>',
    icon: '📝',
  },
];

export const SSMLEditor: React.FC<SSMLEditorProps> = ({
  value,
  onChange,
  placeholder = 'Enter SSML markup...',
}) => {
  const [showHelp, setShowHelp] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const insertTag = (template: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);

    // Replace TEXT placeholder with selected text or keep placeholder
    const newTag = selectedText
      ? template.replace('TEXT', selectedText)
      : template;

    const newValue = value.substring(0, start) + newTag + value.substring(end);
    onChange(newValue);

    // Set cursor position after inserted tag
    setTimeout(() => {
      const newCursorPos = start + newTag.length;
      textarea.focus();
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  const wrapWithSpeak = () => {
    if (!value.trim().startsWith('<speak>')) {
      const wrapped = `<speak>\n${value}\n</speak>`;
      onChange(wrapped);
    }
  };

  const validateSSML = (): { isValid: boolean; error?: string } => {
    if (!value.trim()) return { isValid: true };

    // Basic validation - check for balanced tags
    const openTags: string[] = [];
    const tagRegex = /<\/?([a-z-]+)(?:\s[^>]*)?\/?>/gi;
    let match;

    while ((match = tagRegex.exec(value)) !== null) {
      const [fullTag, tagName] = match;
      if (fullTag.startsWith('</')) {
        // Closing tag
        if (openTags.length === 0 || openTags[openTags.length - 1] !== tagName) {
          return { isValid: false, error: `Unmatched closing tag: </${tagName}>` };
        }
        openTags.pop();
      } else if (!fullTag.endsWith('/>')) {
        // Opening tag (not self-closing)
        openTags.push(tagName);
      }
    }

    if (openTags.length > 0) {
      return { isValid: false, error: `Unclosed tags: ${openTags.join(', ')}` };
    }

    return { isValid: true };
  };

  const validation = validateSSML();

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded transition-colors"
          >
            {showHelp ? '✕ Hide' : 'ℹ️ Show'} Tag Reference
          </button>
          <button
            onClick={wrapWithSpeak}
            className="px-3 py-1.5 text-xs font-medium text-green-700 bg-green-50 hover:bg-green-100 rounded transition-colors"
          >
            🔧 Wrap with &lt;speak&gt;
          </button>
        </div>
        {!validation.isValid && (
          <span className="text-xs text-red-600">⚠️ {validation.error}</span>
        )}
      </div>

      {/* Tag Reference */}
      {showHelp && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-indigo-900 mb-3">
            SSML Tag Reference
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {SSML_TAGS.map((tag) => (
              <button
                key={tag.name}
                onClick={() => insertTag(tag.template)}
                className="text-left p-2 bg-white hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
              >
                <div className="flex items-start space-x-2">
                  <span className="text-lg">{tag.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-gray-900">
                      {tag.name}
                    </div>
                    <div className="text-xs text-gray-600 mt-0.5">
                      {tag.description}
                    </div>
                    <code className="text-xs text-indigo-600 mt-1 block truncate">
                      {tag.template}
                    </code>
                  </div>
                </div>
              </button>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-indigo-200">
            <p className="text-xs text-indigo-700">
              <strong>Tip:</strong> Select text in the editor before clicking a
              tag to wrap the selected text with that tag.
            </p>
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full h-48 px-4 py-3 font-mono text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none ${
            !validation.isValid
              ? 'border-red-300 bg-red-50'
              : 'border-gray-300 bg-white'
          }`}
          spellCheck={false}
        />
        <div className="absolute bottom-2 right-2 text-xs text-gray-500">
          {value.length} characters
        </div>
      </div>

      {/* Examples */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
        <details className="text-xs">
          <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
            📖 SSML Examples
          </summary>
          <div className="mt-2 space-y-2">
            <div>
              <p className="text-gray-600 mb-1">Basic emphasis:</p>
              <code className="block bg-white p-2 rounded text-indigo-600">
                {'<speak>This is <emphasis level="strong">very important</emphasis>!</speak>'}
              </code>
            </div>
            <div>
              <p className="text-gray-600 mb-1">Rate and pitch control:</p>
              <code className="block bg-white p-2 rounded text-indigo-600">
                {'<speak><prosody rate="slow" pitch="low">Speak slowly and deeply</prosody></speak>'}
              </code>
            </div>
            <div>
              <p className="text-gray-600 mb-1">Breaks and numbers:</p>
              <code className="block bg-white p-2 rounded text-indigo-600">
                {'<speak>Count to 3<break time="500ms"/>1<break time="300ms"/>2<break time="300ms"/>3</speak>'}
              </code>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
};
