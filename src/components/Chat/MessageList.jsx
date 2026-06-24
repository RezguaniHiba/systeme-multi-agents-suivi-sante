// gère les échanges avec l'assistant médical
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { FaUserCircle, FaRobot, FaExclamationCircle } from 'react-icons/fa';

const formatElapsed = (seconds) => {
  if (seconds < 60) return `${seconds} s`;
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  return `${min} min ${sec.toString().padStart(2, '0')} s`;
};

const loadingMessage = (seconds) => {
  if (seconds < 10) {
    return "Analyse de votre question en cours…";
  }
  if (seconds < 45) {
    return "Recherche d'informations médicales…";
  }
  if (seconds < 90) {
    return "Préparation de la réponse…";
  }
  return "Traitement toujours en cours — merci de patienter, cela peut prendre quelques minutes.";
};

const MessageList = ({ messages, isLoading, elapsedSeconds = 0 }) => {
  return (
    <div className="space-y-4">
      {messages.map((message) => {
        const isUser = message.role === 'user';

        return (
          <div
            key={message.id}
            className={`flex animate-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[85%] sm:max-w-[75%] ${isUser ? '' : ''}`}>
              <div
                className={`mb-1 flex items-center gap-2 ${
                  isUser ? 'justify-end' : 'justify-start'
                }`}
              >
                {isUser ? (
                  <FaUserCircle className="text-lg text-gray-400" />
                ) : message.isError ? (
                  <FaExclamationCircle className="text-lg text-red-400" />
                ) : (
                  <FaRobot className="text-lg text-primary-500" />
                )}
                <span className="text-xs font-medium text-gray-500">
                  {isUser
                    ? 'Vous'
                    : message.isError
                    ? 'Erreur'
                    : 'Assistant Médical'}
                </span>
                <span className="text-xs text-gray-400">
                  {formatDistanceToNow(message.timestamp, {
                    addSuffix: true,
                    locale: fr,
                  })}
                </span>
              </div>

              <div
                className={`rounded-2xl p-4 shadow-sm transition-all ${
                  isUser
                    ? 'bg-primary-500 text-white'
                    : message.isError
                    ? 'border border-red-200 bg-red-50 text-red-700'
                    : 'border border-gray-200 bg-white text-gray-800'
                }`}
              >
                {isUser ? (
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                  </p>
                ) : (
                  <div className="prose prose-sm max-w-none prose-p:my-2 prose-headings:mt-3 prose-headings:mb-1 prose-ul:my-2 prose-li:my-0.5 prose-strong:text-gray-900">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>


            </div>
          </div>
        );
      })}

      {isLoading && (
        <div className="flex justify-start animate-fade-in">
          <div className="max-w-[85%] rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:max-w-[75%]">
            <div className="flex items-center gap-3">
              <div className="flex space-x-1">
                <div
                  className="h-2 w-2 animate-bounce rounded-full bg-primary-400"
                  style={{ animationDelay: '0ms' }}
                />
                <div
                  className="h-2 w-2 animate-bounce rounded-full bg-primary-400"
                  style={{ animationDelay: '150ms' }}
                />
                <div
                  className="h-2 w-2 animate-bounce rounded-full bg-primary-400"
                  style={{ animationDelay: '300ms' }}
                />
              </div>
              <span className="text-sm text-gray-500">
                {loadingMessage(elapsedSeconds)}
                <span className="ml-2 font-mono text-xs text-gray-400">
                  ({formatElapsed(elapsedSeconds)})
                </span>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
