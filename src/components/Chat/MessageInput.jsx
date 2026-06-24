// gère les échanges avec l'assistant médical
import React, { useEffect, useRef } from 'react';
import { FiSend } from 'react-icons/fi';

const MAX_HEIGHT_PX = 160;

const MessageInput = ({ value, onChange, onSend, isLoading }) => {
  const textareaRef = useRef(null);


  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT_PX)}px`;
  }, [value]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim() && !isLoading) {
      onSend(value);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-3">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Décrivez vos symptômes, posez une question sur un médicament, ou parlez de votre bien-être… (Entrée pour envoyer, Maj+Entrée pour une nouvelle ligne)"
        className="flex-1 resize-none rounded-xl border border-gray-300 p-3 text-sm transition-all focus:border-transparent focus:outline-none focus:ring-2 focus:ring-primary-500"
        rows={1}
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={isLoading || !value.trim()}
        aria-label="Envoyer le message"
        className={`flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-xl transition-all duration-200 ${
          isLoading || !value.trim()
            ? 'cursor-not-allowed bg-gray-300'
            : 'bg-primary-500 shadow-md hover:bg-primary-600 hover:shadow-lg'
        }`}
      >
        {isLoading ? (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
        ) : (
          <FiSend className="text-xl text-white" />
        )}
      </button>
    </form>
  );
};

export default MessageInput;
