// gère les échanges avec l'assistant médical
import React from 'react';
import { FaHeartbeat, FaLungs, FaBrain, FaPills } from 'react-icons/fa';


const SUGGESTIONS = [
  {
    id: 'symptom',
    label: 'Symptômes',
    icon: FaHeartbeat,
    prompt: 'J’ai mal à la tête depuis trois jours, que faire ?',
  },
  {
    id: 'respiratory',
    label: 'Respiration',
    icon: FaLungs,
    prompt: 'Je tousse et j’ai un peu de fièvre, dois-je m’inquiéter ?',
  },
  {
    id: 'mental',
    label: 'Bien-être',
    icon: FaBrain,
    prompt: 'Je me sens souvent fatigué et sans énergie, des conseils ?',
  },
  {
    id: 'medication',
    label: 'Médicaments',
    icon: FaPills,
    prompt: 'Quels sont les effets secondaires courants de l’ibuprofène ?',
  },
];

const QuickSuggestions = ({ onSelectPrompt, disabled }) => {
  return (
    <div>
      <p className="mb-2 text-xs text-gray-500">
        Exemples de questions (vous pouvez aussi écrire les vôtres) :
      </p>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {SUGGESTIONS.map((s) => {
          const Icon = s.icon;
          return (
            <button
              key={s.id}
              type="button"
              disabled={disabled}
              onClick={() => onSelectPrompt(s.prompt)}
              className="flex shrink-0 items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              title={s.prompt}
            >
              <Icon className="text-primary-500" />
              {s.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuickSuggestions;
