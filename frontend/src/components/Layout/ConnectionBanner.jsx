// gère les éléments communs de l'interface
import React from 'react';
import { FaExclamationTriangle } from 'react-icons/fa';


const ConnectionBanner = ({ serverStatus }) => {
  const userDown = serverStatus?.user_server?.status !== 'ok';
  const iotDown = serverStatus?.iot_server?.status !== 'ok';

  if (!userDown && !iotDown) return null;

  let message;
  if (userDown && iotDown) {
    message =
      "Le backend ne répond pas. Vérifiez qu'il est démarré (python main.py) sur http://localhost:8000.";
  } else if (userDown) {
    message =
      "Le service de l'assistant médical (Cas 1, port 8001) est hors ligne. La surveillance IoT reste disponible.";
  } else {
    message =
      'Le service de surveillance IoT (Cas 2, port 8002) est hors ligne. L\'assistant médical reste disponible.';
  }

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
      <div className="mx-auto flex max-w-7xl items-center gap-2">
        <FaExclamationTriangle className="shrink-0 text-amber-500" />
        <span>{message}</span>
      </div>
    </div>
  );
};

export default ConnectionBanner;
