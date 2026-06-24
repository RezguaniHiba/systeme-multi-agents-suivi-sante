// gère l'affichage des données de santé
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { FaBell, FaCheckCircle, FaExclamationTriangle, FaTrashAlt, FaCheckDouble } from 'react-icons/fa';

const AlertPanel = ({ alerts, onDismiss, onDismissAll, onClearAll }) => {
  const unreadCount = alerts.filter((a) => !a.read).length;

  if (alerts.length === 0) {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
        <div className="flex items-center gap-3 text-emerald-700">
          <FaCheckCircle className="text-xl" />
          <div>
            <p className="font-medium">Aucune alerte active</p>
            <p className="text-sm">Toutes les constantes vitales sont dans les normes</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-red-200 bg-red-50 px-4 py-3">
        <div className="flex items-center gap-2">
          <FaBell className="text-red-500" />
          <h3 className="font-semibold text-gray-800">Alertes de santé</h3>
          {unreadCount > 0 && (
            <span className="rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">
              {unreadCount} nouvelle{unreadCount > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <button
              onClick={onDismissAll}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-gray-600 transition-colors hover:bg-white"
            >
              <FaCheckDouble /> Tout marquer lu
            </button>
          )}
          <button
            onClick={onClearAll}
            className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-gray-600 transition-colors hover:bg-white"
          >
            <FaTrashAlt /> Effacer
          </button>
        </div>
      </div>
      <div className="max-h-96 divide-y divide-gray-100 overflow-y-auto">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-4 transition-all ${!alert.read ? 'bg-red-50' : 'hover:bg-gray-50'}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="mb-2 flex items-center gap-2">
                  <FaExclamationTriangle
                    className={!alert.read ? 'text-red-500' : 'text-gray-400'}
                  />
                  <span className="text-xs text-gray-500">
                    Patient : {alert.patientId} •{' '}
                    {formatDistanceToNow(alert.timestamp, { addSuffix: true, locale: fr })}
                  </span>
                </div>

                <div className="prose prose-sm max-w-none prose-p:my-1.5 prose-headings:mt-2 prose-headings:mb-1 prose-ul:my-1.5 text-sm text-gray-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{alert.message}</ReactMarkdown>
                </div>

                {alert.anomalies && alert.anomalies.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {alert.anomalies.map((anomaly, idx) => (
                      <span
                        key={idx}
                        className="rounded-full bg-red-100 px-2 py-1 text-xs text-red-700"
                      >
                        {typeof anomaly === 'string' ? anomaly : JSON.stringify(anomaly)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {!alert.read && (
                <button
                  onClick={() => onDismiss(alert.id)}
                  className="shrink-0 text-xs text-gray-500 hover:text-gray-700"
                >
                  Marquer lu
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertPanel;
