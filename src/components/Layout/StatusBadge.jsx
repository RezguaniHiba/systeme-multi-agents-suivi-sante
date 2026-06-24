// gère les éléments communs de l'interface
import React from 'react';
import { FaCheckCircle, FaExclamationTriangle, FaSpinner } from 'react-icons/fa';


const STATUS_STYLES = {
  ok: {
    dot: 'bg-emerald-400',
    text: 'text-emerald-100',
    icon: <FaCheckCircle className="text-emerald-300" />,
    label: 'En ligne',
  },
  down: {
    dot: 'bg-red-400',
    text: 'text-red-100',
    icon: <FaExclamationTriangle className="text-red-300" />,
    label: 'Hors ligne',
  },
  unknown: {
    dot: 'bg-gray-300',
    text: 'text-white/60',
    icon: <FaSpinner className="animate-spin text-white/50" />,
    label: 'Vérification…',
  },
};

const StatusBadge = ({ status, label }) => {
  let key = 'unknown';
  if (status) {
    key = status.status === 'ok' ? 'ok' : 'down';
  }
  const style = STATUS_STYLES[key];

  return (
    <div
      className="flex items-center gap-1.5 text-xs"
      title={`${label} : ${style.label}`}
    >
      <span className={`relative flex h-2 w-2 ${key === 'ok' ? '' : ''}`}>
        {key === 'ok' && (
          <span
            className={`absolute inline-flex h-full w-full rounded-full ${style.dot} opacity-75 animate-ping`}
          />
        )}
        <span className={`relative inline-flex h-2 w-2 rounded-full ${style.dot}`} />
      </span>
      <span className={style.text}>{label}</span>
    </div>
  );
};

export default StatusBadge;
