// gère les échanges avec l'assistant médical
import React, { useState, useRef, useEffect } from 'react';
import { FaRobot, FaRedo } from 'react-icons/fa';
import toast from 'react-hot-toast';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import QuickSuggestions from './QuickSuggestions';
import healthAPI from '../../services/api';


const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content: `Bonjour. Je suis votre assistant médical.

Je peux vous aider avec des questions sur les symptômes, les médicaments, l'alimentation ou le bien-être mental.

Mes réponses sont basées sur des connaissances médicales générales. Elles ne remplacent pas l'avis d'un professionnel de santé.`,
  timestamp: new Date(),
};


const parseTimestamp = (value) => {
  if (!value) return new Date();
  const hasTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
};


const ChatContainer = ({
  user,
  conversationId,
  onConversationCreated,
  onConversationUpdated,
  onNewConversation,
}) => {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (!isLoading) {
      setElapsedSeconds(0);
      return;
    }
    const start = Date.now();
    const interval = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [isLoading]);


  useEffect(() => {
    let cancelled = false;

    if (!conversationId) {
      setMessages([WELCOME_MESSAGE]);
      return;
    }

    const loadHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const data = await healthAPI.getConversationMessages(conversationId, user?.id);
        if (cancelled) return;

        const loaded = (data?.messages || []).map((m) => ({
          id: `m-${m.id}`,
          role: m.role,
          content: m.content,
          timestamp: parseTimestamp(m.timestamp),
        }));

        setMessages(loaded.length > 0 ? loaded : [WELCOME_MESSAGE]);
      } catch (error) {
        if (!cancelled) {
          toast.error('Impossible de charger cette conversation.');
          setMessages([WELCOME_MESSAGE]);
        }
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    };

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [conversationId, user?.id]);

  const sendMessage = async (text) => {
    const question = text.trim();
    if (!question || isLoading) return;

    const userMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await healthAPI.askQuestion(question, user?.id, conversationId);
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
        },
      ]);

      if (response.conversation_id && response.conversation_id !== conversationId) {


        onConversationCreated?.(response.conversation_id);
      } else {

        onConversationUpdated?.();
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: 'assistant',
          isError: true,
          content: error.message || "Désolé, une erreur s'est produite. Veuillez réessayer.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = () => {
    if (isLoading) return;
    onNewConversation?.();
  };

  return (
    <div className="mx-auto flex h-full w-full max-w-4xl flex-col bg-gray-50">
      <div className="border-b border-gray-200 bg-white px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="flex items-center gap-2 text-xl font-bold text-gray-800 sm:text-2xl">
              <FaRobot className="text-primary-500" />
              Assistant Médical
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Posez vos questions sur la santé, les symptômes ou les médicaments
            </p>
          </div>
          <button
            onClick={resetConversation}
            disabled={isLoading}
            title="Nouvelle conversation"
            className="flex shrink-0 items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-500 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FaRedo />
            <span className="hidden sm:inline">Nouvelle conversation</span>
          </button>
        </div>
      </div>

      <div className="border-b border-gray-200 bg-white px-4 py-3 sm:px-6">
        <QuickSuggestions onSelectPrompt={setInputValue} disabled={isLoading} />
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
        {isLoadingHistory ? (
          <div className="flex h-full items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-400 border-t-transparent" />
              Chargement de la conversation…
            </div>
          </div>
        ) : (
          <>
            <MessageList messages={messages} isLoading={isLoading} elapsedSeconds={elapsedSeconds} />
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="border-t border-gray-200 bg-white px-4 py-4 sm:px-6">
        <MessageInput
          value={inputValue}
          onChange={setInputValue}
          onSend={sendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default ChatContainer;
