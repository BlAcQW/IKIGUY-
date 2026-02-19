/**
 * ConversationDrawer Component
 * Q&A history drawer with conversation management
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Trash2, Download } from 'lucide-react';
import AIResponse from './AIResponse';

export interface Conversation {
  id: string;
  question: string;
  answer: string;
  audioUrl?: string;
  timestamp: Date;
}

interface ConversationDrawerProps {
  conversations: Conversation[];
  onClear?: () => void;
  onExport?: () => void;
}

export default function ConversationDrawer({
  conversations,
  onClear,
  onExport,
}: ConversationDrawerProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="relative flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-300 transition"
      >
        <MessageCircle className="h-5 w-5" />
        <span className="hidden sm:inline">Conversations</span>
        {conversations.length > 0 && (
          <span className="absolute -top-1 -right-1 px-2 py-0.5 bg-purple-500 text-white text-xs font-semibold rounded-full">
            {conversations.length}
          </span>
        )}
      </button>

      {/* Drawer */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/80 z-40"
            />

            {/* Drawer Content */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="fixed right-0 top-0 bottom-0 w-full sm:w-[500px] bg-gray-900 shadow-2xl z-50 overflow-y-auto"
            >
              {/* Header */}
              <div className="sticky top-0 bg-gray-900 border-b border-gray-800 p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <MessageCircle className="h-6 w-6 text-purple-400" />
                    <h2 className="text-xl font-bold text-white">
                      Q&A History
                    </h2>
                  </div>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 hover:bg-gray-800 rounded-lg transition"
                  >
                    <X className="h-5 w-5 text-gray-400" />
                  </button>
                </div>

                {/* Actions */}
                {conversations.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={onExport}
                      className="flex items-center space-x-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition"
                    >
                      <Download className="h-4 w-4" />
                      <span>Export</span>
                    </button>
                    <button
                      onClick={onClear}
                      className="flex items-center space-x-2 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 rounded-lg text-sm text-red-400 transition"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Clear All</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Conversations List */}
              <div className="p-4 space-y-4">
                {conversations.length === 0 ? (
                  <div className="text-center py-16">
                    <MessageCircle className="h-16 w-16 text-gray-700 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-400 mb-2">
                      No conversations yet
                    </h3>
                    <p className="text-sm text-gray-500 max-w-xs mx-auto">
                      Ask questions about the book using the voice button, and
                      they'll appear here.
                    </p>
                  </div>
                ) : (
                  <>
                    {conversations.map((conversation, index) => (
                      <motion.div
                        key={conversation.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <AIResponse
                          question={conversation.question}
                          answer={conversation.answer}
                          audioUrl={conversation.audioUrl}
                          timestamp={conversation.timestamp}
                        />
                      </motion.div>
                    ))}
                  </>
                )}
              </div>

              {/* Footer */}
              {conversations.length > 0 && (
                <div className="sticky bottom-0 bg-gray-900 border-t border-gray-800 p-4">
                  <p className="text-xs text-center text-gray-500">
                    {conversations.length}{' '}
                    {conversations.length === 1 ? 'conversation' : 'conversations'}
                  </p>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
