// gère les éléments communs de l'interface
import React from 'react';
import { FaPlus, FaTrash, FaRegCommentDots, FaChevronLeft } from 'react-icons/fa';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';


const Sidebar = ({
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isLoading = false,
  isOpen = true,
  onToggle,
}) => {
  const handleDelete = (e, conversationId) => {
    e.stopPropagation();
    onDeleteConversation(conversationId);
  };

  if (!isOpen) {

    return (
      <button
        type="button"
        onClick={onToggle}
        className="fixed left-0 top-1/2 z-10 -translate-y-1/2 rounded-r-lg bg-gray-900 p-2 text-white shadow-lg transition-all hover:bg-gray-700"
        aria-label="Ouvrir l'historique"
        title="Ouvrir l'historique des conversations"
      >
        <FaChevronLeft className="h-4 w-4 rotate-180" />
      </button>
    );
  }

  return (
    <>

      <div className="fixed inset-0 z-30 bg-black/40 sm:hidden" onClick={onToggle} />

      <aside className="fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 flex-col border-r border-gray-200 bg-white shadow-lg transition-transform duration-300 sm:relative sm:translate-x-0">

        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-800">Conversations</h2>
          <button
            type="button"
            onClick={onToggle}
            aria-label="Fermer l'historique"
            className="rounded-lg p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
            title="Fermer l'historique"
          >
            <FaChevronLeft className="h-5 w-5" />
          </button>
        </div>


        <div className="p-3">
          <button
            type="button"
            onClick={onNewConversation}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-600"
          >
            <FaPlus className="text-xs" />
            Nouvelle conversation
          </button>
        </div>


        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {isLoading ? (
            <p className="px-3 py-4 text-center text-xs text-gray-500">
              Chargement de l'historique…
            </p>
          ) : conversations.length === 0 ? (
            <p className="px-3 py-4 text-center text-xs text-gray-500">
              Aucune conversation pour le moment.
              <br />
              Commencez une nouvelle discussion !
            </p>
          ) : (
            <ul className="space-y-1">
              {conversations.map((conv) => {
                const isActive = conv.id === activeConversationId;
                return (
                  <li key={conv.id}>
                    <button
                      type="button"
                      onClick={() => onSelectConversation(conv.id)}
                      title={conv.title}
                      className={`group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                        isActive
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <FaRegCommentDots className="shrink-0 text-gray-400" />
                      <span className="flex-1 overflow-hidden">
                        <span className="block truncate">
                          {conv.title || 'Nouvelle conversation'}
                        </span>
                        {conv.updated_at && (
                          <span className="block truncate text-[11px] text-gray-400">
                            {formatDistanceToNow(new Date(conv.updated_at), {
                              addSuffix: true,
                              locale: fr,
                            })}
                          </span>
                        )}
                      </span>
                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(e) => handleDelete(e, conv.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') handleDelete(e, conv.id);
                        }}
                        title="Supprimer la conversation"
                        aria-label="Supprimer la conversation"
                        className="shrink-0 rounded p-1.5 text-gray-400 opacity-0 transition-opacity hover:bg-gray-200 hover:text-red-500 group-hover:opacity-100 focus:opacity-100"
                      >
                        <FaTrash size={12} />
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Pied de page */}
        <div className="border-t border-gray-200 p-3 text-center text-[11px] text-gray-400">
          Historique stocké localement (SQLite)
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
